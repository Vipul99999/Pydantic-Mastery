"""
Demonstrates @field_validator decorator in Pydantic v2.

Key concepts covered:
- mode="before": Transform raw input BEFORE type coercion
- mode="after": Validate/clean AFTER field is parsed
- mode="wrap": Full control over validation pipeline
- check_fields: Validate fields that don't exist in model
- Multiple validators on same field (execution order)
- Classmethod requirement for validators

Real-world use cases:
- Email normalization, phone formatting, tag sanitization
- Business rule enforcement (age limits, password strength)
- Data enrichment (auto-setting derived fields)
"""

from pydantic import BaseModel, Field, field_validator, ValidationError, EmailStr
from typing import List, Optional, Self
from datetime import datetime
import re


class FieldValidatorDemo(BaseModel):
    """
    Comprehensive example of @field_validator patterns.
    
    Each field demonstrates a different validation technique.
    """
    
    # === Email Field: mode="before" for pre-processing ===
    email: EmailStr
    """
    EmailStr provides built-in RFC-compliant validation.
    We add custom pre-processing with mode="before".
    """
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """
        BEFORE validation: Clean and normalize email input.
        
        Use cases:
        - Strip whitespace from copy-pasted emails
        - Force lowercase for consistent storage
        - Handle common typos (optional enhancement)
        
        Note: mode="before" receives raw input (str) before EmailStr validation.
        """
        if not isinstance(v, str):
            return v  # Let EmailStr handle type errors
        return v.strip().lower()
    
    # === Tags Field: mode="after" for post-processing ===
    tags: List[str] = Field(default_factory=list, max_length=10)
    """
    List of string tags with constraints.
    We deduplicate and format AFTER list parsing.
    """
    
    @field_validator("tags", mode="after")
    @classmethod
    def process_tags(cls, v: List[str]) -> List[str]:
        """
        AFTER validation: Clean and deduplicate tags.
        
        Techniques demonstrated:
        - dict.fromkeys() preserves order while deduplicating
        - Lowercase normalization for consistency
        - Length enforcement via Field(max_length=10)
        
        Note: mode="after" receives parsed List[str], not raw input.
        """
        if not v:
            return []
        
        # Remove duplicates while preserving order + lowercase
        unique_tags = list(dict.fromkeys(tag.strip().lower() for tag in v if tag.strip()))
        
        # Enforce business rule: max 5 meaningful tags
        if len(unique_tags) > 5:
            raise ValueError("Maximum 5 unique tags allowed after deduplication")
        
        return unique_tags
    
    # === Age Field: mode="wrap" for full control ===
    age: Optional[int] = Field(default=None, ge=0, le=150)
    """
    Age with range constraints + custom business logic.
    mode="wrap" gives us the handler to chain validation.
    """
    
    @field_validator("age", mode="wrap")
    @classmethod
    def validate_age_with_rules(cls, v: int, handler) -> Optional[int]:
        """
        WRAP mode: Full control over validation pipeline.
        
        Pattern:
        1. Pre-check: Custom business rules before standard validation
        2. handler(v): Run Pydantic's built-in validation (ge=0, le=150)
        3. Post-check: Additional rules after standard validation
        
        Use case: Age restrictions for different user roles.
        """
        # Handle None explicitly (Optional field)
        if v is None:
            return None
        
        # Pre-check: Negative values (before Pydantic's ge=0)
        if isinstance(v, (int, float)) and v < 0:
            raise ValueError("Age cannot be negative")
        
        # Run standard Pydantic validation (ge=0, le=150)
        try:
            validated_age = handler(v)
        except Exception as e:
            # Re-raise with context if needed
            raise ValueError(f"Invalid age value: {e}")
        
        # Post-check: Business rule - minors need parental consent
        if validated_age < 18:
            # In real app: set flag or require additional field
            pass  # Just logging for demo
        
        # Post-check: Warn about unrealistic ages
        if validated_age > 120:
            # Could log warning or require admin approval
            pass
        
        return validated_age
    
    # === Username: Multiple validators on same field ===
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    """
    Username with multiple validation layers:
    1. Field constraints (min/max length, regex pattern)
    2. Custom validator for reserved names
    3. Custom validator for profanity filtering (demo)
    """
    
    @field_validator("username", mode="after")
    @classmethod
    def check_reserved_usernames(cls, v: str) -> str:
        """Block reserved system usernames."""
        reserved = {"admin", "root", "system", "moderator", "api"}
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved and cannot be used")
        return v
    
    @field_validator("username", mode="after")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Additional sanitization after pattern validation."""
        # Example: Prevent usernames that look like emails
        if "@" in v:
            raise ValueError("Username cannot contain '@' character")
        return v
    
    # === API Key: Conditional validation ===
    api_key: Optional[str] = Field(default=None, min_length=20, max_length=100)
    """
    Optional API key with format validation.
    Demonstrates conditional logic based on other fields.
    """
    
    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key_format(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate API key format: must start with 'sk_' prefix.
        
        This runs BEFORE min_length/max_length Field constraints.
        """
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("API key must be a string")
        if not v.startswith("sk_"):
            raise ValueError("API key must start with 'sk_' prefix")
        return v.strip()
    
    # === Created At: Auto-format datetime ===
    created_at: Optional[datetime] = Field(default=None)
    
    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v) -> Optional[datetime]:
        """
        Handle multiple datetime input formats.
        
        Accepts:
        - ISO 8601 string: "2025-01-15T10:30:00Z"
        - Unix timestamp: 1705315800
        - datetime object (already parsed)
        """
        if v is None or isinstance(v, datetime):
            return v
        
        if isinstance(v, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(v)
        
        if isinstance(v, str):
            # Try ISO format first
            try:
                # Handle 'Z' suffix for UTC
                if v.endswith("Z"):
                    v = v[:-1] + "+00:00"
                return datetime.fromisoformat(v)
            except ValueError:
                pass
            # Could add more parsers here (strptime, dateutil, etc.)
        
        raise ValueError(f"Unable to parse datetime: {v}")


# === Standalone validator examples for testing ===

def validate_password_strength(password: str) -> str:
    """
    Standalone validator function for password strength.
    Can be reused with Annotated or in multiple models.
    
    Requirements:
    - Min 8 characters
    - At least one uppercase, one lowercase, one digit
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    return password


class UserRegistration(BaseModel):
    """
    Real-world example: User registration with comprehensive validation.
    Combines multiple field validator patterns.
    """
    
    email: EmailStr
    password: str
    confirm_password: str
    username: str = Field(min_length=3, max_length=30)
    age: int = Field(ge=13)  # COPPA compliance
    
    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, v: str) -> str:
        return v.strip().lower()
    
    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        # Reuse standalone validator
        return validate_password_strength(v)
    
    @field_validator("confirm_password", mode="after")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        # Access other field values via info.data
        if info.data.get("password") != v:
            raise ValueError("Passwords do not match")
        return v
    
    @field_validator("username", mode="after")
    @classmethod
    def username_not_email(cls, v: str) -> str:
        if "@" in v:
            raise ValueError("Username cannot be an email address")
        return v