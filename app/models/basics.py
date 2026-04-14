"""
🎓 Pydantic Basics: BaseModel, Field, Constraints, Defaults

Demonstrates:
- Field constraints: min_length, max_length, pattern, ge, le, etc.
- Optional fields with defaults and default_factory
- Nested dict fields and datetime handling
- Field metadata: description, examples, json_schema_extra
- Model methods: model_dump(), model_validate(), model_copy()
- PlaygroundConfig for interactive learning frontend

🎓 INTERACTIVE LEARNING READY:
- Every field has examples for "try it" buttons
- Field constraints show immediate feedback on invalid input
- model_dump() modes demonstrated: python vs json vs pretty
- Error messages include field name + constraint for learning
- Playground metadata enables auto-generated forms
"""

from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import Optional, List, Dict, Any, Union, Set  # ✅ Added Set
from datetime import datetime, date
from enum import StrEnum
import re


# === Basic User Model (Using Provided Dataset) ===

class UserBasic(BaseModel):
    """
    Basic user model matching the provided dataset structure.
    
    🎓 Learning Focus: Foundation for all other examples.
    Start here to understand BaseModel + Field before advanced features.
    
    Dataset example:
    {
        "id": 1,
        "username": "alice_dev",
        "email": "alice@example.com",
        "role": "admin",
        "api_key": "sk_test_1234567890",
        "is_active": true,
        "address": {"street": "123 Code Ave", "city": "Techville", "country": "US"},
        "created_at": "2025-01-15T10:30:00"
    }
    """
    
    # === Required Fields ===
    
    id: int = Field(
        ...,  # Ellipsis = required field
        description="Unique user identifier",
        examples=[1, 42, 100],
        json_schema_extra={"x-order": 1}  # Custom OpenAPI extension
    )
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",  # Alphanumeric + underscore only
        description="Unique username (3-30 chars, alphanumeric)",
        examples=["alice_dev", "bob_user", "charlie123"],
        json_schema_extra={
            "x-placeholder": "Enter username",
            "x-error-messages": {
                "min_length": "Username must be at least 3 characters",
                "max_length": "Username cannot exceed 30 characters",
                "pattern": "Only letters, numbers, and underscores allowed"
            }
        }
    )
    
    email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Valid email address",
        examples=["alice@example.com", "bob@company.org"],
        json_schema_extra={"format": "email"}
    )
    
    # === Optional Fields with Defaults ===
    
    role: str = Field(
        default="user",
        pattern=r"^(admin|moderator|user|guest)$",
        description="User role/permission level",
        examples=["admin", "user", "moderator"],
        json_schema_extra={"x-display": "dropdown"}
    )
    
    api_key: Optional[str] = Field(
        default=None,
        min_length=20,
        max_length=100,
        pattern=r"^sk_[a-zA-Z0-9_]+$",  # Demo: simple API key format
        description="API key (starts with 'sk_')",
        examples=["sk_test_1234567890abcdef", "sk_prod_xyz789secret"],
        json_schema_extra={"x-sensitive": True}  # Hint for UI masking
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether user account is active",
        examples=[True, False],
        json_schema_extra={"x-display": "toggle"}
    )
    
    # === Nested Model Field ===
    
    address: Optional[Dict[str, str]] = Field(
        default=None,
        description="User address (street, city, country)",
        examples=[
            {"street": "123 Code Ave", "city": "Techville", "country": "US"},
            {"street": "456 Data Ln", "city": "CloudCity", "country": "UK"}
        ],
        json_schema_extra={
            "x-nested-fields": {
                "street": {"type": "string", "required": True},
                "city": {"type": "string", "required": True},
                "country": {"type": "string", "required": True, "pattern": "^[A-Z]{2}$"}
            }
        }
    )
    
    # === DateTime Field ===
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),  # ✅ Fixed: timezone-aware compatible
        description="Account creation timestamp (ISO 8601)",
        examples=["2025-01-15T10:30:00Z", "2025-02-20T14:00:00+00:00"],
        json_schema_extra={"format": "date-time"}
    )
    
    # === Model Configuration ===
    
    model_config = ConfigDict(
        str_strip_whitespace=True,  # Auto-trim all string fields
        populate_by_name=True,       # Accept both field name and alias
        extra="ignore",              # Silently ignore unknown fields (lenient for demo)
        # In production: extra="forbid" to catch typos
    )
    
    # === Useful Model Methods ===
    
    def to_public_response(self) -> Dict[str, Any]:
        """
        Serialize for public API: hide sensitive fields.
        
        🎓 Learning: Show controlled serialization patterns.
        """
        return self.model_dump(
            mode="json",
            exclude={"api_key"},  # Never expose API key
            exclude_none=True,     # Remove None values for cleaner JSON
        )
    
    def to_admin_response(self) -> Dict[str, Any]:
        """
        Serialize for admin view: include all fields.
        """
        return self.model_dump(mode="json", exclude_none=False)
    
    def update(self, **updates: Any) -> "UserBasic":
        """
        Create updated copy with new values (immutable pattern).
        
        🎓 Learning: Demonstrate model_copy() for safe updates.
        """
        return self.model_copy(update=updates)
    
    # === Playground Metadata ===
    
    class PlaygroundConfig:
        """
        Configuration for interactive learning playground.
        
        🎓 Frontend: Read this via model_json_schema() to auto-generate forms.
        """
        form_layout = {
            "sections": [
                {
                    "title": "Account Info",
                    "fields": ["id", "username", "email", "role"],
                    "collapsible": False
                },
                {
                    "title": "Security",
                    "fields": ["api_key", "is_active"],
                    "collapsible": True,
                    "default_collapsed": True
                },
                {
                    "title": "Profile",
                    "fields": ["address", "created_at"],
                    "collapsible": True
                }
            ]
        }
        
        validation_hints = {
            "username": "3-30 characters, letters/numbers/underscores only",
            "email": "Must be valid format: user@domain.com",
            "api_key": "Optional. If provided, must start with 'sk_' and be 20-100 chars",
            "address.country": "Two-letter country code: US, UK, CA, etc.",
        }


