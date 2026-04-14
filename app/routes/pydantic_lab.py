"""
🎓 Pydantic Mastery Lab - Interactive Learning API Routes

This module provides comprehensive FastAPI endpoints demonstrating ALL Pydantic v2 features.
Designed for:
✅ Recruiter code review (shows depth of Pydantic expertise)
✅ Interactive learning platform foundation  
✅ Auto-generated OpenAPI documentation (/docs)
✅ Frontend playground integration (schema export, live validation)

📚 Feature Categories:
1. 🧱 Basics: BaseModel, Field, defaults, constraints
2. 🔍 Field Validators: @field_validator (before/after/wrap)
3. 🔗 Model Validators: @model_validator (cross-field logic)
4. 🧮 Computed Fields: @computed_field for derived values
5. 🔧 TypeAdapter: Runtime/dynamic validation
6. ⚙️ Strict Config: ConfigDict, strict mode, aliases, frozen
7. 🔣 Enums & Custom Types: StrEnum, EmailStr, SecretStr, HttpUrl
8. 🔄 Serialization: model_dump modes, field_serializer
9. 📐 Annotated: Composable constraints with Annotated[T, ...]
10. 🌳 Nested & Generics: Recursive models, Generic[T] responses
11. 🎭 Discriminated Unions: Field(discriminator=...) auto-routing

🎮 Interactive Learning Features:
- /playground/validate: Universal validator with any model + payload
- /playground/schema/{model}: JSON Schema for frontend form generation
- /playground/examples/{model}: Pre-filled example payloads
- /playground/errors: Structured error format for UI highlighting
- /playground/compare: Side-by-side validation (strict vs lenient)

🚀 Quick Start:
    uvicorn app.main:app --reload
    open http://localhost:8000/docs
"""

from fastapi import APIRouter, Query, HTTPException, status, Body, Path
from fastapi.responses import JSONResponse
from pydantic import ValidationError, TypeAdapter, BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Annotated
from datetime import datetime, timezone
from pathlib import Path as FilePath
import json
import re

# Core config & exceptions
from app.core.config import settings
from app.core.exceptions import format_validation_error

# All model imports for comprehensive demo
from app.models.basics import (
    UserBasic, AddressBasic, UserWithAddress, 
    ConstraintExamples, MethodsDemo, BasicsPlayground
)
from app.models.field_validators import FieldValidatorDemo, UserRegistration
from app.models.model_validators import ModelValidatorDemo, OrderValidation, OrderItem
from app.models.computed import (
    UserProfileComputed, OrderWithComputed, PlaygroundComputed
)
from app.models.type_adapters import (
    TypeAdapterDemo, BatchValidator, PlaygroundAdapter, 
    EmailListAdapter, TagListAdapter
)
from app.models.strict_config import (
    StrictUser, LenientUser, CamelCaseModel, FrozenConfig,
    ORMUser, ConfigComparison
)
from app.models.enum_custom import (
    UserWithEnums, CustomTypesDemo, PaymentProfile as EnumPaymentProfile,
    UserRole, AccountStatus, Theme, EnumPlayground
)

from app.models.serialization import SerializationDemo, UserWithAddress as SerialUser
from app.models.annotated_advanced import (
    AnnotatedAdvancedDemo, Product, PaginatedList, ContextConstrained
)
from app.models.nested_generics import (
    UserProfile, Comment, PaginatedResponse, 
    Department, Employee, UserNotificationPreferences
)
from app.models.discriminated_unions import (
    PaymentProfile as UnionPaymentProfile, PaymentMethod,
    WebhookReceiver, SearchQuery, DomainEvent
)

# NOTE: Services layer is optional - removed unused import since you only have __init__.py
# from app.services.json_db import JSONDatabase

# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(
    prefix="/lab", 
    tags=["🎓 Pydantic Mastery Lab"],
    responses={
        404: {"description": "Feature not found"},
        422: {"description": "Validation error - check field errors"}
    }
)

# NOTE: Database service is optional - using in-memory data for demo
# user_db = JSONDatabase(UserBasic, settings.database.data_path)

# Model registry for dynamic endpoints - maps string keys to model classes
# Used by /playground/validate for runtime model selection
MODEL_REGISTRY = {
    # === 🧱 Basics ===
    "basics.user": UserBasic,
    "basics.address": AddressBasic,
    "basics.constraints": ConstraintExamples,
    "basics.methods": MethodsDemo,
    
    # === 🔍 Field Validators ===
    "validators.field": FieldValidatorDemo,
    "validators.registration": UserRegistration,
    
    # === 🔗 Model Validators ===
    "validators.model": ModelValidatorDemo,
    "validators.order": OrderValidation,
    
    # === 🧮 Computed Fields ===
    "computed.profile": UserProfileComputed,
    "computed.order": OrderWithComputed,
    "computed.playground": PlaygroundComputed,
    
    # === 🔧 TypeAdapter ===
    "adapter.demo": TypeAdapterDemo,
    "adapter.batch": BatchValidator,
    
    # === ⚙️ Strict Config ===
    "config.strict": StrictUser,
    "config.lenient": LenientUser,
    "config.camel": CamelCaseModel,
    "config.frozen": FrozenConfig,
    
    # === 🔣 Enums & Custom Types ===
    "enums.user": UserWithEnums,
    "enums.custom_types": CustomTypesDemo,
    "enums.payment": EnumPaymentProfile,
    
    # === 🔄 Serialization ===
    "serialize.demo": SerializationDemo,
    
    # === 📐 Annotated ===
    "annotated.demo": AnnotatedAdvancedDemo,
    "annotated.product": Product,
    "annotated.paginated": PaginatedList,
    
    # === 🌳 Nested & Generics ===
    "nested.user": UserProfile,
    "nested.comment": Comment,
    "nested.department": Department,
    
    # === 🎭 Discriminated Unions ===
    "union.payment": UnionPaymentProfile,
    "union.webhook": WebhookReceiver,
    "union.search": SearchQuery,
}

# TypeAdapter registry for primitive types - enables dynamic validation without models
TYPE_ADAPTER_REGISTRY = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "List[int]": List[int],
    "List[str]": List[str],
    "Dict[str, str]": Dict[str, str],
    "Email": Annotated[str, Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")],
}


# =============================================================================
# 🏠 Home & Documentation Endpoints
# =============================================================================

