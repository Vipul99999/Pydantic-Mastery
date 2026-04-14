"""
Demonstrates discriminated unions in Pydantic v2.

Key concepts covered:
- Literal types for discrimination field
- Field(discriminator=...) for auto-routing
- Union of multiple models with shared discriminator
- Nested discriminated unions
- Runtime type detection and validation
- Error messages specific to union members

Real-world use cases:
- Payment method selection (card/bank/crypto)
- Notification channels (email/sms/push)
- Event types in event-sourcing systems
- Plugin/extension architecture
"""

from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Annotated, Union, Literal, List, Optional, Dict, Any
from datetime import datetime
from enum import StrEnum


# === Simple discriminated union: Payment Methods ===

class PaymentMethodBase(BaseModel):
    """Base fields for all payment methods."""
    is_default: bool = False
    nickname: Optional[str] = Field(default=None, max_length=50)


class CreditCardPayment(PaymentMethodBase):
    """Credit/debit card payment details."""
    type: Literal["credit_card"] = "credit_card"
    
    card_brand: Literal["visa", "mastercard", "amex", "discover"]
    last_four: str = Field(pattern=r"^\d{4}$")
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=datetime.now().year)
    
    # Never store full card number!
    @field_validator("last_four")
    @classmethod
    def validate_last_four(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("last_four must be numeric")
        return v


class BankTransferPayment(PaymentMethodBase):
    """Bank account / ACH payment details."""
    type: Literal["bank_transfer"] = "bank_transfer"
    
    bank_name: str
    account_type: Literal["checking", "savings"]
    last_four: str = Field(pattern=r"^\d{4}$")
    routing_number: Optional[str] = Field(default=None, pattern=r"^\d{9}$")


class CryptoPayment(PaymentMethodBase):
    """Cryptocurrency payment details."""
    type: Literal["crypto"] = "crypto"
    
    currency: Literal["BTC", "ETH", "USDC", "USDT"]
    wallet_address: str = Field(min_length=26, max_length=200)
    network: Literal["mainnet", "testnet"] = "mainnet"
    
    @field_validator("wallet_address")
    @classmethod
    def validate_crypto_address(cls, v: str) -> str:
        # Basic format check (real implementation would use crypto libraries)
        if not v[0].isalnum():
            raise ValueError("Invalid wallet address format")
        return v.strip()


# Discriminated union: Pydantic auto-selects model based on 'type' field
PaymentMethod = Annotated[
    Union[CreditCardPayment, BankTransferPayment, CryptoPayment],
    Field(discriminator="type")
]


class PaymentProfile(BaseModel):
    """
    User payment profile with discriminated union.
    
    Benefits:
    - Type-safe access to payment method fields
    - Auto-validation based on 'type' discriminator
    - Clear error messages for invalid union members
    """
    
    user_id: int
    primary_method: PaymentMethod
    backup_methods: List[PaymentMethod] = Field(default_factory=list)
    
    @field_validator("backup_methods")
    @classmethod
    def validate_no_duplicates(cls, methods: List[PaymentMethod]) -> List[PaymentMethod]:
        """Ensure no duplicate payment methods by type+last_four."""
        seen = set()
        for method in methods:
            key = (method.type, getattr(method, "last_four", None))
            if key in seen:
                raise ValueError(f"Duplicate payment method: {key}")
            seen.add(key)
        return methods


# === Advanced: Nested discriminated unions ===

class EventBase(BaseModel):
    """Base event fields for event-sourcing."""
    event_id: str
    timestamp: datetime
    actor_id: int


class UserCreatedEvent(EventBase):
    """Event: New user registration."""
    event_type: Literal["user.created"] = "user.created"
    
    username: str
    email: str
    source: Literal["web", "mobile", "api"]


class UserUpdatedEvent(EventBase):
    """Event: User profile update."""
    event_type: Literal["user.updated"] = "user.updated"
    
    user_id: int
    changes: Dict[str, Any]  # Changed fields
    reason: Optional[str] = None


class OrderPlacedEvent(EventBase):
    """Event: New order created."""
    event_type: Literal["order.placed"] = "order.placed"
    
    order_id: int
    total: float
    items_count: int
    payment_method_type: str  # Reference, not full details


class OrderShippedEvent(EventBase):
    """Event: Order shipped."""
    event_type: Literal["order.shipped"] = "order.shipped"
    
    order_id: int
    tracking_number: str
    carrier: Literal["ups", "fedex", "usps", "dhl"]


# Nested discriminated union: Events grouped by aggregate root
UserEvent = Annotated[
    Union[UserCreatedEvent, UserUpdatedEvent],
    Field(discriminator="event_type")
]

OrderEvent = Annotated[
    Union[OrderPlacedEvent, OrderShippedEvent],
    Field(discriminator="event_type")
]

# Top-level discriminated union
DomainEvent = Annotated[
    Union[UserEvent, OrderEvent],
    Field(discriminator="event_type")
]


class EventStore(BaseModel):
    """
    Event store with nested discriminated unions.
    
    Demonstrates:
    - Hierarchical union discrimination
    - Type narrowing based on event_type
    - Validation of complex event structures
    """
    
    stream_id: str  # Aggregate ID (e.g., user_123)
    events: List[DomainEvent]
    version: int = Field(ge=0)
    
    def get_events_by_type(self, event_type: str) -> List[DomainEvent]:
        """Filter events by type (demonstrates type narrowing)."""
        return [e for e in self.events if e.event_type == event_type]


# === Real-world: Webhook payload with discriminated union ===

class WebhookBase(BaseModel):
    """Base webhook payload."""
    webhook_id: str
    timestamp: datetime
    signature: str  # HMAC signature for verification


class UserWebhook(WebhookBase):
    """Webhook for user-related events."""
    event: Literal["user.signed_up", "user.deleted", "user.updated"]
    user_id: int
    data: Dict[str, Any]


class OrderWebhook(WebhookBase):
    """Webhook for order-related events."""
    event: Literal["order.created", "order.fulfilled", "order.cancelled"]
    order_id: int
    data: Dict[str, Any]


class PaymentWebhook(WebhookBase):
    """Webhook for payment-related events."""
    event: Literal["payment.succeeded", "payment.failed", "payment.refunded"]
    payment_id: str
    amount: float
    currency: str
    data: Dict[str, Any]


# Discriminated union for webhook router
WebhookPayload = Annotated[
    Union[UserWebhook, OrderWebhook, PaymentWebhook],
    Field(discriminator="event")
]


class WebhookReceiver(BaseModel):
    """
    Webhook receiver that routes to appropriate handler.
    
    Usage in FastAPI:
        @app.post("/webhooks")
        def receive_webhook(payload: WebhookPayload):
            match payload.event:
                case "user.signed_up":
                    handle_user_signup(payload)  # payload is UserWebhook
                case "order.created":
                    handle_order_created(payload)  # payload is OrderWebhook
    """
    
    payload: WebhookPayload
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("payload", mode="before")
    @classmethod
    def verify_webhook_signature(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify webhook signature before validation.
        
        In production: Use HMAC-SHA256 with shared secret.
        This is a demo placeholder.
        """
        # signature = v.get("signature")
        # if not verify_hmac(v, signature, WEBHOOK_SECRET):
        #     raise ValueError("Invalid webhook signature")
        return v


# === Advanced: Conditional union based on multiple fields ===

class SearchFilterBase(BaseModel):
    """Base for search filter types."""
    field: str
    operator: Literal["eq", "ne", "gt", "lt", "contains", "in"]


class StringFilter(SearchFilterBase):
    """Filter for string fields."""
    field_type: Literal["string"] = "string"
    value: str
    case_sensitive: bool = True


class NumberFilter(SearchFilterBase):
    """Filter for numeric fields."""
    field_type: Literal["number"] = "number"
    value: Union[int, float]
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class DateFilter(SearchFilterBase):
    """Filter for date/datetime fields."""
    field_type: Literal["date"] = "date"
    value: Union[str, datetime]  # ISO string or datetime
    timezone: str = "UTC"


class BooleanFilter(SearchFilterBase):
    """Filter for boolean fields."""
    field_type: Literal["boolean"] = "boolean"
    value: bool


# Multi-field discriminator: field_type + operator
SearchFilter = Annotated[
    Union[StringFilter, NumberFilter, DateFilter, BooleanFilter],
    Field(discriminator="field_type")
]


class SearchQuery(BaseModel):
    """
    Search query with discriminated union filters.
    
    Demonstrates:
    - Discrimination based on field_type
    - Operator validation per filter type
    - Nested filter composition
    """
    
    query: str
    filters: List[SearchFilter] = Field(default_factory=list)
    sort_by: Optional[str] = None
    limit: int = Field(ge=1, le=100, default=20)
    
    @field_validator("filters")
    @classmethod
    def validate_filter_operators(cls, filters: List[SearchFilter]) -> List[SearchFilter]:
        """Ensure operators are valid for each filter type."""
        for f in filters:
            if f.field_type == "boolean" and f.operator not in ["eq", "ne"]:
                raise ValueError(f"Boolean fields only support eq/ne operators")
            if f.field_type == "string" and f.operator == "in" and not isinstance(f.value, list):
                raise ValueError("'in' operator requires list value for string filters")
        return filters