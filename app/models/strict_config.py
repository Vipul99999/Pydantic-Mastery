"""
Demonstrates ConfigDict and strict validation in Pydantic v2.

Key concepts covered:
- ConfigDict for model configuration (replaces class Config)
- strict=True: No type coercion (123 != "123")
- extra="forbid"|"allow"|"ignore": Control unknown fields
- validate_assignment=True: Validate on attribute setting
- populate_by_name=True: Allow alias or field name for input
- from_attributes=True: ORM mode for SQLAlchemy/Django
- frozen=True: Immutable models
- alias_generator: Auto-generate field aliases (camelCase ↔ snake_case)

Real-world use cases:
- API input validation: strict mode prevents silent bugs
- Data import: extra="forbid" catches typos in CSV headers
- ORM integration: from_attributes=True for SQLAlchemy models
- Frontend sync: alias_generator for JavaScript camelCase
- Config files: frozen=True prevents accidental mutation

🎓 INTERACTIVE LEARNING READY:
- Toggle strict mode to see coercion differences
- Try adding unknown fields with extra="forbid" vs extra="allow"
- Demonstrate alias conversion: snake_case ↔ camelCase
- Show frozen model error when trying to modify
- Visualize validate_assignment catching invalid updates
"""

from pydantic import BaseModel, Field, ConfigDict, ValidationError, PrivateAttr
from pydantic.alias_generators import to_camel, to_snake
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import StrEnum


# === Strict Mode Demo ===

class StrictUser(BaseModel):
    """
    User model with strict validation.
    
    🎓 Learning Focus: Show difference between strict and lenient mode.
    
    Config:
    - strict=True: No automatic type coercion
    - extra="forbid": Reject unknown fields
    - validate_assignment=True: Validate when setting attributes
    """
    
    model_config = ConfigDict(
        strict=True,              # CRITICAL: No "123" → 123 coercion
        extra="forbid",           # Reject fields not in model
        validate_assignment=True, # Validate on user.age = "not-a-number"
        populate_by_name=True,    # Accept both "id" and "id" (if alias set)
    )
    
    id: int = Field(description="Unique user ID")
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    age: int = Field(ge=13, le=120)
    is_active: bool = Field(default=True)
    
    # 🎓 Interactive: Try these and see strict mode in action:
    # 1. {"id": "123"} → ERROR: str not allowed for int (strict=True)
    # 2. {"id": 123, "unknown_field": "x"} → ERROR: extra field forbidden
    # 3. After creation: user.age = "thirty" → ERROR: validate_assignment
    # 4. {"id": 123, "is_active": "true"} → ERROR: str not allowed for bool
    
    @property
    def display_name(self) -> str:
        return f"@{self.username}"


class LenientUser(BaseModel):
    """
    Same model with lenient (default) validation.
    
    🎓 Compare: See how lenient mode accepts more inputs.
    
    Config:
    - strict=False (default): Allows type coercion
    - extra="ignore" (default): Silently drops unknown fields
    """
    
    # No model_config = uses Pydantic defaults
    
    id: int
    username: str
    email: str
    age: int = Field(ge=13, le=120)
    is_active: bool = True
    
    # 🎓 Interactive: These work in lenient mode but fail in strict:
    # 1. {"id": "123"} → OK: coerces "123" to 123
    # 2. {"id": 123, "typo_field": "x"} → OK: ignores unknown field
    # 3. {"is_active": "true"} → OK: coerces "true" to True


# === Extra Fields Behavior Demo ===

class StrictExtraModel(BaseModel):
    """Reject any fields not explicitly defined."""
    model_config = ConfigDict(extra="forbid")
    
    name: str
    value: int


class AllowExtraModel(BaseModel):
    """Accept and store unknown fields in __pydantic_extra__."""
    model_config = ConfigDict(extra="allow")
    
    name: str
    value: int
    
    def get_extra_fields(self) -> Dict[str, Any]:
        """Access extra fields that were allowed."""
        return self.__pydantic_extra__ or {}


class IgnoreExtraModel(BaseModel):
    """Silently ignore unknown fields (default behavior)."""
    model_config = ConfigDict(extra="ignore")
    
    name: str
    value: int


# === Alias Generator Demo ===