@router.get("/", summary="🎓 Pydantic Mastery Lab Home", response_class=JSONResponse)
def lab_home():
    """
    Welcome endpoint with feature catalog and quick links.
    
    🎓 Perfect for: Interactive learning navigation, recruiter tour.
    
    Returns a structured overview of:
    - Quick links to docs and playground
    - Feature categories with endpoint mappings
    - Interactive features for frontend integration
    - Recruiter highlights for code review
    """
    return {
        "title": "🎓 Pydantic v2 Mastery Lab",
        "version": "2.0.0",
        "description": "Interactive API demonstrating ALL Pydantic v2 features with real-world patterns.",
        "quick_links": {
            "interactive_docs": "/docs",
            "feature_catalog": "/lab/features",
            "playground": "/lab/playground/validate",
            "schema_export": "/lab/playground/schema/{model}",
            "health": "/lab/health"
        },
        "feature_categories": [
            {"id": "basics", "name": "🧱 Basics", "endpoint": "/lab/basics/user", "models": 4},
            {"id": "validators", "name": "🔍 Validators", "endpoint": "/lab/validators/field", "models": 4},
            {"id": "computed", "name": "🧮 Computed Fields", "endpoint": "/lab/computed/profile", "models": 3},
            {"id": "adapter", "name": "🔧 TypeAdapter", "endpoint": "/lab/adapter/demo", "models": 2},
            {"id": "config", "name": "⚙️ Strict Config", "endpoint": "/lab/config/strict", "models": 4},
            {"id": "enums", "name": "🔣 Enums & Types", "endpoint": "/lab/enums/user", "models": 3},
            {"id": "serialize", "name": "🔄 Serialization", "endpoint": "/lab/serialize/demo", "models": 1},
            {"id": "annotated", "name": "📐 Annotated", "endpoint": "/lab/annotated/demo", "models": 3},
            {"id": "nested", "name": "🌳 Nested Models", "endpoint": "/lab/nested/user", "models": 3},
            {"id": "unions", "name": "🎭 Discriminated Unions", "endpoint": "/lab/union/payment", "models": 3},
        ],
        "interactive_features": [
            "Live validation with immediate feedback",
            "Schema export for frontend form generation",
            "Example payloads with 'try it' buttons",
            "Side-by-side config comparison (strict vs lenient)",
            "Structured errors for UI field highlighting",
        ],
        "recruiter_highlights": [
            "Production-ready error handling with field-specific messages",
            "Type-safe API contracts with auto-generated OpenAPI docs", 
            "Composable validation patterns that scale with codebase",
            "Clear separation: models, routes, services, config",
            "Extensive inline documentation for knowledge transfer",
        ]
    }


@router.get("/features", summary="📚 Complete Feature Catalog")
def feature_catalog():
    """
    Return detailed catalog of all Pydantic features with examples.
    
    🎓 Use: Interactive learning navigation, recruiter code tour.
    
    Each category includes:
    - Description of the Pydantic concept
    - Example endpoints with test cases
    - Learning points for understanding the pattern
    """
    return {
        "categories": [
            {
                "id": "basics",
                "name": "🧱 BaseModel & Field Fundamentals",
                "description": "Core Pydantic patterns: constraints, defaults, metadata",
                "endpoints": [
                    {
                        "path": "POST /lab/basics/user",
                        "model": "UserBasic",
                        "description": "Validate user with Field constraints",
                        "examples": [
                            {"username": "alice_dev", "email": "alice@example.com", "id": 1},
                            {"username": "ab", "email": "invalid"}  # Triggers validation errors
                        ],
                        "learning_points": [
                            "Field(..., min_length, pattern) for constraints",
                            "Optional[T] vs T = None for optional fields",
                            "Field examples for OpenAPI docs",
                            "model_dump() modes: python vs json"
                        ]
                    },
                    {
                        "path": "POST /lab/basics/constraints",
                        "model": "ConstraintExamples", 
                        "description": "Test all Field constraint types",
                        "examples": [
                            {"short_text": "Hi", "positive_int": 42, "percentage": 85.5},
                            {"short_text": "", "positive_int": -1}  # Triggers errors
                        ],
                        "constraint_types": [
                            "String: min_length, max_length, pattern",
                            "Numeric: gt, ge, lt, le, multiple_of",
                            "Float: decimal_places",
                            "List: min_length, max_length, unique_items"
                        ]
                    }
                ]
            },
            {
                "id": "validators",
                "name": "🔍 Field & Model Validators",
                "description": "Custom validation logic with @field_validator and @model_validator",
                "endpoints": [
                    {
                        "path": "POST /lab/validators/field",
                        "model": "FieldValidatorDemo",
                        "description": "Test @field_validator modes: before/after/wrap",
                        "validator_modes": {
                            "before": "Transform raw input BEFORE type coercion (email normalization)",
                            "after": "Validate/clean AFTER field is parsed (tag deduplication)", 
                            "wrap": "Full control over validation pipeline (age business rules)"
                        },
                        "test_cases": [
                            "Email: '  TEST@Example.COM  ' → 'test@example.com'",
                            "Tags: ['Py', 'py', 'PY'] → ['py'] (deduplicated)",
                            "Age: -5 → error, 17 → ok, 125 → warning"
                        ]
                    },
                    {
                        "path": "POST /lab/validators/model",
                        "model": "ModelValidatorDemo",
                        "description": "Cross-field validation with @model_validator",
                        "business_rules": [
                            "Passwords must match",
                            "Premium flag aligns with subscription tier",
                            "Postal code format matches country",
                            "Order totals calculated from items"
                        ]
                    }
                ]
            },
            {
                "id": "computed",
                "name": "🧮 Computed Fields",
                "description": "Derived values with @computed_field",
                "endpoints": [
                    {
                        "path": "POST /lab/computed/profile",
                        "model": "UserProfileComputed",
                        "description": "User profile with auto-calculated fields",
                        "computed_fields": [
                            "full_name: first_name + last_name",
                            "age: calculated from date_of_birth",
                            "account_age_days: since creation timestamp",
                            "display_role: based on is_premium flag",
                            "profile_url: generated from username slug"
                        ],
                        "interactive_demo": "Change input fields → see computed values update instantly"
                    }
                ]
            },
            {
                "id": "adapter",
                "name": "🔧 TypeAdapter for Dynamic Validation",
                "description": "Validate arbitrary types at runtime without model definition",
                "endpoints": [
                    {
                        "path": "POST /lab/adapter/validate",
                        "description": "Validate any JSON against any registered type",
                        "supported_types": list(TYPE_ADAPTER_REGISTRY.keys()),
                        "use_cases": [
                            "Webhook payload validation",
                            "Configuration file validation",
                            "Plugin system config validation",
                            "Data pipeline batch validation"
                        ],
                        "methods": {
                            "validate_python": "Validate Python object",
                            "validate_json": "Parse AND validate JSON string in one step",
                            "dump_python/json": "Serialize with type control"
                        }
                    }
                ]
            },
            {
                "id": "config",
                "name": "⚙️ ConfigDict & Strict Validation",
                "description": "Model configuration for production-grade validation",
                "endpoints": [
                    {
                        "path": "POST /lab/config/compare",
                        "description": "Side-by-side: strict vs lenient validation",
                        "config_options": {
                            "strict": "No type coercion: '123' ≠ 123",
                            "extra": "forbid/allow/ignore unknown fields",
                            "validate_assignment": "Validate on attribute setting",
                            "alias_generator": "Auto camelCase ↔ snake_case",
                            "frozen": "Immutable models",
                            "from_attributes": "ORM mode for SQLAlchemy"
                        },
                        "interactive": "Toggle config options → see behavior change in real-time"
                    }
                ]
            },
            {
                "id": "enums",
                "name": "🔣 Enums & Custom Types",
                "description": "StrEnum, EmailStr, SecretStr, HttpUrl, and more",
                "endpoints": [
                    {
                        "path": "POST /lab/enums/user",
                        "model": "UserWithEnums",
                        "description": "User model with validated enum fields",
                        "enum_fields": {
                            "role": "UserRole: admin/moderator/user/guest",
                            "status": "AccountStatus: active/pending/suspended",
                            "theme": "Theme: light/dark/auto",
                            "notification_freq": "Frequency: immediate/daily/weekly"
                        },
                        "custom_types": {
                            "EmailStr": "RFC-compliant email validation",
                            "SecretStr": "Auto-masking for sensitive values",
                            "HttpUrl": "Valid URL with scheme/TLD check",
                            "FilePath/DirectoryPath": "Filesystem path validation"
                        }
                    }
                ]
            }
        ],
        "playground_endpoints": {
            "/lab/playground/validate": "Universal validator: any model + any payload",
            "/lab/playground/schema/{model}": "Export JSON Schema for frontend forms",
            "/lab/playground/examples/{model}": "Get pre-filled example payloads",
            "/lab/playground/compare": "Compare validation behaviors side-by-side"
        }
    }