# === Address Sub-Model (For Nested Demo) ===

class AddressBasic(BaseModel):
    """
    Reusable address model.
    
    🎓 Learning: Show nested model composition.
    """
    
    street: str = Field(..., min_length=5, max_length=200, examples=["123 Code Ave"])
    city: str = Field(..., min_length=2, max_length=100, examples=["Techville"])
    state: Optional[str] = Field(default=None, max_length=100, examples=["CA"])
    country: str = Field(..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$", examples=["US"])
    postal_code: Optional[str] = Field(default=None, max_length=20, examples=["94105"])
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @property
    def formatted(self) -> str:
        """Human-readable address format."""
        parts = [self.street, self.city]
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ", ".join(p for p in parts if p)


# === Enhanced User with Nested Address ===

class UserWithAddress(BaseModel):
    """User model with properly nested Address model."""
    
    id: int = Field(..., description="Unique identifier")
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    
    # Nested model (properly typed)
    address: Optional[AddressBasic] = Field(default=None)
    
    # Other fields from dataset
    role: str = Field(default="user", pattern=r"^(admin|moderator|user|guest)$")
    api_key: Optional[str] = Field(default=None, min_length=20)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Format for human-readable display."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "status": "Active" if self.is_active else "Inactive",
            "address": self.address.formatted if self.address else "Not provided",
            "member_since": self.created_at.strftime("%B %Y"),
        }


# === Field Constraint Examples ===

