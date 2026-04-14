"""
Demonstrates Pydantic serialization features in v2.

Key concepts covered:
- model_dump() modes: "python" vs "json" vs "jsonable"
- @field_serializer for custom output formatting
- include/exclude parameters for partial serialization
- round_trip mode for lossless serialization/deserialization
- by_alias control for field name mapping
- Custom serializers for datetime, secrets, nested models

Real-world use cases:
- API response formatting (hide internal fields)
- Database storage optimization
- Frontend payload minimization
- Audit logging with sensitive data masking
"""

from pydantic import BaseModel, Field, field_serializer, SecretStr, computed_field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import StrEnum
import json


class Theme(StrEnum):
    """User interface theme options."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class SerializationDemo(BaseModel):
    """
    Comprehensive serialization example with multiple techniques.
    
    Demonstrates how to control output format for different contexts:
    - Public API responses
    - Internal logging
    - Database storage
    - Frontend consumption
    """
    
    # === Basic fields ===
    id: int
    username: str
    email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # === Sensitive data ===
    api_key: SecretStr  # Automatically masked in str() and repr()
    internal_notes: Optional[str] = Field(default=None, exclude=True)  # Always excluded
    
    # === Complex types ===
    preferences: Dict[str, Any]  # JSON-compatible dict
    tags: List[str]
    theme: Theme = Theme.AUTO
    
    # === Computed field (v2 feature) ===
    @computed_field
    @property
    def account_age_days(self) -> int:
        """Calculate account age in days (computed, not stored)."""
        if not self.created_at:
            return 0
        return (datetime.utcnow() - self.created_at).days
    
    # === Custom field serializers ===
    
    @field_serializer("created_at", "last_login")
    def serialize_datetime_iso(self, dt: Optional[datetime]) -> Optional[str]:
        """
        Serialize datetime to ISO 8601 string with timezone info.
        
        This ensures consistent format across all datetime fields.
        Returns None if field is None (Optional fields).
        """
        if dt is None:
            return None
        # Ensure UTC timezone for API consistency
        if dt.tzinfo is None:
            # Assume UTC if no timezone (not recommended in production)
            return dt.isoformat() + "Z"
        return dt.isoformat()
    
    @field_serializer("api_key")
    def serialize_api_key_masked(self, key: SecretStr) -> str:
        """
        Serialize SecretStr to masked format for logging/responses.
        
        Shows last 4 characters only for security.
        Note: SecretStr.model_dump() already masks by default,
        but this demonstrates custom masking logic.
        """
        # Get the secret value (only safe in serializer context)
        plain = key.get_secret_value()
        if len(plain) <= 4:
            return "*" * len(plain)
        return "*" * (len(plain) - 4) + plain[-4:]
    
    @field_serializer("preferences", mode="plain")
    def serialize_preferences_flat(self, prefs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten or transform preferences dict for frontend consumption.
        
        mode="plain" means we receive the raw Python value, not a serialized one.
        Useful for transforming nested structures.
        """
        # Example: Add derived preference flags
        result = prefs.copy() if prefs else {}
        if "notifications" in result:
            result["has_notifications_enabled"] = bool(result["notifications"])
        return result
    
    @field_serializer("tags", when_used="json")
    def serialize_tags_as_string(self, tags: List[str]) -> str:
        """
        Serialize tags list as comma-separated string for JSON output only.
        
        when_used="json" means this only applies to model_dump(mode="json").
        Python mode still returns the original list.
        """
        return ",".join(tags)
    
    # === Serialization helper methods ===
    
    def to_public_response(self) -> Dict[str, Any]:
        """
        Serialize for public API response.
        
        Excludes:
        - internal_notes (via Field(exclude=True))
        - raw api_key (via custom serializer)
        - Any fields marked exclude=True
        
        Includes:
        - Computed fields (account_age_days)
        - Formatted datetime strings
        """
        return self.model_dump(
            mode="json",           # Convert all types to JSON-compatible
            exclude={"internal_notes"},  # Explicit exclude (redundant but clear)
            exclude_none=True,     # Remove None values to reduce payload
            by_alias=False         # Use field names, not aliases
        )
    
    def to_admin_view(self) -> Dict[str, Any]:
        """
        Serialize for admin/internal use.
        
        Includes sensitive fields but masks appropriately.
        """
        return self.model_dump(
            mode="json",
            exclude_none=False,    # Keep None for admin debugging
            include={"id", "username", "email", "api_key", "internal_notes", "created_at"}
        )
    
    def to_frontend_payload(self) -> Dict[str, Any]:
        """
        Minimal payload for frontend consumption.
        
        Only fields needed for UI rendering.
        """
        return self.model_dump(
            mode="json",
            include={"username", "email", "theme", "tags", "account_age_days"},
            exclude_unset=True     # Only include fields that were explicitly set
        )
    
    def to_database_dict(self) -> Dict[str, Any]:
        """
        Serialize for database storage.
        
        Uses round_trip mode to preserve all type information.
        """
        return self.model_dump(
            mode="python",         # Keep Python types for ORM compatibility
            round_trip=True,       # Ensure lossless serialization
            exclude={"internal_notes"}  # Don't store internal notes
        )


