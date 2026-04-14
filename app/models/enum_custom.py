# app/models/enum_custom.py
"""
🎓 Enums & Custom Types in Pydantic v2

Demonstrates:
- StrEnum for string-compatible enums (API-friendly)
- EmailStr, HttpUrl, SecretStr custom validators
- PastDate/FutureDate constraint helpers
- Enum metadata for frontend dropdown generation
- PlaygroundConfig for interactive learning

🎓 INTERACTIVE LEARNING READY:
- Enum values → frontend <select> options
- Custom type validation → immediate error feedback
- SecretStr masking → safe demo of sensitive data handling
"""

from enum import StrEnum
from pydantic import BaseModel, Field, SecretStr, HttpUrl, EmailStr, field_validator
from pydantic.types import PastDate, FutureDate
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
import re


# === StrEnum Definitions (String-Compatible for APIs) ===

class UserRole(StrEnum):
    """User permission levels."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"
    
    @property
    def display_name(self) -> str:
        return self.value.capitalize()
    
    @property
    def permissions(self) -> List[str]:
        perms = {
            "admin": ["read", "write", "delete", "manage_users"],
            "moderator": ["read", "write", "delete"],
            "user": ["read", "write"],
            "guest": ["read"],
        }
        return perms.get(self.value, [])


class AccountStatus(StrEnum):
    """Account lifecycle states."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DELETED = "deleted"
    
    @property
    def is_active_state(self) -> bool:
        return self.value in ["active", "pending"]
    
    @property
    def color_code(self) -> str:
        colors = {
            "pending": "yellow",
            "active": "green",
            "suspended": "orange",
            "archived": "gray",
            "deleted": "red",
        }
        return colors.get(self.value, "gray")


class Theme(StrEnum):
    """UI theme preferences."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class NotificationFrequency(StrEnum):
    """How often to send notifications."""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


# === Main Demo Model ===

class UserWithEnums(BaseModel):
    """
    User model with validated enum fields and custom types.
    
    🎓 Interactive: Select enum values from dropdown, see validation.
    """
    
    id: int = Field(..., description="Unique identifier")
    username: str = Field(..., min_length=3, max_length=30)
    
    # Custom type: EmailStr validates RFC format
    email: EmailStr = Field(..., description="Valid email address")
    
    # Enum fields: Only accept defined values
    role: UserRole = Field(default=UserRole.USER, description="User permission level")
    status: AccountStatus = Field(default=AccountStatus.PENDING, description="Account lifecycle state")
    theme: Theme = Field(default=Theme.AUTO, description="UI theme preference")
    notification_freq: NotificationFrequency = Field(default=NotificationFrequency.DAILY)
    
    # Custom types demo
    website: Optional[HttpUrl] = Field(default=None, description="User website")
    api_key: Optional[SecretStr] = Field(default=None, description="API key (masked)")
    birth_date: Optional[PastDate] = Field(default=None, description="Must be in past")
    
    # Computed properties
    @property
    def can_login(self) -> bool:
        """Business rule: Only active/pending users can login."""
        return self.status.is_active_state
    
    @property
    def permission_summary(self) -> str:
        """Human-readable permissions list."""
        perms = self.role.permissions
        if not perms:
            return "No permissions"
        return ", ".join(perms[:3]) + ("..." if len(perms) > 3 else "")
    
    def to_safe_response(self) -> Dict[str, Any]:
        """Serialize with sensitive fields masked."""
        data = self.model_dump(mode="json", exclude_none=True)
        if data.get("api_key"):
            data["api_key"] = "********"  # Masked for safety
        return data
    
    # Playground metadata for frontend
    class PlaygroundMeta:
        """Metadata for interactive playground UI generation."""
        enum_fields = {
            "role": {
                "options": [{"value": r.value, "label": r.display_name, "permissions": r.permissions} for r in UserRole],
                "default": UserRole.USER.value,
                "description": "Select user role"
            },
            "status": {
                "options": [{"value": s.value, "label": s.value.capitalize(), "color": s.color_code} for s in AccountStatus],
                "default": AccountStatus.PENDING.value,
                "description": "Account status"
            },
            "theme": {
                "options": [{"value": t.value, "label": t.value.capitalize()} for t in Theme],
                "default": Theme.AUTO.value,
                "description": "UI theme"
            },
            "notification_freq": {
                "options": [{"value": f.value, "label": f.value.capitalize()} for f in NotificationFrequency],
                "default": NotificationFrequency.DAILY.value,
                "description": "Notification frequency"
            },
        }


# === Custom Types Demo Model ===

class CustomTypesDemo(BaseModel):
    """
    Demonstrate Pydantic's built-in custom types.
    
    🎓 Interactive: Test invalid email/URL → see specific error messages.
    """
    
    # EmailStr: RFC-compliant email validation
    contact_email: EmailStr = Field(..., description="Primary contact email")
    
    # HttpUrl: Validates URL format, scheme, TLD
    website: Optional[HttpUrl] = Field(default=None, description="User website or profile URL")
    
    # SecretStr: Automatically masks value in repr/str
    api_key: SecretStr = Field(..., description="API key (masked in logs)")
    
    # PastDate/FutureDate: Date constraints
    birth_date: PastDate = Field(..., description="Must be in the past")
    subscription_renewal: Optional[FutureDate] = Field(default=None, description="Next renewal date")
    
    # Constrained string with pattern
    phone_us: Optional[str] = Field(
        default=None,
        pattern=r"^\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$",
        description="US phone: (555) 123-4567"
    )
    
    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Ensure API key starts with 'sk_' prefix."""
        if isinstance(v, str) and not v.startswith("sk_"):
            raise ValueError("API key must start with 'sk_' prefix")
        return v
    
    def get_masked_api_key(self) -> str:
        """Return masked API key for safe display."""
        plain = self.api_key.get_secret_value()
        if len(plain) <= 4:
            return "*" * len(plain)
        return "*" * (len(plain) - 4) + plain[-4:]
    
    def to_safe_response(self) -> Dict[str, Any]:
        """Serialize with sensitive fields masked."""
        data = self.model_dump(mode="json", exclude_none=True)
        if "api_key" in data:
            data["api_key"] = self.get_masked_api_key()
        return data
    
    class PlaygroundTips:
        """Help text for each custom type in interactive UI."""
        tips = {
            "contact_email": "Enter valid email: user@example.com",
            "website": "Enter full URL: https://example.com/user",
            "api_key": "Sensitive value - will be masked in responses",
            "birth_date": "Must be a past date (YYYY-MM-DD)",
            "phone_us": "Format: (555) 123-4567 or 5551234567",
        }