# =============================================================================
# 🧱 BASICS ENDPOINTS
# =============================================================================

@router.post(
    "/basics/user",
    response_model=UserBasic,
    summary="🧱 Validate Basic User Model",
    description=r"""
    **Model**: UserBasic
    
    **Features Demonstrated**:
    - Field constraints: min_length, max_length, pattern
    - Optional fields with defaults
    - Nested dict field (address)
    - DateTime with default_factory
    - Field metadata: description, examples for OpenAPI
    
    **Try These Test Cases**:
    1. ✅ Valid: `{"id": 1, "username": "alice_dev", "email": "alice@example.com"}`
    2. ❌ Invalid username: `{"username": "ab"}` → min_length error
    3. ❌ Invalid email: `{"email": "not-an-email"}` → pattern error
    4. ❌ Invalid role: `{"role": "superuser"}` → pattern error
    
    **Learning Points**:
    - Field(...) = required field
    - Optional[str] = can be None
    - pattern uses Python re module regex
    - examples appear in /docs for "try it" buttons
    """
)
def validate_basic_user(payload: UserBasic = Body(..., examples=[{
    "id": 1,
    "username": "alice_dev", 
    "email": "alice@example.com",
    "role": "admin",
    "api_key": "sk_test_1234567890abcdef",
    "is_active": True,
    "address": {"street": "123 Code Ave", "city": "Techville", "country": "US"},
    "created_at": "2025-01-15T10:30:00Z"
}])):
    """
    Validate and return user with all constraints applied.
    
    🎓 Interactive: Change fields → see validation errors instantly.
    """
    return payload


@router.post(
    "/basics/constraints",
    response_model=ConstraintExamples,
    summary="🧱 Test All Field Constraint Types",
    description=r"""
    **Model**: ConstraintExamples
    
    **Constraint Types Covered**:
    - String: min_length, max_length, pattern
    - Integer: gt, ge, lt, le, multiple_of  
    - Float: ge, le, decimal_places
    - List: min_length, max_length, unique_items
    - Optional with default_factory
    
    **Try These**:
    1. ✅ `{"short_text": "Hello", "positive_int": 42, "percentage": 85.5}`
    2. ❌ `{"short_text": "", "positive_int": -1}` → multiple errors
    3. ❌ `{"pattern_text": "hello"}` → pattern requires capital first letter
    4. ❌ `{"unique_ids": [1, 2, 2]}` → duplicate not allowed
    
    **Pro Tip**: Each constraint generates specific error messages for frontend highlighting.
    """
)
def test_constraints(payload: ConstraintExamples):
    """Validate payload with comprehensive field constraints."""
    return payload


@router.post(
    "/basics/methods",
    summary="🧱 Demonstrate Model Methods",
    description="""
    **Model**: MethodsDemo
    
    **Methods Demonstrated**:
    - model_validate(): Create from dict
    - model_dump(mode="python"|"json"): Serialize with type control
    - model_copy(update={...}): Immutable update pattern
    - Legacy dict() method (v1 compatibility)
    
    **Interactive Demo**:
    1. POST with payload → get validated instance
    2. Call to_dict_json() → see datetime as ISO string
    3. Call with_updated_score(99.0) → get new instance with changed score
    4. Compare python vs json mode outputs
    
    **Learning**: Understand when to use each serialization mode.
    """
)
def demo_model_methods(
    payload: MethodsDemo,
    mode: str = Query("json", pattern="^(python|json)$", description="Serialization mode")
):
    """
    Demonstrate model serialization methods.
    
    Query param `mode` controls output format.
    """
    if mode == "python":
        return payload.to_dict_python()
    return payload.to_dict_json()


# =============================================================================
# 🔍 VALIDATORS ENDPOINTS  
# =============================================================================

@router.post(
    "/validators/field",
    response_model=FieldValidatorDemo,
    summary="🔍 Test @field_validator Patterns",
    description=r"""
    **Model**: FieldValidatorDemo
    
    **Validator Modes Demonstrated**:
    
    🔹 mode="before" (email):
    - Runs BEFORE type coercion
    - Use for: Normalization, pre-processing
    - Example: "  TEST@Example.COM  " → "test@example.com"
    
    🔹 mode="after" (tags):  
    - Runs AFTER field is parsed
    - Use for: Business rules, cross-value logic
    - Example: ["Py", "py", "PY"] → ["py"] (deduplicated)
    
    🔹 mode="wrap" (age):
    - Full control: pre-check → handler → post-check
    - Use for: Complex validation pipelines
    - Example: Age < 0 → error, 17 → ok, 125 → warning
    
    **Test Cases**:
    1. Email normalization: `"  Alice@Example.COM  "` → `"alice@example.com"`
    2. Tag dedup: `["python", "Python", "PYTHON", "fastapi"]` → `["python", "fastapi"]`
    3. Age edge: `-5` → error, `17` → ok, `125` → warning logged
    4. Reserved username: `"admin"` → error
    
    **🎓 Interactive**: Paste raw input → see transformed output instantly.
    """
)
def demo_field_validators(payload: FieldValidatorDemo):
    """
    Validate with field validators and return processed result.
    
    Shows normalization, deduplication, and business rule enforcement.
    """
    return payload