# === Advanced: Conditional serialization based on context ===

class ContextAwareModel(BaseModel):
    """
    Model that serializes differently based on context.
    
    Demonstrates:
    - Dynamic field inclusion/exclusion
    - Serializer that receives context via info
    - Custom serialization modes
    """
    
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    internal_id: str = Field(exclude=True)  # Never serialize normally
    
    @field_serializer("email", "phone")
    def serialize_contact_info(self, value: Optional[str], info) -> Optional[str]:
        """
        Serialize contact info based on caller context.
        
        Access serialization context via info:
        - info.mode: "python" or "json"
        - info.include/exclude: field selection
        - info.context: custom dict passed to model_dump()
        """
        # Example: Mask email if requested via context
        context = info.context or {}
        if context.get("mask_contacts") and value:
            if "@" in value:  # Email
                parts = value.split("@")
                return f"{parts[0][0]}***@{parts[1]}"
            else:  # Phone
                return "***-***-" + value[-4:] if len(value) >= 4 else "***"
        return value
    
    def dump_with_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize with custom context passed to field serializers.
        
        Usage:
            model.dump_with_context({"mask_contacts": True})
        """
        return self.model_dump(mode="json", context=context)


# === Example: Nested model serialization ===

class Address(BaseModel):
    """Nested address model with its own serialization rules."""
    street: str
    city: str
    country: str
    postal_code: str
    
    @field_serializer("postal_code")
    def format_postal_code(self, code: str) -> str:
        """Format postal code based on country (simplified)."""
        if self.country == "US":
            # Ensure ZIP+4 format
            if "-" not in code and len(code) == 5:
                return code
        return code


class UserWithAddress(BaseModel):
    """User model with nested Address."""
    id: int
    name: str
    address: Address
    billing_address: Optional[Address] = None
    
    @field_serializer("address", "billing_address")
    def serialize_address_summary(self, addr: Optional[Address]) -> Optional[Dict[str, str]]:
        """
        Serialize address as summary for list views.
        
        Returns only city/country for brevity in list endpoints.
        Full address available via detail endpoint.
        """
        if addr is None:
            return None
        return {
            "summary": f"{addr.city}, {addr.country}",
            "country": addr.country
        }
    
    def to_detail_response(self) -> Dict[str, Any]:
        """Full serialization for detail view."""
        return self.model_dump(
            mode="json",
            exclude_none=True
        )
    
    def to_list_response(self) -> Dict[str, Any]:
        """Minimal serialization for list view."""
        return self.model_dump(
            mode="json",
            include={"id", "name", "address"},
            exclude_none=True
        )