class ConstraintExamples(BaseModel):
    """
    Showcase various Field() constraints.
    
    🎓 Interactive: Try invalid values to see specific error messages.
    """
    
    # === String Constraints ===
    short_text: str = Field(..., min_length=1, max_length=50, description="1-50 characters")
    pattern_text: str = Field(..., pattern=r"^[A-Z][a-z]+$", description="Capitalized word only")
    
    # === Numeric Constraints ===
    positive_int: int = Field(..., gt=0, description="Must be > 0")
    bounded_int: int = Field(..., ge=0, le=100, description="0-100 inclusive")
    multiple_of: int = Field(..., multiple_of=5, description="Must be multiple of 5")
    
    # === Float Constraints ===
    percentage: float = Field(..., ge=0.0, le=100.0, description="0.0 to 100.0")
    price: float = Field(..., gt=0.0, description="Positive value")  # ✅ Removed decimal_places (not valid in Field)
    
    # === List Constraints ===
    tags: List[str] = Field(..., min_length=1, max_length=10, description="1-10 tags")
    
    # ✅ FIX: Use Set instead of List with unique_items (removed in Pydantic v2)
    unique_ids: Set[int] = Field(..., description="No duplicate IDs (Set enforces uniqueness)")
    
    # === Optional with Default Factory ===
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary key-value pairs")
    
    # === Union Field ===
    flexible_value: Union[str, int, float] = Field(..., description="Accept string, int, or float")
    
    # === Playground: Show constraint in action ===
    class PlaygroundExamples:
        """Example valid/invalid inputs for each field."""
        examples = {
            "short_text": {
                "valid": ["Hello", "Pydantic"],
                "invalid": ["", "a" * 100],
                "errors": ["String should have at least 1 character", "String should have at most 50 characters"]
            },
            "pattern_text": {
                "valid": ["Hello", "World"],
                "invalid": ["hello", "HELLO", "Hello123"],
                "errors": ["String should match pattern"]
            },
            "positive_int": {
                "valid": [1, 42, 100],
                "invalid": [0, -5, "10"],
                "errors": ["Input should be greater than 0", "Input should be a valid integer"]
            },
            "percentage": {
                "valid": [0.0, 50.5, 100.0],
                "invalid": [-1, 101, "50"],
                "errors": ["Input should be greater than or equal to 0", "Input should be less than or equal to 100"]
            },
            "unique_ids": {
                "valid": [[1, 2, 3], [42]],  # Set accepts list input, dedupes automatically
                "invalid": "Not applicable - Set enforces uniqueness automatically",
            },
        }


# === Basic Model Methods Demo ===