@router.post(
    "/validators/model",
    response_model=ModelValidatorDemo,
    summary="🔍 Test @model_validator Cross-Field Logic",
    description=r"""
    **Model**: ModelValidatorDemo
    
    **Model Validator Modes**:
    
    🔹 mode="before":
    - Receives raw dict before model creation
    - Use for: Field mapping, input normalization
    - Example: {"email_address": "x@y.com"} → {"email": "x@y.com"}
    
    🔹 mode="after":
    - Receives fully validated model instance
    - Use for: Cross-field business rules
    - Examples: 
      * Passwords must match
      * Premium flag aligns with subscription tier
      * Postal code format matches country
    
    **Business Rules Enforced**:
    1. password == confirm_password
    2. subscription="free" → is_premium must be False
    3. subscription!="free" → is_premium auto-set to True
    4. US postal code: must match ^\\d{5}(-\\d{4})?$
    
    **Test Cases**:
    1. ✅ `{"password": "secure123", "confirm_password": "secure123"}` → OK
    2. ❌ `{"password": "a", "confirm_password": "b"}` → "Passwords do not match"
    3. ❌ `{"subscription": "free", "is_premium": true}` → "Free tier cannot be premium"
    4. ❌ `{"country": "US", "postal_code": "123"}` → "US postal code must be 5 digits"
    
    **🎓 Learning**: Cross-field validation ensures data consistency.
    """
)
def demo_model_validators(payload: ModelValidatorDemo):
    """Validate with cross-field business rules."""
    return payload


@router.post(
    "/validators/order",
    response_model=OrderValidation,
    summary="🔍 Complex Order Validation",
    description="""
    **Model**: OrderValidation (with nested OrderItem)
    
    **Advanced Validation Patterns**:
    
    🔸 Auto-calculation:
    - Missing subtotal → calculated from items
    - Total verified: subtotal - discount + shipping
    
    🔸 Financial rules:
    - Discount cannot exceed subtotal
    - Max 50% discount for non-enterprise
    
    🔸 Shipping logic:
    - Method availability by country
    - Restricted methods demo: no overnight to CA
    
    **Test Cases**:
    1. ✅ Valid order with items → auto-calculates totals
    2. ❌ Wrong total → error with expected value
    3. ❌ Discount > subtotal → "Discount cannot exceed subtotal"  
    4. ❌ Overnight to CA → "Shipping method not available"
    
    **🎓 Real-World**: E-commerce order validation pattern.
    """
)
def validate_order(payload: OrderValidation):
    """Validate complex order with financial and shipping rules."""
    return payload


# =============================================================================
# 🧮 COMPUTED FIELDS ENDPOINTS
# =============================================================================

@router.post(
    "/computed/profile",
    summary="🧮 User Profile with Computed Fields",
    description="""
    **Model**: UserProfileComputed
    
    **Computed Fields Demonstrated**:
    
    🔹 full_name: `first_name + last_name`
    🔹 age: Calculated from date_of_birth (with birthday adjustment)
    🔹 account_age_days: Days since account_created
    🔹 display_role: "Premium Member" if is_premium else "Free User"
    🔹 email_domain: Extracted from email address
    🔹 profile_url: Generated from username (slugified)
    🔹 premium_badge: "✨ Premium" or None (conditional)
    🔹 account_status: "new"/"active"/"inactive" based on rules
    
    **Interactive Demo**:
    1. Change first_name/last_name → see full_name update
    2. Change date_of_birth → see age recalculate
    3. Toggle is_premium → see display_role and premium_badge change
    4. Change email → see email_domain extract automatically
    
    **Serialization Control**:
    - to_minimal_response(): exclude_computed=True
    - to_full_response(): include all computed fields
    
    **🎓 Learning**: Computed fields auto-update when source fields change.
    """
)
def demo_computed_profile(payload: UserProfileComputed):
    """Return profile with all computed fields evaluated."""
    return payload.model_dump(mode="json", exclude_none=False)


@router.post(
    "/computed/order",
    summary="🧮 Order with Computed Pricing",
    description="""
    **Model**: OrderWithComputed (with nested OrderItem)
    
    **Computed Pricing Fields**:
    
    🔹 subtotal: Σ(item.price × item.quantity)
    🔹 discount_amount: subtotal × discount_percent
    🔹 taxable_amount: max(0, subtotal - discount)
    🔹 tax_amount: taxable_amount × tax_rate
    🔹 total: taxable + tax + shipping
    🔹 item_count: Σ(item.quantity)
    🔹 savings_message: "You saved $X!" if discount applied
    
    **Interactive Pricing Demo**:
    1. Add items → see subtotal auto-calculate
    2. Change discount_percent → see discount_amount and total update
    3. Adjust tax_rate → see tax_amount recalculate
    4. View to_receipt() → formatted pricing breakdown
    
    **🎓 Real-World**: E-commerce cart pricing pattern.
    """
)
def demo_computed_order(payload: OrderWithComputed):
    """Return order with computed pricing fields."""
    return payload.to_receipt()


@router.post(
    "/computed/playground",
    summary="🧮 Simple Computed Fields Playground",
    description="""
    **Model**: PlaygroundComputed (Beginner-Friendly)
    
    **Designed for Interactive Learning**:
    
    🔹 Inputs: first_name, last_name, birth_year (simple types)
    🔹 Outputs: 
      - full_name: "Alice Smith"
      - age_estimate: 2025 - birth_year  
      - greeting: "Hello, Alice Smith! You're ~35 years old."
    
    **PlaygroundConfig Metadata**:
    - Frontend can read via model_json_schema()
    - Auto-generates form inputs with labels/placeholders
    - Highlights computed outputs with icons
    
    **Perfect For**: 
    - First-time Pydantic learners
    - Live preview demos
    - "Change input → see output" interactions
    
    **🎓 Try It**: Type names and birth year → see greeting update instantly.
    """
)
def demo_playground_computed(payload: PlaygroundComputed):
    """Return computed values for beginner playground."""
    return {
        "inputs": payload.model_dump(include={"first_name", "last_name", "birth_year"}),
        "computed": {
            "full_name": payload.full_name,
            "age_estimate": payload.age_estimate,
            "greeting": payload.greeting,
        },
        "playground_meta": PlaygroundComputed.PlaygroundConfig.__dict__ if hasattr(PlaygroundComputed, 'PlaygroundConfig') else {}
    }


# =============================================================================
# 🔧 TYPEADAPTER ENDPOINTS
# =============================================================================

