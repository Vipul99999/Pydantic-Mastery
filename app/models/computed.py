"""
Demonstrates @computed_field in Pydantic v2.

Key concepts covered:
- @computed_field decorator for derived properties
- Return type annotations required for computed fields
- Integration with model_dump() and JSON serialization
- Cached vs dynamic computed fields
- Computed fields with dependencies on other fields
- Excluding computed fields from serialization

Real-world use cases:
- Full name from first+last name
- Age calculation from birthdate
- Order total from line items
- Account status based on multiple flags
- URL generation from slug + base path

🎓 INTERACTIVE LEARNING READY:
- Each computed field has a clear input→output relationship
- Easy to demonstrate in playground: "Change X, see Y update"
- Computed fields appear in JSON Schema for frontend form generation
- Can be toggled on/off via model_dump(exclude_computed=True)
"""

from pydantic import BaseModel, Field, computed_field, field_validator
from datetime import datetime, date
from typing import Optional, List, Literal
from enum import StrEnum
import re


# === Basic Computed Field Example ===

class UserProfileComputed(BaseModel):
    """
    User profile with computed fields for API responses.
    
    🎓 Learning Focus: Show how computed fields auto-update when source fields change.
    """
    
    # Source fields (user provides these)
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_of_birth: date
    is_premium: bool = False
    account_created: datetime = Field(default_factory=datetime.utcnow)
    
    # === Computed Fields ===
    
    @computed_field
    @property
    def full_name(self) -> str:
        """
        Compute full name from first + last name.
        
        🎓 Interactive Demo: Type first_name="John", last_name="Doe" → see full_name="John Doe"
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    @computed_field
    @property
    def age(self) -> int:
        """
        Calculate age from date_of_birth.
        
        🎓 Interactive Demo: Change date_of_birth → see age recalculate instantly.
        """
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    @computed_field
    @property
    def account_age_days(self) -> int:
        """
        Days since account creation.
        
        🎓 Interactive Demo: Shows real-time calculation based on account_created timestamp.
        """
        delta = datetime.utcnow() - self.account_created
        return delta.days
    
    @computed_field
    @property
    def display_role(self) -> str:
        """
        Human-readable role based on premium status.
        
        🎓 Interactive Demo: Toggle is_premium → see display_role change from "Free User" to "Premium Member".
        """
        return "Premium Member" if self.is_premium else "Free User"
    
    @computed_field
    @property
    def email_domain(self) -> str:
        """
        Extract domain from email address.
        
        🎓 Interactive Demo: Type email="alice@company.com" → see email_domain="company.com".
        """
        if "@" in self.email:
            return self.email.split("@")[1]
        return "unknown"
    
    # === Computed Field with Custom Serialization ===
    
    @computed_field
    @property
    def profile_url(self) -> str:
        """
        Generate profile URL from username.
        
        Uses custom serializer to ensure consistent format.
        🎓 Interactive Demo: Change username → see profile_url update with slugified version.
        """
        # Slugify username for URL safety
        slug = re.sub(r"[^a-zA-Z0-9_-]", "-", self.username.lower())
        return f"https://app.example.com/users/{slug}"
    
    # === Conditional Computed Field ===
    
    @computed_field
    @property
    def premium_badge(self) -> Optional[str]:
        """
        Return badge emoji only for premium users.
        
        Returns None for non-premium (excluded from JSON if exclude_none=True).
        🎓 Interactive Demo: Toggle is_premium → see badge appear/disappear.
        """
        if self.is_premium:
            return "✨ Premium"
        return None
    
    # === Computed Field with Complex Logic ===
    
    @computed_field
    @property
    def account_status(self) -> Literal["active", "new", "inactive", "suspended"]:
        """
        Determine account status based on multiple factors.
        
        Business logic:
        - "new": Account created within last 7 days
        - "inactive": No activity in last 90 days (demo: using account_created as proxy)
        - "suspended": Would check a suspended_at field (not implemented)
        - "active": Default state
        
        🎓 Interactive Demo: Change account_created date → see status update based on rules.
        """
        # Demo logic (simplified)
        days_old = self.account_age_days
        
        if days_old < 7:
            return "new"
        elif days_old > 365:  # Demo: treat very old accounts as inactive
            return "inactive"
        return "active"
    
    # === Excluding Computed Fields ===
    
    def to_minimal_response(self) -> dict:
        """
        Serialize without computed fields for lightweight responses.
        
        🎓 Learning Point: Computed fields are included by default in model_dump(),
        but can be excluded with exclude_computed=True or explicit exclude.
        """
        return self.model_dump(
            mode="json",
            exclude_computed=True,  # Exclude all @computed_field properties
            exclude_none=True
        )
    
    def to_full_response(self) -> dict:
        """
        Serialize with all computed fields for detail views.
        """
        return self.model_dump(
            mode="json",
            exclude_none=False  # Include None values like premium_badge for free users
        )


# === Advanced: Computed Field with Dependencies ===

class OrderWithComputed(BaseModel):
    """
    Order model demonstrating computed fields with nested dependencies.
    
    🎓 Learning Focus: Show how computed fields can depend on nested models.
    """
    
    order_id: str
    items: List["OrderItem"]
    tax_rate: float = Field(ge=0.0, le=1.0, default=0.08)  # 8% default
    shipping_cost: float = Field(ge=0.0, default=5.99)
    discount_code: Optional[str] = None
    discount_percent: float = Field(ge=0.0, le=1.0, default=0.0)
    
    @computed_field
    @property
    def subtotal(self) -> float:
        """Sum of all item prices × quantities."""
        return round(sum(item.price * item.quantity for item in self.items), 2)
    
    @computed_field
    @property
    def discount_amount(self) -> float:
        """Calculate discount based on percent and subtotal."""
        return round(self.subtotal * self.discount_percent, 2)
    
    @computed_field
    @property
    def taxable_amount(self) -> float:
        """Amount subject to tax (after discount, before shipping)."""
        return max(0.0, self.subtotal - self.discount_amount)
    
    @computed_field
    @property
    def tax_amount(self) -> float:
        """Calculate tax on taxable amount."""
        return round(self.taxable_amount * self.tax_rate, 2)
    
    @computed_field
    @property
    def total(self) -> float:
        """Final order total: taxable + tax + shipping."""
        return round(self.taxable_amount + self.tax_amount + self.shipping_cost, 2)
    
    @computed_field
    @property
    def item_count(self) -> int:
        """Total quantity of all items."""
        return sum(item.quantity for item in self.items)
    
    @computed_field
    @property
    def savings_message(self) -> Optional[str]:
        """Human-readable savings message if discount applied."""
        if self.discount_amount > 0:
            return f"You saved ${self.discount_amount:.2f}!"
        return None
    
    def to_receipt(self) -> dict:
        """
        Format order as receipt for frontend display.
        
        🎓 Interactive Demo: Show line-item breakdown with computed totals.
        """
        return {
            "order_id": self.order_id,
            "items": [item.model_dump() for item in self.items],
            "pricing": {
                "subtotal": f"${self.subtotal:.2f}",
                "discount": f"-${self.discount_amount:.2f}" if self.discount_amount > 0 else None,
                "tax": f"${self.tax_amount:.2f}",
                "shipping": f"${self.shipping_cost:.2f}",
                "total": f"${self.total:.2f}",
            },
            "summary": {
                "item_count": self.item_count,
                "savings": self.savings_message
            }
        }


class OrderItem(BaseModel):
    """Line item for OrderWithComputed."""
    product_name: str
    price: float = Field(ge=0.01)
    quantity: int = Field(ge=1, le=100)
    
    @computed_field
    @property
    def line_total(self) -> float:
        """Price × quantity for this line item."""
        return round(self.price * self.quantity, 2)


# Rebuild for forward reference
OrderWithComputed.model_rebuild()


# === Computed Field with Caching (Demo Pattern) ===

class AnalyticsDashboard(BaseModel):
    """
    Dashboard with expensive computed fields.
    
    🎓 Learning Focus: Demonstrate when to cache computed values vs recalculate.
    Note: Pydantic computed fields recalculate on every access.
    For expensive computations, implement manual caching.
    """
    
    user_id: int
    raw_metrics: dict  # Raw data from database
    
    # Manual cache attribute (not a Pydantic field)
    _cached_total: Optional[float] = None
    
    @computed_field
    @property
    def total_revenue(self) -> float:
        """
        Expensive computation: Sum revenue from raw metrics.
        
        🎓 Interactive Demo: Show performance difference with/without caching.
        In production, add @lru_cache or manual caching pattern.
        """
        # Demo: Simulate expensive computation
        # In real app: query database, aggregate, transform
        return round(sum(self.raw_metrics.get("revenue", [])), 2)
    
    @computed_field
    @property
    def revenue_formatted(self) -> str:
        """Format revenue as currency string."""
        return f"${self.total_revenue:,.2f}"
    
    def clear_cache(self):
        """Manual cache invalidation (demo pattern)."""
        self._cached_total = None


# === Example for Interactive Playground ===

class PlaygroundComputed(BaseModel):
    """
    Simplified model for interactive learning playground.
    
    🎓 Designed for frontend: Each computed field has clear, immediate feedback.
    """
    
    # Simple inputs for beginners
    first_name: str = Field(min_length=1, examples=["Alice"])
    last_name: str = Field(min_length=1, examples=["Smith"])
    birth_year: int = Field(ge=1900, le=2025, examples=[1990])
    
    @computed_field
    @property
    def full_name(self) -> str:
        """Combine first and last name."""
        return f"{self.first_name} {self.last_name}"
    
    @computed_field
    @property
    def age_estimate(self) -> int:
        """Estimate age from birth year (simplified)."""
        return 2025 - self.birth_year
    
    @computed_field
    @property
    def greeting(self) -> str:
        """Personalized greeting using computed values."""
        return f"Hello, {self.full_name}! You're approximately {self.age_estimate} years old."
    
    # 🎓 Playground Metadata (for frontend UI)
    class PlaygroundConfig:
        """
        Metadata for interactive playground UI.
        
        Frontend can read this via model_json_schema() to:
        - Generate form inputs
        - Show live preview of computed fields
        - Provide helpful tooltips
        """
        inputs = {
            "first_name": {"label": "First Name", "type": "text", "placeholder": "Enter first name"},
            "last_name": {"label": "Last Name", "type": "text", "placeholder": "Enter last name"},
            "birth_year": {"label": "Birth Year", "type": "number", "min": 1900, "max": 2025},
        }
        outputs = {
            "full_name": {"label": "Full Name", "type": "computed", "icon": "user"},
            "age_estimate": {"label": "Estimated Age", "type": "computed", "icon": "calendar"},
            "greeting": {"label": "Greeting Preview", "type": "computed", "icon": "message", "highlight": True},
        }