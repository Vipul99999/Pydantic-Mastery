"""
🎓 Advanced Annotated Types in Pydantic v2

Demonstrates:
- Annotated[T, metadata] for composable, reusable constraints
- StringConstraints, Field, BeforeValidator, AfterValidator composition
- Custom constraint types with type aliases (DRY validation)
- Multiple metadata items on a single field
- Integration with field_validator for complex business logic
- Generic models with constrained type parameters

Real-world use cases:
- Standardized validation rules across a large codebase
- Domain-specific types (Email, Phone, Currency, SKU)
- Configurable constraints via dependency injection
- Type-safe API parameter validation with clear error messages

🎓 INTERACTIVE LEARNING READY:
- Each Annotated type has clear input→transformation→output behavior
- Playground can demonstrate: "Paste ' (555) 123-4567 ' → see '5551234567'"
- Constraint aliases enable reusable validation patterns across models
- Schema export (model_json_schema) enables frontend form generation
- Error messages are specific to the constraint that failed
"""

from typing import Annotated, List, Optional, TypeVar, Generic, Union
from pydantic import (
    BaseModel, Field, 
    StringConstraints, BeforeValidator, AfterValidator, 
    field_validator, ValidationError, ConfigDict
)
# ✅ FIX: Pydantic v2 uses AfterValidator, not AfterValidatorInfo
from pydantic.functional_validators import AfterValidator
import re
from datetime import date
from decimal import Decimal


# =============================================================================
# 🧱 REUSABLE CONSTRAINT TYPE ALIASES
# =============================================================================
# These aliases allow you to define a validation rule ONCE and reuse it 
# across your entire application. This is the "DRY" (Don't Repeat Yourself) 
# pattern for validation logic.

# === Normalized Email ===
# Combines:
# 1. StringConstraints: RFC-compliant pattern, auto-lowercase, strip whitespace
# 2. BeforeValidator: Ensures normalization happens BEFORE pattern validation
NormalizedEmail = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    ),
    BeforeValidator(lambda v: v.strip().lower() if isinstance(v, str) else v)
]
# 🎓 Interactive: Input "  USER@Example.COM  " → Output "user@example.com"


# === US Phone Number ===
# Two-step validation pipeline:
# 1. sanitize_phone: Remove all non-digit characters (parentheses, dashes, spaces)
# 2. validate_us_phone: Ensure exactly 10 digits remain
def sanitize_phone(v: str) -> str:
    """Remove all non-digit characters from phone string."""
    if not isinstance(v, str):
        return v
    return re.sub(r"\D", "", v)

def validate_us_phone(v: str) -> str:
    """Validate US phone is exactly 10 digits."""
    digits = sanitize_phone(v)
    if len(digits) != 10:
        raise ValueError(f"US phone must be 10 digits, got {len(digits)}")
    return digits

USPhone = Annotated[
    str,
    BeforeValidator(sanitize_phone),  # Step 1: Clean input
    AfterValidator(validate_us_phone)  # Step 2: Validate cleaned input
]
# 🎓 Interactive: Input "(555) 123-4567" → Output "5551234567"


# === Currency with Precision ===
# Ensures monetary values are:
# 1. Non-negative (Field(ge=0))
# 2. Rounded to exactly 2 decimal places (AfterValidator)
# Note: decimal_places is NOT a valid Field kwarg in Pydantic v2
Currency = Annotated[
    Decimal,
    Field(ge=0),  # Non-negative constraint
    AfterValidator(lambda v: v.quantize(Decimal("0.01")))  # Round to cents
]
# 🎓 Interactive: Input 19.999 → Output Decimal("20.00")


# === Username Constraints ===
# Reusable pattern for all usernames in the app
Username = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",  # Alphanumeric + underscore/hyphen only
        strip_whitespace=True
    )
]


# === ISO Country Code ===
# Auto-uppercases input and enforces 2-letter uppercase pattern
CountryCode = Annotated[
    str,
    StringConstraints(
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$"
    ),
    BeforeValidator(lambda v: v.upper().strip() if isinstance(v, str) else v)
]
# 🎓 Interactive: Input "us" → Output "US"


# =============================================================================
# 🧪 COMPREHENSIVE DEMO MODEL
# =============================================================================