@router.post(
    "/adapter/validate",
    summary="🔧 Dynamic Validation with TypeAdapter",
    description="""
    **Feature**: TypeAdapter for runtime validation
    
    **Use Cases**:
    - Webhook payload validation (arbitrary JSON)
    - Configuration file validation
    - Plugin system config validation
    - Data pipeline batch validation
    
    **Query Params**:
    - `type`: Target type from registry:
      * Primitives: "int", "float", "str", "bool"
      * Collections: "List[int]", "List[str]", "Dict[str, str]"
      * Custom: "Email" (validated email string)
    
    **Body**: Arbitrary JSON to validate
    
    **Response Includes**:
    - valid: bool
    - validated: Parsed and validated value
    - serialized: JSON-compatible output
    - schema: JSON Schema for frontend form generation
    - errors: Detailed validation errors (if invalid)
    
    **Test Cases**:
    1. ✅ `{"data": [1, 2, 3], "type": "List[int]"}` → valid
    2. ❌ `{"data": ["a", "b"], "type": "List[int]"}` → type errors
    3. ✅ `{"data": "user@example.com", "type": "Email"}` → valid
    4. ❌ `{"data": "not-an-email", "type": "Email"}` → pattern error
    
    **🎓 Interactive**: Paste any JSON, select type → see validation result.
    """
)
def dynamic_validate(
    payload: Dict[str, Any] = Body(..., description="Data to validate"),
    type_name: str = Query(..., description="Target type name", examples=["List[int]", "Email"])
):
    """
    Validate arbitrary data against registered type using TypeAdapter.
    
    Perfect for webhook handlers, config validation, plugin systems.
    """
    target_type = TYPE_ADAPTER_REGISTRY.get(type_name)
    if not target_type:
        raise HTTPException(400, f"Unknown type: {type_name}. Available: {list(TYPE_ADAPTER_REGISTRY.keys())}")
    
    adapter = TypeAdapter(target_type)
    
    try:
        validated = adapter.validate_python(payload)
        return {
            "valid": True,
            "type": type_name,
            "input": payload,
            "validated": validated,
            "serialized": adapter.dump_python(validated, mode="json"),
            "schema": adapter.json_schema(),
        }
    except ValidationError as e:
        return {
            "valid": False,
            "type": type_name,
            "input": payload,
            "errors": e.errors(include_url=False, include_input=False),
            "error_count": e.error_count(),
            "schema": adapter.json_schema(),
            "tips": ["💡 Check the error messages above for details"],  # Fallback tips
        }


@router.post(
    "/adapter/batch",
    summary="🔧 Batch Validation with TypeAdapter",
    description="""
    **Feature**: BatchValidator for validating lists of models
    
    **Use Case**: CSV import, bulk API endpoint, data migration
    
    **Query Params**:
    - `model`: Target model name (e.g., "basics.user")
    
    **Body**: List of dicts to validate
    
    **Response Includes**:
    - Summary: total, valid, invalid, success_rate
    - Items: Per-item validation result with index
    - Errors: Detailed errors for invalid items
    
    **Test Cases**:
    1. ✅ Valid batch: All items pass → 100% success
    2. ⚠️ Mixed batch: Some valid, some invalid → detailed report
    3. ❌ Invalid batch: All fail → error summary
    
    **🎓 Interactive**: Paste array of objects → see which pass/fail and why.
    """
)
def batch_validate(
    items: List[Dict[str, Any]] = Body(..., description="List of items to validate"),
    model_name: str = Query(..., description="Target model name", examples=["basics.user"])
):
    """
    Validate batch of items against registered model.
    
    Returns detailed report for import wizard / bulk operations.
    """
    model_cls = MODEL_REGISTRY.get(model_name)
    if not model_cls:
        raise HTTPException(400, f"Unknown model: {model_name}")
    
    validator = BatchValidator(model_cls)
    return validator.validate_batch(items)


# =============================================================================
# ⚙️ STRICT CONFIG ENDPOINTS
# =============================================================================

@router.post(
    "/config/strict",
    response_model=StrictUser,
    summary="⚙️ Strict Mode Validation",
    description="""
    **Model**: StrictUser (ConfigDict with strict=True)
    
    **Strict Mode Behavior**:
    
    🔹 NO type coercion:
    - `{"id": "123"}` → ERROR (str not allowed for int)
    - `{"is_active": "true"}` → ERROR (str not allowed for bool)
    
    🔹 extra="forbid":
    - `{"id": 1, "typo_field": "x"}` → ERROR (unknown field)
    
    🔹 validate_assignment=True:
    - After creation: `user.age = "thirty"` → ERROR
    
    **Compare with Lenient Mode**:
    Use `/lab/config/compare` to see side-by-side behavior.
    
    **Test Cases**:
    1. ✅ `{"id": 123, "username": "alice", "email": "a@b.com", "age": 25}`
    2. ❌ `{"id": "123", ...}` → "Input should be a valid integer"
    3. ❌ `{"id": 123, "unknown": "x", ...}` → "Extra inputs are not permitted"
    4. ❌ After creation: `user.age = "old"` → "Input should be a valid integer"
    
    **🎓 Learning**: Strict mode prevents silent bugs from type coercion.
    """
)
def validate_strict_config(payload: StrictUser):
    """Validate with strict config: no coercion, forbid extras."""
    return payload


@router.post(
    "/config/compare",
    summary="⚙️ Compare Strict vs Lenient Validation",
    description="""
    **Feature**: Side-by-side validation comparison
    
    **Validates Same Payload With**:
    - StrictUser: strict=True, extra="forbid"
    - LenientUser: defaults (coercion allowed, extra ignored)
    
    **Response Shows**:
    ```json
    {
      "input": {...},
      "comparison": {
        "strict": {"valid": bool, "data/errors": ...},
        "lenient": {"valid": bool, "data/errors": ...}
      },
      "key_differences": [
        "strict=True: No type coercion",
        "extra=\"forbid\": Unknown fields cause errors",
        "validate_assignment: Runtime updates validated"
      ]
    }
    ```
    
    **Interactive Demo**:
    1. Paste payload with type mismatch: `{"id": "123"}`
    2. See: strict=ERROR, lenient=OK (coerced to int)
    3. Paste payload with unknown field: `{"typo": "x"}`
    4. See: strict=ERROR, lenient=OK (field ignored)
    
    **🎓 Learning**: Understand tradeoffs: strict=safety, lenient=flexibility.
    """
)
def compare_validation_configs(payload: Dict[str, Any] = Body(...)):
    """Compare same payload with strict vs lenient validation."""
    return ConfigComparison.compare_strict_vs_lenient(payload)


@router.post(
    "/config/alias",
    summary="⚙️ Alias Generator: camelCase ↔ snake_case",
    description="""
    **Model**: CamelCaseModel (alias_generator=to_camel)
    
    **Alias Behavior**:
    
    🔹 Input (populate_by_name=True):
    - Accepts BOTH: `{"user_id": 1}` OR `{"userId": 1}`
    
    🔹 Output (alias_generator=to_camel):
    - Always returns: `{"userId": 1, "firstName": "Alice", ...}`
    
    **Use Case**: Bridge Python (snake_case) ↔ JavaScript (camelCase)
    
    **Test Cases**:
    1. ✅ Input snake_case: `{"user_id": 1, "first_name": "Alice"}` → OK
    2. ✅ Input camelCase: `{"userId": 1, "firstName": "Alice"}` → OK (populate_by_name)
    3. ✅ Output: Always camelCase: `{"userId": 1, "firstName": "Alice", ...}`
    
    **🎓 Interactive**: Try both input styles → see consistent camelCase output.
    """
)
def demo_alias_conversion(payload: CamelCaseModel):
    """Demonstrate alias conversion for Python/JS interoperability."""
    return {
        "input_received": payload.model_dump(by_alias=False),  # Python names
        "api_response": payload.model_dump(by_alias=True),     # camelCase aliases
        "note": "populate_by_name=True allows both input styles"
    }


