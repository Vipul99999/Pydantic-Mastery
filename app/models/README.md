# 📦 Pydantic Models Directory

## 🎯 Purpose
This directory contains the **validation & serialization layer** for the Pydantic Mastery Lab. Each file isolates a specific Pydantic v2 concept, demonstrates production-ready patterns, and is explicitly designed to power both the API and the future interactive learning platform.

## 📁 Architecture & Conventions
| Convention | Reason |
|------------|--------|
| `ConfigDict` over legacy `class Config` | Pydantic v2 standard, enables type-checking & IDE support |
| One concept per file | Clear separation for recruiters, easier testing & maintenance |
| `model_rebuild()` for forward refs | Required in v2 for recursive/nested models |
| `mode="before/after/wrap"` validators | Replaces deprecated `@validator`/`@root_validator` |
| `Annotated[T, metadata]` | Composable, reusable constraint pipelines |
| `model_dump(mode="json")` in routes | Guarantees JSON-serializable API responses |

## 🔍 File-by-File Breakdown

| File | Core Pydantic Features | Real-World Use Case | Playground Integration |
|------|------------------------|---------------------|------------------------|
| `basics.py` | `BaseModel`, `Field()`, constraints, defaults, `model_dump()` modes | DTOs, API request/response contracts | Field constraint testing, example payload generation |
| `field_validators.py` | `@field_validator(mode="before/after/wrap")` | Email normalization, tag deduplication, age range enforcement | Live input → transformed output demo |
| `model_validators.py` | `@model_validator(mode="before/after")`, cross-field logic | Password matching, subscription tier rules, order total validation | Side-by-side config comparison |
| `computed.py` | `@computed_field`, `@property`, derived values | Full name, age calculation, pricing breakdown, status badges | Real-time computed value preview |
| `type_adapters.py` | `TypeAdapter`, `validate_python()`, `dump_json()`, batch validation | Webhook payloads, config files, plugin systems, CSV imports | "Paste any JSON, validate against type" playground |
| `strict_config.py` | `ConfigDict(strict=True, extra="forbid", validate_assignment, alias_generator, frozen)` | API input hardening, ORM mapping, immutable configs, JS/Python naming sync | Toggle strict/lenient → see coercion differences |
| `enum_custom.py` | `StrEnum`, `EmailStr`, `SecretStr`, `HttpUrl`, custom validators | Role-based access, UI themes, secure token handling, URL validation | Dropdown generation, secret masking demo |
| `serialization.py` | `@field_serializer`, `include/exclude`, `exclude_none`, `context` | Public API responses, admin views, frontend payloads, database sync | Context-aware serialization selector |
| `annotated_advanced.py` | `Annotated[T, ...]`, `StringConstraints`, `Before/AfterValidator`, generic constraints | Reusable domain types (USPhone, Currency, SKU), composable rules | Constraint pipeline visualization |
| `nested_generics.py` | Recursive models, `Generic[T]`, `PaginatedResponse`, forward references | Comment threads, org hierarchies, paginated list endpoints | Tree structure viewer, pagination metadata |
| `discriminated_unions.py` | `Literal`, `Union`, `Field(discriminator="...")`, nested routing | Payment methods, webhook events, search filters, event sourcing | Auto-routing demo, union error diagnostics |

## 🧩 Core Pydantic v2 Patterns Demonstrated

### 1. Validation Pipeline Control
```python
@field_validator("email", mode="before")  # Pre-coercion cleaning
@field_validator("tags", mode="after")    # Post-parsing business logic
@field_validator("age", mode="wrap")      # Full pipeline control