class MethodsDemo(BaseModel):
    """
    Demonstrate essential Pydantic model methods.
    
    🎓 Learning: Show the core API every developer should know.
    """
    
    name: str = Field(..., examples=["Alice"])
    score: float = Field(..., ge=0.0, le=100.0, examples=[95.5])
    tags: List[str] = Field(default_factory=list, examples=[["python", "pydantic"]])
    
    # === model_validate: Create from dict ===
    @classmethod
    def from_dict_example(cls,  dict) -> "MethodsDemo":
        """
        Validate and create instance from dictionary.
        
        🎓 Interactive: Paste JSON → see validation result.
        """
        return cls.model_validate(data)
    
    # === model_dump: Serialize to dict ===
    def to_dict_python(self) -> Dict[str, Any]:
        """Serialize with Python types (datetime objects, etc.)."""
        return self.model_dump(mode="python")
    
    def to_dict_json(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible types (strings for dates)."""
        return self.model_dump(mode="json")
    
    def to_dict_pretty(self) -> str:
        """Serialize to formatted JSON string."""
        import json
        return json.dumps(self.model_dump(mode="json"), indent=2)
    
    # === model_copy: Create modified copy ===
    def with_updated_score(self, new_score: float) -> "MethodsDemo":
        """Return new instance with updated score."""
        return self.model_copy(update={"score": new_score})
    
    def with_added_tag(self, tag: str) -> "MethodsDemo":
        """Return new instance with tag added to list."""
        new_tags = self.tags + [tag]
        return self.model_copy(update={"tags": new_tags})
    
    # === dict() legacy method (still works but prefer model_dump) ===
    def to_legacy_dict(self) -> Dict[str, Any]:
        """Legacy method (Pydantic v1 style)."""
        return self.dict()  # Works but model_dump() is preferred in v2


# === Playground Helper for Basics ===

class BasicsPlayground:
    """
    Helper for interactive basics learning.
    
    🎓 Frontend: Use to generate forms, show examples, display errors.
    """
    
    @classmethod
    def get_field_info(cls, model: type[BaseModel], field_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract field metadata for form generation.
        
        🎓 Output: Use in React/Vue to create labeled inputs with validation.
        """
        field = model.model_fields.get(field_name)
        if not field:
            return None
        
        return {
            "name": field_name,
            "type": str(field.annotation),
            "required": field.is_required(),
            "default": field.default if not field.is_required() else None,
            "constraints": {
                "min_length": getattr(field, "min_length", None),
                "max_length": getattr(field, "max_length", None),
                "pattern": getattr(field, "pattern", None),
                "ge": getattr(field, "ge", None),
                "le": getattr(field, "le", None),
                "gt": getattr(field, "gt", None),
                "lt": getattr(field, "lt", None),
            },
            "metadata": {
                "description": field.description,
                "examples": field.examples,
                "title": field.title,
            },
            "json_schema": field.json_schema_extra,
        }
    
    @classmethod
    def generate_example_payload(cls, model: type[BaseModel]) -> Dict[str, Any]:
        """
        Generate valid example payload from field examples.
        
        🎓 Interactive: "Fill with example" button in playground.
        """
        payload = {}
        for field_name, field in model.model_fields.items():
            if field.examples:
                # Use first example
                payload[field_name] = field.examples[0]
            elif not field.is_required() and field.default is not None:
                # Use default for optional fields
                payload[field_name] = field.default
            # Skip required fields without examples (user must fill)
        return payload
    
    @classmethod
    def format_validation_error(cls, error: dict) -> str:
        """
        Format Pydantic error for user-friendly display.
        
        🎓 Learning: Turn technical errors into helpful messages.
        """
        field_path = ".".join(str(loc) for loc in error.get("loc", []) if loc != "body")
        msg = error.get("msg", "Validation failed")
        error_type = error.get("type", "unknown")
        
        # Customize messages for common errors
        custom_messages = {
            "string_too_short": f"{field_path} is too short",
            "string_too_long": f"{field_path} is too long",
            "value_error": f"Invalid value for {field_path}",
            "int_parsing": f"{field_path} must be a number",
            "float_parsing": f"{field_path} must be a number",
            "pattern": f"{field_path} format is invalid",
        }
        
        return custom_messages.get(error_type, f"{field_path}: {msg}")
    
    @classmethod
    def _get_validation_tips(cls, model_name: str, errors: List[dict]) -> List[str]:
        """
        Generate helpful tips based on validation errors.
        
        🎓 Learning: Turn errors into teaching moments.
        """
        tips = []
        error_types = set(err["type"] for err in errors)
        
        if "int_parsing" in error_types or "float_parsing" in error_types:
            tips.append("💡 Tip: Make sure numbers don't have quotes: use 42, not \"42\"")
        
        if "string_pattern_mismatch" in error_types:
            if "email" in model_name.lower() or "Email" in model_name:
                tips.append("💡 Tip: Email must be format: user@domain.com")
        
        if "list_type" in error_types:
            tips.append("💡 Tip: Lists use square brackets: [1, 2, 3]")
        
        if "dict_type" in error_types:
            tips.append("💡 Tip: Objects use curly braces: {\"key\": \"value\"}")
        
        if "extra_forbidden" in error_types:
            tips.append("💡 Tip: Remove fields not defined in the schema")
        
        return tips if tips else ["💡 Tip: Check the error messages above for details"]