class AnnotatedAdvancedDemo(BaseModel):
    """
    Comprehensive example of Annotated constraint composition.
    
    Demonstrates:
    - Multiple constraint types on a single field
    - Reusable type aliases across models (DRY principle)
    - Custom validator functions in Annotated chain
    - Integration with Field() for additional metadata (description, examples)
    
    🎓 Learning Focus: Show how Annotated creates composable, testable validation.
    """
    
    # === Email with normalized constraints ===
    # Uses NormalizedEmail alias + Field metadata for docs/examples
    email: NormalizedEmail = Field(
        description="User email address (auto-normalized to lowercase)",
        examples=["user@example.com", "Admin@Company.ORG"]
    )
    
    # === Phone with custom sanitization ===
    # Optional field using USPhone alias
    phone: Optional[USPhone] = Field(
        default=None,
        description="US phone number (auto-formatted to 10 digits)"
    )
    
    # === Currency with precision ===
    # Uses Currency alias for monetary values
    balance: Currency = Field(
        default=Decimal("0.00"),
        description="Account balance in USD (rounded to 2 decimals)"
    )
    
    # === Username with reusable constraints ===
    # Uses Username alias + custom business logic validator below
    username: Username = Field(
        description="Unique username (3-30 chars, alphanumeric + _-)"
    )
    
    # === Country code with auto-uppercase ===
    # Uses CountryCode alias
    country: CountryCode = Field(
        default="US",
        description="ISO 3166-1 alpha-2 country code"
    )
    
    # === Complex: Multiple Annotated constraints + Field ===
    # Inline Annotated definition for one-off complex rules
    referral_code: Annotated[
        str,
        StringConstraints(min_length=6, max_length=12, pattern=r"^[A-Z0-9]+$"),
        BeforeValidator(lambda v: v.upper().strip() if isinstance(v, str) else v)
    ] = Field(
        default_factory=lambda: f"REF{date.today().strftime('%y%m%d')}",
        description="Auto-generated referral code (REF + date)"
    )
    
    # === List with constrained items ===
    # Each item in the list must match the inner Annotated constraints
    tags: List[Annotated[
        str,
        StringConstraints(min_length=2, max_length=20, pattern=r"^[a-z0-9-]+$")
    ]] = Field(
        default_factory=list,
        max_length=10,  # Max 10 tags in the list
        description="Lowercase alphanumeric tags with hyphens"
    )
    
    # === Optional with default factory ===
    metadata: Optional[Annotated[dict, Field(description="Key-value pairs")]] = Field(
    default_factory=dict,  # ← Move here
    description="Arbitrary key-value metadata"
)
    
    # === Custom validator that uses Annotated constraints ===
    @field_validator("username", mode="after")
    @classmethod
    def check_username_availability(cls, v: str) -> str:
        """
        Additional business logic AFTER Annotated format validation.
        
        Flow:
        1. Username alias validates format (3-30 chars, pattern)
        2. This validator checks business rules (reserved names)
        
        In real app: Query database to check uniqueness.
        """
        reserved = {"admin", "root", "system", "test", "api"}
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved and cannot be used")
        return v
    
    # === Playground Metadata for Frontend ===
    class PlaygroundConfig:
        """
        Metadata for interactive learning playground.
        
        Frontend can read via model_json_schema() to:
        - Generate form inputs with correct types/constraints
        - Show helpful placeholder text and examples
        - Display constraint-specific error messages
        """
        field_hints = {
            "email": "Enter email: user@example.com (auto-lowercased)",
            "phone": "Enter US phone: (555) 123-4567 (auto-formatted)",
            "balance": "Enter amount: 19.99 (auto-rounded to 2 decimals)",
            "username": "3-30 chars, letters/numbers/_/- only",
            "country": "Two-letter code: US, UK, CA (auto-uppercased)",
            "referral_code": "Auto-generated, or enter 6-12 uppercase alphanumeric",
            "tags": "Comma-separated: python,fastapi,pydantic",
        }


# =============================================================================
# 🔄 GENERIC MODEL WITH ANNOTATED CONSTRAINTS
# =============================================================================

T = TypeVar("T")