# === Payment Profile with Enums ===

class PaymentProfile(BaseModel):
    """Payment profile with enum and custom type fields."""
    
    user_id: int = Field(..., description="User identifier")
    
    # Enum for payment method type
    method_type: StrEnum = Field(default="card", description="Payment method type")  # Simplified for demo
    
    # Conditional fields (validated with field_validator)
    card_last_four: Optional[str] = Field(default=None, pattern=r"^\d{4}$")
    bank_name: Optional[str] = Field(default=None, min_length=2)
    
    # Common fields
    is_default: bool = Field(default=False)
    nickname: Optional[str] = Field(default=None, max_length=30)
    
    @property
    def masked_details(self) -> Optional[str]:
        """Masked payment details for display."""
        if self.card_last_four:
            return f"**** **** **** {self.card_last_four}"
        elif self.bank_name:
            return f"{self.bank_name} (****)"
        return None


# === Playground Helper for Enum Demo ===

class EnumPlayground:
    """
    Helper for interactive enum learning.
    
    🎓 Frontend: Use this to generate dropdowns, validate selections, show metadata.
    """
    
    @classmethod
    def get_enum_schema(cls, enum_class: type[StrEnum]) -> Dict[str, Any]:
        """
        Generate JSON Schema for enum (for frontend form generation).
        
        🎓 Output: Use in React/Vue to create <select> with options.
        """
        return {
            "type": "string",
            "enum": [e.value for e in enum_class],
            "title": enum_class.__name__,
            "description": f"Select one of: {', '.join(e.value for e in enum_class)}",
            "x-display": "dropdown",  # Custom hint for UI library
            "x-options": [
                {
                    "value": e.value,
                    "label": getattr(e, "display_name", e.value.capitalize()),
                    "permissions": getattr(e, "permissions", None),
                    "color_code": getattr(e, "color_code", None),
                }
                for e in enum_class
            ],
        }
    
    @classmethod
    def validate_enum_selection(cls, enum_class: type[StrEnum], value: str) -> Dict[str, Any]:
        """
        Validate a string against enum values.
        
        🎓 Interactive: User types/picks value → show valid/invalid + suggestions.
        """
        valid_values = [e.value for e in enum_class]
        
        if value in valid_values:
            enum_member = enum_class(value)
            return {
                "valid": True,
                "value": value,
                "enum_member": enum_member.name,
                "metadata": {
                    "display_name": getattr(enum_member, "display_name", value.capitalize()),
                    "permissions": getattr(enum_member, "permissions", None),
                    "color_code": getattr(enum_member, "color_code", None),
                }
            }
        
        # Provide helpful error with suggestions
        suggestions = [v for v in valid_values if value.lower() in v.lower()]
        return {
            "valid": False,
            "value": value,
            "error": f"'{value}' is not a valid {enum_class.__name__}",
            "allowed": valid_values,
            "suggestions": suggestions if suggestions else None,
            "hint": f"Must be one of: {', '.join(valid_values)}",
        }