# =============================================================================
# 🔣 ENUMS & CUSTOM TYPES ENDPOINTS
# =============================================================================

@router.post(
    "/enums/user",
    response_model=UserWithEnums,
    summary="🔣 User Model with Validated Enums",
    description="""
    **Model**: UserWithEnums
    
    **Enum Fields Demonstrated**:
    
    🔹 role: UserRole (admin/moderator/user/guest)
    🔹 status: AccountStatus (pending/active/suspended/archived)
    🔹 theme: Theme (light/dark/auto)
    🔹 notification_freq: NotificationFrequency (immediate/daily/weekly/never)
    
    **Custom Type Fields**:
    
    🔹 email: EmailStr (RFC-compliant validation)
    🔹 website: Optional[HttpUrl] (valid URL with scheme/TLD)
    🔹 api_key: SecretStr (auto-masked in responses)
    🔹 birth_date: PastDate (must be in past)
    
    **Enum Metadata for Frontend**:
    - PlaygroundMeta class provides dropdown options
    - Each enum value has: value, label, description, color, permissions
    
    **Test Cases**:
    1. ✅ `{"role": "admin", "status": "active"}` → OK
    2. ❌ `{"role": "superuser"}` → "Input should be one of: admin, moderator, user, guest"
    3. ❌ `{"email": "not-an-email"}` → EmailStr validation error
    4. ✅ `{"api_key": "sk_secret"}` → Response shows "sk_****" (masked)
    
    **🎓 Interactive**: Select enum from dropdown → see validation + metadata.
    """
)
def validate_user_with_enums(payload: UserWithEnums):
    """Validate user with enum fields and custom types."""
    return payload


@router.post(
    "/enums/custom-types",
    response_model=CustomTypesDemo,
    summary="🔣 Custom Types: EmailStr, SecretStr, HttpUrl",
    description="""
    **Model**: CustomTypesDemo
    
    **Pydantic Custom Types Covered**:
    
    🔹 EmailStr: RFC 5322 compliant email validation
    🔹 HttpUrl: Validates scheme, domain, TLD (https://example.com)
    🔹 SecretStr: Auto-masks value in repr/str/logs
    🔹 PastDate/FutureDate: Date constraint helpers
    🔹 FilePath/DirectoryPath: Filesystem existence validation (demo: skipped)
    
    **SecretStr Behavior**:
    - Input: `"api_key": "sk_super_secret_123"`
    - repr(): `SecretStr('**********')`
    - model_dump(mode="json"): `"api_key": "sk_su****"` (masked)
    
    **Test Cases**:
    1. ✅ `{"contact_email": "user@example.com"}` → OK
    2. ❌ `{"contact_email": "invalid"}` → "value is not a valid email address"
    3. ✅ `{"website": "https://example.com/profile"}` → OK
    4. ❌ `{"website": "ftp://invalid"}` → "URL scheme not permitted"
    5. ✅ `{"api_key": "sk_test_123"}` → Response shows masked value
    
    **🎓 Learning**: Custom types provide domain-specific validation out of box.
    """
)
def validate_custom_types(payload: CustomTypesDemo):
    """Validate with Pydantic custom types."""
    return payload.to_safe_response()


@router.get(
    "/enums/schema/{enum_name}",
    summary="🔣 Export Enum Schema for Frontend Dropdowns",
    description="""
    **Feature**: Generate JSON Schema for enum → frontend <select> generation
    
    **Available Enums**:
    - UserRole, AccountStatus, Theme, NotificationFrequency, PaymentMethodEnum
    
    **Response Schema**:
    ```json
    {
      "type": "string",
      "enum": ["admin", "moderator", "user", "guest"],
      "x-display": "dropdown",
      "x-options": [
        {"value": "admin", "label": "Admin", "permissions": ["read", "write", ...]},
        ...
      ]
    }
    ```
    
    **Frontend Integration**:
    1. Fetch `/lab/enums/schema/UserRole`
    2. Parse x-options array
    3. Generate <select> with labels and metadata
    4. Use enum array for client-side validation
    
    **🎓 Interactive**: Select enum → see dropdown config for React/Vue.
    """
)
def get_enum_schema(enum_name: str = Path(..., description="Enum class name")):
    """Return JSON Schema for enum with frontend metadata."""
    enum_map = {
        "UserRole": UserRole,
        "AccountStatus": AccountStatus,
        "Theme": Theme,
        "NotificationFrequency": NotificationFrequency,
    }
    
    enum_cls = enum_map.get(enum_name)
    if not enum_cls:
        raise HTTPException(404, f"Enum not found: {enum_name}. Available: {list(enum_map.keys())}")
    
    return EnumPlayground.get_enum_schema(enum_cls)


# =============================================================================
# 🔄 SERIALIZATION ENDPOINTS
# =============================================================================

@router.post(
    "/serialize/demo",
    summary="🔄 Serialization Modes & Custom Serializers",
    description="""
    **Model**: SerializationDemo
    
    **Serialization Features**:
    
    🔹 model_dump modes:
    - mode="python": Keep Python types (datetime objects)
    - mode="json": Convert to JSON-compatible (ISO strings)
    
    🔹 @field_serializer:
    - created_at → ISO 8601 string
    - api_key → masked format "sk_****"
    - tags → comma-separated string (JSON mode only)
    
    🔹 include/exclude control:
    - to_public_response(): Hide api_key, exclude None
    - to_admin_response(): Include all fields
    - to_frontend_payload(): Minimal UI fields only
    
    🔹 Computed fields:
    - account_age_days: Auto-included unless exclude_computed=True
    
    **Query Param**: `context` controls output format:
    - public: API response (masked, minimal)
    - admin: Internal view (full data)
    - frontend: UI payload (essential fields)
    - database: ORM-ready dict
    
    **🎓 Interactive**: Same input → different outputs based on context.
    """
)
def demo_serialization(
    payload: SerializationDemo,
    context: str = Query("public", pattern="^(public|admin|frontend|database)$")
):
    """Serialize payload based on consumer context."""
    if context == "public":
        return payload.to_public_response()
    elif context == "admin":
        return payload.to_admin_view()
    elif context == "frontend":
        return payload.to_frontend_payload()
    elif context == "database":
        return payload.to_database_dict()
    return payload.model_dump(mode="json")


# =============================================================================
# 🎮 PLAYGROUND ENDPOINTS (Interactive Learning)
# =============================================================================