class CamelCaseModel(BaseModel):
    """
    Model with automatic camelCase ↔ snake_case conversion.
    
    🎓 Learning Focus: Show how alias_generator bridges Python/JS naming.
    
    Config:
    - alias_generator=to_camel: Output uses camelCase
    - populate_by_name=True: Input accepts both snake_case and camelCase
    """
    
    model_config = ConfigDict(
        alias_generator=to_camel,      # snake_case → camelCase for output
        populate_by_name=True,          # Accept both naming styles for input
        str_strip_whitespace=True,      # Auto-trim all string fields
    )
    
    user_id: int = Field(description="Unique identifier")
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email_address: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    is_premium_user: bool = Field(default=False)
    
    # 🎓 Interactive: 
    # Input: {"userId": 123, "firstName": "Alice"} → OK (populate_by_name)
    # Output: {"userId": 123, "firstName": "Alice", ...} (alias_generator)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class SnakeCaseModel(BaseModel):
    """
    Model that prefers snake_case but accepts camelCase input.
    
    Config:
    - alias_generator=to_snake: camelCase input → snake_case fields
    - populate_by_name=True: Also accept snake_case input
    """
    
    model_config = ConfigDict(
        alias_generator=to_snake,
        populate_by_name=True,
    )
    
    userId: int  # Field name is camelCase (unusual but demo purposes)
    firstName: str
    lastName: str
    
    # 🎓 Interactive:
    # Input: {"user_id": 123} or {"userId": 123} → both work
    # Output: {"user_id": 123, ...} (converted to snake_case)


# === Frozen (Immutable) Model Demo ===

class FrozenConfig(BaseModel):
    """
    Immutable model: fields cannot be changed after creation.
    
    🎓 Learning Focus: Demonstrate data integrity patterns.
    
    Config:
    - frozen=True: All fields are read-only after __init__
    """
    
    model_config = ConfigDict(frozen=True)
    
    config_id: str
    version: str
    settings: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 🎓 Interactive:
    # After creation: config.version = "2.0" → ERROR: Instance is frozen
    
    def create_new_version(self, new_settings: Dict[str, Any]) -> "FrozenConfig":
        """
        Create updated copy instead of mutating.
        
        🎓 Pattern: Immutable objects return new instances for changes.
        """
        return self.model_copy(
            update={
                "version": f"{self.version}.1",
                "settings": {**self.settings, **new_settings},
                "created_at": datetime.utcnow()
            }
        )


# === ORM Mode Demo (from_attributes) ===

# Simulated database record (like SQLAlchemy model)
class DatabaseRecord:
    """Mock ORM model for demonstration."""
    def __init__(self, id: int, username: str, email: str, created: datetime):
        self.id = id
        self.username = username
        self.email = email
        self.created_at = created  # Note: attribute name differs from Pydantic field
        self._private = "internal"  # Should be ignored


class ORMUser(BaseModel):
    """
    Pydantic model that reads from ORM objects.
    
    🎓 Learning Focus: Show integration with SQLAlchemy/Django.
    
    Config:
    - from_attributes=True: Allow model_validate(orm_obj)
    """
    
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        extra="ignore",         # Ignore ORM private attributes
    )
    
    id: int
    username: str
    email: str
    created_at: datetime  # Matches DatabaseRecord.created_at
    
    # 🎓 Interactive:
    # db_record = DatabaseRecord(1, "alice", "a@b.com", datetime.now())
    # user = ORMUser.model_validate(db_record)  # Works with from_attributes=True
    # user.model_dump() → {"id": 1, "username": "alice", ...}


# === Validate Assignment Demo ===

class ValidatedAssignmentModel(BaseModel):
    """
    Model that validates on every attribute assignment.
    
    🎓 Learning Focus: Catch invalid updates at runtime.
    
    Config:
    - validate_assignment=True: Run validators when setting fields
    """
    
    model_config = ConfigDict(validate_assignment=True)
    
    score: float = Field(ge=0.0, le=100.0)
    status: str = Field(pattern="^(active|inactive|pending)$")
    
    # 🎓 Interactive:
    # obj = ValidatedAssignmentModel(score=95.0, status="active")
    # obj.score = 150.0 → ERROR: validation fails (ge=0, le=100)
    # obj.status = "deleted" → ERROR: pattern mismatch
    
    @property
    def is_passing(self) -> bool:
        return self.score >= 70.0


