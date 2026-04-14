"""
Demonstrates @model_validator decorator in Pydantic v2.

Key concepts covered:
- mode="before": Validate/transform raw dict before model creation
- mode="after": Validate cross-field constraints after model is built
- Access to all fields for business rule enforcement
- Returning Self for method chaining
- Handling optional/conditional field dependencies

Real-world use cases:
- Password confirmation matching
- Subscription plan + feature flag consistency
- Address normalization based on country
- Calculated field dependencies
"""

from pydantic import BaseModel, Field, model_validator, ValidationError, EmailStr
from typing import Self, Optional, Dict, Any
from datetime import datetime
import re


class ModelValidatorDemo(BaseModel):
    """
    Comprehensive example of @model_validator patterns.
    
    Demonstrates cross-field validation and data transformation
    at the model level (not just individual fields).
    """
    
    # === Basic fields for cross-field validation ===
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str
    
    # === Business logic fields ===
    subscription: str = Field(default="free", pattern="^(free|pro|enterprise)$")
    is_premium: bool = Field(default=False)
    trial_ends_at: Optional[datetime] = None
    
    # === Address fields for geo-validation ===
    country: str = Field(min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    postal_code: Optional[str] = None
    
    # === mode="before": Transform raw input dict ===
    @model_validator(mode="before")
    @classmethod
    def normalize_input_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        BEFORE model creation: Clean and normalize incoming data.
        
        Use cases:
        - Map legacy API field names to new model structure
        - Coalesce multiple input formats into standard format
        - Apply default values based on other fields
        
        Note: 'values' is a raw dict, not yet validated.
        Return modified dict or raise ValueError.
        """
        # Example 1: Handle legacy field name mapping
        if "email_address" in values and "email" not in values:
            values["email"] = values.pop("email_address")
        
        # Example 2: Auto-set country from postal code prefix (demo)
        if "postal_code" in values and "country" not in values:
            pc = str(values["postal_code"])
            if pc[:2].upper() in ["US", "CA", "GB", "DE", "FR"]:
                values["country"] = pc[:2].upper()
        
        # Example 3: Trim all string fields (common data cleaning)
        for key, value in values.items():
            if isinstance(value, str):
                values[key] = value.strip()
        
        return values
    
    # === mode="after": Cross-field business rules ===
    @model_validator(mode="after")
    def validate_subscription_consistency(self) -> Self:
        """
        AFTER model creation: Enforce business rules across fields.
        
        Rules enforced:
        1. Passwords must match
        2. Premium flag must align with subscription tier
        3. Trial end date only valid for free/pro tiers
        4. Postal code format matches country (demo)
        
        Note: 'self' has all fields validated individually.
        Return self or raise ValueError.
        """
        # Rule 1: Password confirmation
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        
        # Rule 2: Subscription tier consistency
        if self.subscription == "free":
            if self.is_premium:
                raise ValueError("Free tier cannot have premium flag enabled")
        elif self.subscription in ["pro", "enterprise"]:
            if not self.is_premium:
                # Auto-correct instead of error (business decision)
                self.is_premium = True
        
        # Rule 3: Trial end date logic
        if self.trial_ends_at:
            if self.subscription == "enterprise":
                raise ValueError("Enterprise tier does not support trials")
            if self.trial_ends_at <= datetime.utcnow():
                raise ValueError("Trial end date must be in the future")
        
        # Rule 4: Postal code format by country (simplified demo)
        if self.country and self.postal_code:
            if self.country == "US" and not re.match(r"^\d{5}(-\d{4})?$", self.postal_code):
                raise ValueError("US postal code must be in format 12345 or 12345-6789")
            elif self.country == "CA" and not re.match(r"^[A-Z]\d[A-Z] ?\d[A-Z]\d$", self.postal_code.upper()):
                raise ValueError("Canadian postal code must be in format A1A 1A1")
        
        return self
    
    # === Additional after validator for computed fields ===
    @model_validator(mode="after")
    def set_derived_fields(self) -> Self:
        """
        Example: Set computed/derived fields after validation.
        
        In real apps, you might:
        - Generate user slug from username
        - Set timezone from country
        - Calculate subscription features
        
        Note: This runs AFTER validate_subscription_consistency.
        Order of @model_validator(mode="after") methods is definition order.
        """
        # Example: Auto-generate display name if not provided
        # (Would be a separate field in real model)
        return self


# === Real-world example: Order validation ===

class OrderItem(BaseModel):
    """Simple order line item."""
    product_id: int
    quantity: int = Field(ge=1, le=100)
    unit_price: float = Field(ge=0.01)


class OrderValidation(BaseModel):
    """
    Complex order validation with multiple model validators.
    
    Business rules:
    - Total must match sum of items
    - Discount cannot exceed order total
    - Shipping method must be valid for destination country
    """
    
    customer_email: EmailStr
    items: list[OrderItem]
    subtotal: float
    discount: float = Field(default=0.0, ge=0.0)
    shipping_cost: float = Field(ge=0.0)
    total: float
    country: str
    shipping_method: str = Field(pattern="^(standard|express|overnight)$")
    
    @model_validator(mode="before")
    @classmethod
    def calculate_missing_totals(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-calculate subtotal/total if not provided.
        Useful for flexible API input.
        """
        if "items" in values and "subtotal" not in values:
            items = values["items"]
            if isinstance(items, list):
                calculated_subtotal = sum(
                    item["quantity"] * item["unit_price"] 
                    for item in items 
                    if isinstance(item, dict)
                )
                values["subtotal"] = calculated_subtotal
        
        return values
    
    @model_validator(mode="after")
    def validate_order_totals(self) -> Self:
        """Verify financial calculations are consistent."""
        # Recalculate expected subtotal
        calculated_subtotal = sum(
            item.quantity * item.unit_price 
            for item in self.items
        )
        
        # Allow small floating point tolerance
        if abs(self.subtotal - calculated_subtotal) > 0.01:
            raise ValueError(
                f"Subtotal {self.subtotal} does not match items total {calculated_subtotal}"
            )
        
        # Calculate expected total
        expected_total = self.subtotal - self.discount + self.shipping_cost
        
        if abs(self.total - expected_total) > 0.01:
            raise ValueError(
                f"Total {self.total} does not match calculated {expected_total}"
            )
        
        return self
    
    @model_validator(mode="after")
    def validate_discount_limits(self) -> Self:
        """Business rule: Discount cannot exceed subtotal."""
        if self.discount > self.subtotal:
            raise ValueError("Discount cannot exceed order subtotal")
        # Additional rule: Max 50% discount for non-enterprise
        if self.discount > (self.subtotal * 0.5):
            raise ValueError("Discount exceeds maximum allowed (50% of subtotal)")
        return self
    
    @model_validator(mode="after")
    def validate_shipping_availability(self) -> Self:
        """Check shipping method availability by country."""
        # Demo business rules
        restricted_methods = {
            "CA": ["overnight"],  # No overnight to Canada (demo)
            "AU": ["overnight", "express"],  # Limited options to Australia
        }
        
        if self.country in restricted_methods:
            if self.shipping_method in restricted_methods[self.country]:
                raise ValueError(
                    f"Shipping method '{self.shipping_method}' not available to {self.country}"
                )
        
        return self


# === Example: Profile update with conditional validation ===

class ProfileUpdate(BaseModel):
    """
    Profile update with conditional field requirements.
    
    Demonstrates:
    - Optional fields that become required based on other values
    - Cross-field validation for consistency
    """
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)
    
    # Conditional: If changing email, must provide password
    new_email: Optional[EmailStr] = None
    password_for_change: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_email_change_requirements(self) -> Self:
        """If new_email is provided, password confirmation is required."""
        if self.new_email is not None:
            if not self.password_for_change:
                raise ValueError("Password required to change email address")
            if len(self.password_for_change) < 8:
                raise ValueError("Password must be at least 8 characters for security")
        return self