@router.post(
    "/playground/validate",
    summary="🎮 Universal Playground Validator",
    description=r"""
    **🎮 Interactive Learning: Universal Validator**
    
    Validate ANY registered model with ANY payload.
    Perfect for: Live demos, experimentation, learning by doing.
    
    **Query Params**:
    - `model`: Model name from registry (see /lab/features)
      * Examples: "basics.user", "computed.profile", "enums.user"
    
    **Body**: Arbitrary JSON matching model structure
    
    **Response Format**:
    ```json
    {
      "valid": true/false,
      "model": "model_name",
      "data": {...},           // Validated + serialized (if valid)
      "errors": [...],         // Field-specific errors (if invalid)
      "schema": {...},         // JSON Schema for form generation
      "computed": {...},       // Computed field values (if applicable)
      "tips": [...]            // Helpful hints for fixing errors
    }
    ```
    
    **Frontend Integration**:
    1. User selects model from dropdown
    2. Editor shows example payload (from /playground/examples/{model})
    3. User edits JSON → auto-validates on change
    4. Errors highlight specific fields in editor
    5. Success shows validated output + computed values
    
    **🎓 Try It Now**:
    ```bash
    curl -X POST http://localhost:8000/lab/playground/validate?model=basics.user \\
      -H "Content-Type: application/json" \\
      -d '{"id": 1, "username": "alice_dev", "email": "alice@example.com"}'
    ```
    """
)
def playground_validate(
    payload: Dict[str, Any] = Body(..., description="JSON payload to validate"),
    model: str = Query(..., description="Model name from registry", examples=["basics.user", "computed.profile"])
):
    """
    Universal validator for interactive learning playground.
    
    Accepts any registered model + any payload → returns validation result.
    """
    model_cls = MODEL_REGISTRY.get(model)
    if not model_cls:
        raise HTTPException(400, f"Unknown model: {model}. Available: {list(MODEL_REGISTRY.keys())}")
    
    try:
        # Validate with model
        instance = model_cls.model_validate(payload)
        
        # Extract computed fields (properties with @computed_field)
        computed = {}
        for attr_name in dir(instance):
            attr = getattr(type(instance), attr_name, None)
            if isinstance(attr, property):
                try:
                    computed[attr_name] = getattr(instance, attr_name)
                except:
                    pass  # Skip if computed field has dependencies not met
        
        return {
            "valid": True,
            "model": model,
            "data": instance.model_dump(mode="json", exclude_none=False),
            "computed": computed,
            "schema": instance.model_json_schema(),
            "message": "✓ Validation successful!",
        }
        
    except ValidationError as e:
        # Format errors for frontend highlighting
        field_errors = {}
        for error in e.errors(include_url=False, include_input=False):
            field_path = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            if field_path not in field_errors:
                field_errors[field_path] = []
            field_errors[field_path].append(error["msg"])
        
        # ✅ FIX: Fallback tips if method doesn't exist
        tips = ["💡 Review the error messages and adjust your input accordingly"]
        if hasattr(BasicsPlayground, '_get_validation_tips'):
            try:
                tips = BasicsPlayground._get_validation_tips(model, e.errors())
            except:
                pass
        
        return {
            "valid": False,
            "model": model,
            "input": payload,
            "field_errors": field_errors,
            "raw_errors": e.errors(include_url=False),
            "error_count": e.error_count(),
            "schema": model_cls.model_json_schema(),
            "message": f"✗ {e.error_count()} validation error(s)",
            "tips": tips,
        }


@router.get(
    "/playground/schema/{model}",
    summary="🎮 Export JSON Schema for Frontend Forms",
    description=r"""
    **🎮 Frontend Integration: JSON Schema Export**
    
    Generate OpenAPI-compatible JSON Schema for any registered model.
    Use to: Auto-generate forms, validate frontend input, create TypeScript interfaces.
    
    **Available Models**: See /lab/features or /lab/playground/validate
    
    **Response Includes**:
    ```json
    {
      "model": "model_name",
      "schema": {
        "type": "object",
        "properties": {...},
        "required": [...],
        "title": "Model Title",
        "description": "Model description",
        "$defs": {...}  // Nested model definitions
      },
      "playground_meta": {...}  // Custom hints for UI generation
    }
    ```
    
    **Frontend Usage**:
    1. Fetch schema: `GET /lab/playground/schema/basics.user`
    2. Parse properties → generate form fields
    3. Use constraints (minLength, pattern) for client validation
    4. Render examples as placeholder values
    5. Use json_schema_extra for custom UI hints (x-display, x-placeholder)
    
    **TypeScript Generation**:
    ```bash
    # Using quicktype or similar:
    curl http://localhost:8000/lab/playground/schema/basics.user | \
      jq '.schema' | \
      quicktype --lang typescript --output UserBasic.ts
    ```
    
    **🎓 Learning**: Schema export enables type-safe frontend/backend sync.
    """
)
def get_model_schema(model: str = Path(..., description="Model name")):
    """Return JSON Schema for model with playground metadata."""
    model_cls = MODEL_REGISTRY.get(model)
    if not model_cls:
        raise HTTPException(404, f"Model not found: {model}. Available: {list(MODEL_REGISTRY.keys())}")
    
    schema = model_cls.model_json_schema(
        ref_template="#/definitions/{model}",
    )
    
    # Extract playground metadata if defined
    playground_meta = {}
    if hasattr(model_cls, "PlaygroundConfig"):
        playground_meta = {k: v for k, v in model_cls.PlaygroundConfig.__dict__.items() if not k.startswith("_")}
    elif hasattr(model_cls, "PlaygroundMeta"):
        playground_meta = {k: v for k, v in model_cls.PlaygroundMeta.__dict__.items() if not k.startswith("_")}
    
    return {
        "model": model,
        "schema": schema,
        "title": schema.get("title"),
        "description": schema.get("description"),
        "definitions": schema.get("$defs", {}),
        "playground_meta": playground_meta,
    }


@router.get(
    "/playground/examples/{model}",
    summary="🎮 Get Pre-Filled Example Payloads",
    description="""
    **🎮 Learning Aid: Example Payloads**
    
    Return valid example payloads for any registered model.
    Perfect for: "Fill with example" button in playground, tutorial starters.
    
    **Response**:
    ```json
    {
      "model": "model_name",
      "examples": [
        {
          "name": "Basic Example",
          "description": "Minimal valid payload",
          "payload": {...}
        },
        {
          "name": "Advanced Example", 
          "description": "Payload with optional fields",
          "payload": {...}
        }
      ],
      "field_examples": {
        "username": ["alice_dev", "bob_user"],
        "email": ["alice@example.com", "bob@company.org"]
      }
    }
    ```
    
    **Frontend Usage**:
    1. User clicks "Load Example" in playground
    2. Fetch examples for selected model
    3. Populate JSON editor with example payload
    4. User can modify and re-validate
    
    **🎓 Learning**: Examples reduce friction for first-time users.
    """
)
def get_model_examples(model: str = Path(..., description="Model name")):
    """Return example payloads for model."""
    model_cls = MODEL_REGISTRY.get(model)
    if not model_cls:
        raise HTTPException(404, f"Model not found: {model}")
    
    # Generate examples from Field examples metadata
    examples = []
    field_examples = {}
    
    for field_name, field in model_cls.model_fields.items():
        if field.examples:
            field_examples[field_name] = field.examples
    
    # Create basic example from field examples
    basic_example = {}
    for field_name, field in model_cls.model_fields.items():
        if field.examples:
            basic_example[field_name] = field.examples[0]
        elif not field.is_required() and field.default is not None:
            basic_example[field_name] = field.default
    
    if basic_example:
        examples.append({
            "name": "Basic Example",
            "description": "Minimal valid payload using field examples",
            "payload": basic_example
        })
    
    return {
        "model": model,
        "examples": examples,
        "field_examples": field_examples,
        "note": "Use these payloads with POST /lab/playground/validate"
    }