# === Combined Config Demo ===

class ProductionConfigModel(BaseModel):
    """
    Production-ready model combining multiple config options.
    
    🎓 Learning Focus: Show best-practice configuration for APIs.
    """
    
    model_config = ConfigDict(
        # Validation
        strict=True,                    # Prevent silent coercion bugs
        extra="forbid",                 # Catch API typos early
        validate_assignment=True,       # Catch invalid updates
        
        # Serialization
        populate_by_name=True,          # Accept both alias and name
        str_strip_whitespace=True,      # Clean user input
        
        # Integration
        from_attributes=True,           # Support ORM loading
        # frozen=False,                 # Allow updates (set True for config objects)
        
        # Aliases for frontend
        alias_generator=to_camel,       # Output camelCase for JavaScript
    )
    
    # Fields with aliases (alias_generator creates camelCase output)
    user_id: int = Field(description="Unique user identifier")
    email_address: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    account_status: str = Field(pattern="^(active|suspended|deleted)$")
    created_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Private attribute (not serialized, not validated)
    _internal_cache: Optional[Dict] = PrivateAttr(default=None)
    
    # 🎓 Interactive Demo Scenarios:
    # 1. Input coercion: {"user_id": "123"} → ERROR (strict=True)
    # 2. Unknown field: {"user_id": 123, "typo": "x"} → ERROR (extra="forbid")
    # 3. Alias input: {"userId": 123} → OK (populate_by_name=True)
    # 4. Output alias: model_dump() → {"userId": 123, ...} (alias_generator)
    # 5. Runtime update: obj.account_status = "invalid" → ERROR (validate_assignment)
    # 6. ORM load: model_validate(db_record) → OK (from_attributes=True)
    
    def to_api_response(self) -> Dict[str, Any]:
        """Serialize for public API (camelCase, no internals)."""
        return self.model_dump(
            mode="json",
            by_alias=True,      # Use camelCase aliases
            exclude_private=True,  # Exclude PrivateAttr fields
            exclude_none=True,
        )
    
    def to_internal_dict(self) -> Dict[str, Any]:
        """Serialize for internal use (snake_case, all fields)."""
        return self.model_dump(
            mode="python",
            by_alias=False,     # Use Python field names
            exclude_private=False,
        )


# === Config Comparison Helper for Playground ===

class ConfigComparison:
    """
    Helper to demonstrate config differences interactively.
    
    🎓 Playground: Let users toggle config options and see behavior change.
    """
    
    @staticmethod
    def compare_strict_vs_lenient(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate same data with strict and lenient configs.
        
        🎓 Interactive: Side-by-side comparison of validation behavior.
        """
        results = {}
        
        # Strict validation
        try:
            strict_user = StrictUser.model_validate(data)
            results["strict"] = {
                "valid": True,
                "data": strict_user.model_dump(mode="json"),
            }
        except ValidationError as e:
            results["strict"] = {
                "valid": False,
                "errors": e.errors(include_url=False, include_input=False),
            }
        
        # Lenient validation
        try:
            lenient_user = LenientUser.model_validate(data)
            results["lenient"] = {
                "valid": True,
                "data": lenient_user.model_dump(mode="json"),
            }
        except ValidationError as e:
            results["lenient"] = {
                "valid": False,
                "errors": e.errors(include_url=False, include_input=False),
            }
        
        return {
            "input": data,
            "comparison": results,
            "key_differences": [
                "strict=True: No type coercion (\"123\" ≠ 123)",
                "extra=\"forbid\": Unknown fields cause errors",
                "validate_assignment: Runtime updates are validated",
            ]
        }
    
    @staticmethod
    def demonstrate_alias_conversion(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show how alias_generator transforms field names.
        
        🎓 Interactive: Input snake_case, see camelCase output.
        """
        try:
            model = CamelCaseModel.model_validate(data)
            return {
                "input": data,
                "python_names": model.model_dump(by_alias=False),
                "api_names": model.model_dump(by_alias=True),
                "note": "populate_by_name=True allows both input styles",
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": e.errors(include_url=False),
            }