class PaginatedList(BaseModel, Generic[T]):
    """
    Generic paginated response with Annotated constraints.
    
    Works with ANY item type T while enforcing pagination rules.
    
    Usage:
        PaginatedList[UserBasic](items=[...], total=100, page=1, per_page=20)
        PaginatedList[Product](...)
    
    🎓 Learning: Show how Generics + Annotated create reusable, type-safe components.
    """
    
    items: List[T]  # Generic list of items (type determined by caller)
    
    # Constrained pagination fields using Annotated + Field
    page: Annotated[int, Field(ge=1, default=1, description="Current page (1-indexed)")]
    per_page: Annotated[int, Field(ge=1, le=100, default=20, description="Items per page (max 100)")]
    total: Annotated[int, Field(ge=0, description="Total items across all pages")]
    
    @property
    def total_pages(self) -> int:
        """Calculate total pages using ceiling division."""
        if self.per_page == 0:
            return 0
        # Ceiling division: -(-a // b) is equivalent to math.ceil(a / b)
        return -(-self.total // self.per_page)
    
    @property
    def has_next(self) -> bool:
        """Check if more pages exist."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if previous page exists."""
        return self.page > 1
    
    def to_dict(self) -> dict:
        """Serialize for API response with computed fields."""
        return self.model_dump(mode="json", exclude_none=True)


# =============================================================================
# 🛍️ DOMAIN-SPECIFIC TYPES WITH ANNOTATED
# =============================================================================

class Product(BaseModel):
    """
    Product model using domain-specific Annotated types.
    
    Demonstrates type safety for e-commerce/business entities.
    
    🎓 Learning: Show how Annotated creates self-documenting, validated domain models.
    """
    
    # === SKU: Stock Keeping Unit ===
    # Business rule: 8-20 chars, uppercase alphanumeric + hyphens only
    sku: Annotated[
        str,
        StringConstraints(
            min_length=8,
            max_length=20,
            pattern=r"^[A-Z0-9-]+$",
            strip_whitespace=True
        ),
        BeforeValidator(lambda v: v.upper().strip() if isinstance(v, str) else v)
    ] = Field(description="Unique product identifier (SKU)")
    
    # === Price: Monetary value ===
    # Business rule: Positive, rounded to 2 decimal places (cents)
    price: Annotated[
        Decimal,
        Field(gt=0),  # Must be positive (gt=0, not ge=0)
        AfterValidator(lambda v: v.quantize(Decimal("0.01")))  # Round to cents
    ] = Field(description="Product price in USD")
    
    # === Weight: Physical constraint ===
    weight_kg: Annotated[float, Field(gt=0, le=1000)] = Field(
        description="Weight in kilograms (0 < weight ≤ 1000)"
    )
    
    # === Dimensions: Bounded floats ===
    length_cm: Annotated[float, Field(ge=0, le=500)] = Field(description="Length in cm")
    width_cm: Annotated[float, Field(ge=0, le=500)] = Field(description="Width in cm")
    height_cm: Annotated[float, Field(ge=0, le=500)] = Field(description="Height in cm")
    
    # === Categories: Constrained list items ===
    # Each category must be 2-50 chars
    categories: List[Annotated[
        str,
        StringConstraints(min_length=2, max_length=50)
    ]] = Field(default_factory=list, max_length=5, description="Product categories (max 5)")
    
    # === Status: Enum-like constrained string ===
    # Pattern enforces allowed values without needing a full Enum class
    status: Annotated[
        str,
        StringConstraints(pattern="^(active|discontinued|preorder)$")
    ] = Field(default="active", description="Product lifecycle status")
    
    # === Computed property ===
    @property
    def volume_cm3(self) -> float:
        """Calculate product volume in cubic centimeters."""
        return self.length_cm * self.width_cm * self.height_cm
    
    # === Playground Metadata ===
    class PlaygroundConfig:
        """Frontend hints for product form generation."""
        examples = {
            "sku": "LAPTOP-PRO-15",
            "price": "1299.99",
            "weight_kg": "2.5",
            "dimensions": {"length_cm": "35.0", "width_cm": "24.0", "height_cm": "2.0"},
            "categories": ["electronics", "computers", "laptops"],
            "status": "active"
        }


# =============================================================================
# ⚙️ DYNAMIC CONSTRAINTS VIA CONTEXT
# =============================================================================

class ContextConstrained(BaseModel):
    """
    Model with constraints that vary by validation context.
    
    Demonstrates using info.context in field_validator for dynamic rules.
    
    Use case: Same field has different rules in different scenarios
    (e.g., "username" is 3-30 chars for users, but 8-20 for API keys).
    
    🎓 Learning: Show how to make validation flexible without duplicating models.
    """
    
    value: str
    
    @field_validator("value", mode="before")
    @classmethod
    def apply_context_constraints(cls, v: str, info) -> str:
        """
        Apply different constraints based on validation context.
        
        Access context via info.context (passed to model_validate).
        
        Example contexts:
        - {"min_length": 5, "max_length": 20}
        - {"min_length": 10, "alphanumeric_only": True}
        """
        context = info.context or {}
        min_len = context.get("min_length", 1)
        max_len = context.get("max_length", 100)
        
        if not isinstance(v, str):
            raise ValueError("Value must be string")
        
        v = v.strip()
        
        if len(v) < min_len:
            raise ValueError(f"Value must be at least {min_len} characters")
        if len(v) > max_len:
            raise ValueError(f"Value must be at most {max_len} characters")
        
        # Apply pattern based on context
        if context.get("alphanumeric_only"):
            if not re.match(r"^[a-zA-Z0-9\s]+$", v):
                raise ValueError("Value must be alphanumeric (letters, numbers, spaces only)")
        
        return v
    
    @classmethod
    def validate_with_context(cls,  dict, context: dict) -> "ContextConstrained":
        """
        Class method to validate with custom context.
        
        Usage:
            ContextConstrained.validate_with_context(
                {"value": "test"}, 
                {"min_length": 5, "alphanumeric_only": True}
            )
        
        🎓 Interactive: Let users adjust context sliders → see validation change.
        """
        return cls.model_validate(data, context=context)
    
    # === Playground Metadata ===
    class PlaygroundConfig:
        """Interactive controls for context-based validation."""
        context_controls = {
            "min_length": {"type": "number", "min": 1, "max": 50, "default": 1},
            "max_length": {"type": "number", "min": 1, "max": 200, "default": 100},
            "alphanumeric_only": {"type": "boolean", "default": False},
        }
        examples = [
            {"context": {"min_length": 5}, "input": "hello", "expected": "valid"},
            {"context": {"min_length": 10}, "input": "hello", "expected": "error: too short"},
            {"context": {"alphanumeric_only": True}, "input": "hello!", "expected": "error: special chars"},
        ]