@router.post(
    "/playground/compare",
    summary="🎮 Side-by-Side Validation Comparison",
    description="""
    **🎮 Interactive Learning: Compare Behaviors**
    
    Validate same payload with different configs/models to see behavior differences.
    
    **Comparison Types**:
    
    🔹 strict vs lenient:
    - Query: `?type=config&models=strict,lenient`
    - See: Type coercion differences
    
    🔹 before vs after validation:
    - Query: `?type=transform&models=field_validator_before,field_validator_after`
    - See: When normalization happens
    
    🔹 with vs without computed:
    - Query: `?type=output&models=computed.profile,computed.profile_minimal`
    - See: Computed fields in output
    
    **Response Format**:
    ```json
    {
      "input": {...},
      "comparisons": {
        "model_a": {"valid": bool, "output": {...}},
        "model_b": {"valid": bool, "output": {...}}
      },
      "differences": [
        "Model A coerces '123' to 123; Model B rejects it",
        "Model A includes computed fields; Model B excludes them"
      ]
    }
    ```
    
    **🎓 Learning**: Visual comparisons accelerate understanding of config impact.
    """
)
def playground_compare(
    payload: Dict[str, Any] = Body(...),
    type: str = Query("config", pattern="^(config|transform|output)$"),
    models: str = Query(..., description="Comma-separated model names to compare")
):
    """Compare validation results across different models/configs."""
    model_names = [m.strip() for m in models.split(",")]
    
    if len(model_names) < 2:
        raise HTTPException(400, "Provide at least 2 models to compare")
    
    results = {}
    for name in model_names:
        model_cls = MODEL_REGISTRY.get(name)
        if not model_cls:
            results[name] = {"error": f"Unknown model: {name}"}
            continue
        
        try:
            instance = model_cls.model_validate(payload)
            results[name] = {
                "valid": True,
                "output": instance.model_dump(mode="json", exclude_none=False)
            }
        except ValidationError as e:
            results[name] = {
                "valid": False,
                "errors": e.errors(include_url=False, include_input=False)
            }
    
    return {
        "input": payload,
        "comparison_type": type,
        "models_compared": model_names,
        "results": results,
    }


# =============================================================================
# 🔧 UTILITY ENDPOINTS
# =============================================================================

@router.get("/health", tags=["System"], summary="🔧 Health Check")
def health_check():
    """Health check for load balancers and monitoring."""
    # ✅ FIX: Use timezone-aware datetime (Python 3.12+ compatible)
    return {
        "status": "healthy",
        "service": "Pydantic Mastery Lab",
        "version": "2.0.0",
        "pydantic_version": "2.x",
        "features_available": len(MODEL_REGISTRY),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/models", tags=["Metadata"], summary="🔧 List Registered Models")
def list_models():
    """Return catalog of all registered models for dynamic UI generation."""
    return {
        "models": {
            name: {
                "class": cls.__name__,
                "module": cls.__module__,
                "fields": list(cls.model_fields.keys()),
                "has_computed": any(
                    isinstance(getattr(cls, attr, None), property)
                    for attr in dir(cls)
                ),
                "has_validators": hasattr(cls, "__pydantic_validators__"),
            }
            for name, cls in MODEL_REGISTRY.items()
        },
        "type_adapters": list(TYPE_ADAPTER_REGISTRY.keys()),
    }


@router.get("/errors/format", tags=["Metadata"], summary="🔧 Error Format Specification")
def error_format_spec():
    """
    Document the structured error format for frontend integration.
    
    Use this to build consistent error handling in your UI.
    """
    return {
        "validation_error_response": {
            "valid": False,
            "model": "model_name",
            "field_errors": {
                "field.path": ["Error message 1", "Error message 2"]
            },
            "raw_errors": [
                {
                    "loc": ["body", "field", "subfield"],
                    "msg": "Human-readable error message",
                    "type": "error_type_code",
                    "input": "original_input_value"
                }
            ],
            "error_count": 2,
            "schema": {},  # JSON Schema for context
            "tips": ["Helpful hint 1", "Hint 2"]
        },
        "frontend_integration": {
            "highlight_field": "Use field_errors keys to highlight editor fields",
            "show_message": "Display first error message per field",
            "provide_tips": "Show tips array as helpful suggestions",
            "link_docs": "Use schema to link to field documentation"
        }
    }


# =============================================================================
# 🚀 DEPLOYMENT & INTEGRATION HELPERS
# =============================================================================

@router.get("/openapi.json", include_in_schema=False)
def get_openapi():
    """Proxy to FastAPI's auto-generated OpenAPI schema."""
    # In production, you might customize this
    from fastapi.openapi.utils import get_openapi as fastapi_get_openapi
    return fastapi_get_openapi(
        title="Pydantic Mastery Lab",
        version="2.0.0",
        routes=router.routes,
    )


@router.post("/webhook/demo", summary="🔧 Webhook Validation Demo", include_in_schema=False)
def webhook_demo(payload: Dict[str, Any] = Body(...)):
    """
    Demo endpoint for webhook validation patterns.
    
    In production: Use TypeAdapter to validate arbitrary webhook payloads.
    """
    # Example: Validate GitHub-style webhook
    if "event_type" in payload and "payload" in payload:
        adapter = TypeAdapter(Dict[str, Any])  # Replace with specific schema
        try:
            validated = adapter.validate_python(payload["payload"])
            return {
                "received": True,
                "event": payload["event_type"],
                "validated": validated,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
        except ValidationError as e:
            return {
                "received": True,
                "event": payload["event_type"],
                "valid": False,
                "errors": e.errors(include_url=False)
            }
    
    return {"error": "Expected {event_type, payload} structure"}

@router.get("/docs-guide", tags=["📚 Documentation"], summary="How to Use This API")
def docs_guide():
    """
    Return a guide for using this interactive API.
    
    Perfect for: First-time users, recruiter walkthroughs.
    """
    return {
        "getting_started": [
            "1. Open /docs to see all endpoints",
            "2. Click 'Try it out' on any endpoint",
            "3. Use example payloads from /lab/playground/examples/{model}",
            "4. Export schemas from /lab/playground/schema/{model}"
        ],
        "recommended_flow": [
            "Start with /lab/basics/user to learn Field constraints",
            "Try /lab/validators/field to see @field_validator modes",
            "Explore /lab/playground/validate for universal testing",
            "Export schemas for your frontend with /lab/playground/schema/{model}"
        ],
        "recruiter_highlights": [
            "Every endpoint demonstrates a specific Pydantic v2 feature",
            "Structured errors include field paths for frontend highlighting",
            "Schema export enables TypeScript code generation",
            "All models include PlaygroundConfig for interactive learning"
        ]
    }