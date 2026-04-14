
# 📐 `API.md` (Detailed API Documentation)

```markdown
# 🌐 Pydantic Mastery Lab - API Documentation

> **Production-Grade FastAPI + Pydantic v2 Reference**  
> Interactive validation, serialization, and dynamic schema demonstrations for recruiters and learners.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.x-e92063.svg)](https://docs.pydantic.dev/latest/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Quick Links

| Resource | Link | Description |
|----------|------|-------------|
| 🎮 **Interactive Docs** | [`/docs`](http://127.0.0.1:8000/docs) | Swagger UI: Try endpoints live, test payloads, view schemas |
| 📖 **Clean Reference** | [`/redoc`](http://127.0.0.1:8000/redoc) | ReDoc: Printable, mobile-friendly API reference |
| 🔧 **OpenAPI Schema** | [`/openapi.json`](http://127.0.0.1:8000/openapi.json) | Raw JSON schema for codegen, frontend integration |
| 🏠 **Lab Home** | [`/api/lab/`](http://127.0.0.1:8000/api/lab/) | Feature catalog, quick links, recruiter highlights |
| 🧪 **Health Check** | [`/api/lab/health`](http://127.0.0.1:8000/api/lab/health) | Service status, version, feature count |

---

## 🚀 Getting Started

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd pydantic-mastery
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Open Documentation
```bash
# Interactive Swagger UI
open http://127.0.0.1:8000/docs

# Or clean ReDoc reference
open http://127.0.0.1:8000/redoc
```

### 4. Test an Endpoint (cURL)
```bash
# Validate a basic user
curl -X POST http://127.0.0.1:8000/api/lab/basics/user \
  -H "Content-Type: application/json" \
  -d '{
    "id": 1,
    "username": "alice_dev",
    "email": "alice@example.com",
    "role": "admin"
  }'
```

**Expected Response**:
```json
{
  "id": 1,
  "username": "alice_dev",
  "email": "alice@example.com",
  "role": "admin",
  "api_key": null,
  "is_active": true,
  "address": null,
  "created_at": "2025-04-14T12:00:00"
}
```

---

## 📚 Feature Categories

### 🧱 Basics: BaseModel & Field Fundamentals
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/basics/user` | `POST` | Validate user with Field constraints | `min_length`, `pattern`, `examples`, nested dicts |
| `/lab/basics/constraints` | `POST` | Test all Field constraint types | String, numeric, float, list constraints |
| `/lab/basics/methods` | `POST` | Demonstrate model methods | `model_validate()`, `model_dump()`, `model_copy()` |

**Example Request** (`/lab/basics/user`):
```json
{
  "id": 42,
  "username": "demo_user",
  "email": "demo@example.com",
  "role": "user",
  "address": {
    "street": "123 Test Ave",
    "city": "QA City",
    "country": "US"
  }
}
```

**Example Error Response**:
```json
{
  "error": {
    "type": "validation_error",
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please correct the highlighted fields.",
    "request_id": "a1b2c3d4",
    "details": {
      "field_errors": {
        "username": ["String should have at least 3 characters"],
        "email": ["String should match pattern"]
      },
      "total_errors": 2
    },
    "playground": {
      "highlight_fields": ["username", "email"],
      "tips": ["💡 Review the error messages and adjust your input accordingly"]
    }
  }
}
```

---

### 🔍 Validators: Field & Model Logic
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/validators/field` | `POST` | Test `@field_validator` modes | `before`, `after`, `wrap` normalization |
| `/lab/validators/model` | `POST` | Cross-field validation | Password matching, subscription rules |
| `/lab/validators/order` | `POST` | Complex order validation | Auto-totals, discount limits, shipping logic |

**Validator Modes Explained**:
```python
# mode="before": Transform raw input BEFORE type coercion
@field_validator("email", mode="before")
def normalize_email(cls, v: str) -> str:
    return v.strip().lower()  # "  USER@Example.COM  " → "user@example.com"

# mode="after": Validate AFTER field is parsed
@field_validator("tags", mode="after")
def deduplicate_tags(cls, v: List[str]) -> List[str]:
    return list(dict.fromkeys(v))  # ["py", "Py", "PY"] → ["py"]

# mode="wrap": Full control over validation pipeline
@field_validator("age", mode="wrap")
def validate_age_range(cls, v: int, handler) -> int:
    if v < 0: raise ValueError("Age cannot be negative")
    return handler(v)  # Run built-in validation
```

---

### 🧮 Computed Fields: Derived Values
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/computed/profile` | `POST` | User profile with computed fields | `full_name`, `age`, `account_age_days` |
| `/lab/computed/order` | `POST` | Order with computed pricing | `subtotal`, `tax`, `total`, `savings_message` |
| `/lab/computed/playground` | `POST` | Beginner-friendly computed demo | Simple greeting generation |

**Computed Fields in Action**:
```json
// Input
{
  "first_name": "Alice",
  "last_name": "Smith",
  "date_of_birth": "1990-05-15",
  "is_premium": true
}

// Output (with computed fields)
{
  "first_name": "Alice",
  "last_name": "Smith",
  "full_name": "Alice Smith",           // ✅ Computed: first + last
  "age": 34,                            // ✅ Computed: from date_of_birth
  "account_age_days": 45,               // ✅ Computed: since creation
  "display_role": "Premium Member",     // ✅ Computed: based on is_premium
  "email_domain": "example.com",        // ✅ Computed: extracted from email
  "premium_badge": "✨ Premium"         // ✅ Computed: conditional badge
}
```

---

### 🔧 TypeAdapter: Dynamic Validation
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/adapter/validate` | `POST` | Validate any JSON against any type | Primitives, collections, custom types |
| `/lab/adapter/batch` | `POST` | Batch validate lists of models | CSV import, bulk operations |

**Dynamic Validation Example**:
```bash
# Validate a list of integers
curl -X POST "http://127.0.0.1:8000/api/lab/adapter/validate?type=List[int]" \
  -H "Content-Type: application/json" \
  -d '{"data": [1, 2, 3, 4]}'

# Response
{
  "valid": true,
  "type": "List[int]",
  "input": [1, 2, 3, 4],
  "validated": [1, 2, 3, 4],
  "serialized": [1, 2, 3, 4],
  "schema": {
    "type": "array",
    "items": {"type": "integer"}
  }
}
```

---

### ⚙️ Strict Config: Production-Grade Validation
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/config/strict` | `POST` | Strict mode validation | `strict=True`, `extra="forbid"` |
| `/lab/config/compare` | `POST` | Side-by-side validation comparison | Strict vs lenient behavior |
| `/lab/config/alias` | `POST` | Alias generator demo | camelCase ↔ snake_case conversion |

**Strict vs Lenient Comparison**:
```json
// Input: {"id": "123", "username": "test"}

// Strict mode response (error):
{
  "valid": false,
  "errors": [{"loc": ["id"], "msg": "Input should be a valid integer"}]
}

// Lenient mode response (coerced):
{
  "valid": true,
  "data": {"id": 123, "username": "test"}  // "123" → 123
}
```

---

### 🔣 Enums & Custom Types
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/enums/user` | `POST` | User model with validated enums | `UserRole`, `AccountStatus`, `Theme` |
| `/lab/enums/custom-types` | `POST` | Custom type validation | `EmailStr`, `SecretStr`, `HttpUrl` |
| `/lab/enums/schema/{enum}` | `GET` | Export enum schema for frontend | JSON Schema for `<select>` generation |

**Enum Schema Export** (`/lab/enums/schema/UserRole`):
```json
{
  "type": "string",
  "enum": ["admin", "moderator", "user", "guest"],
  "x-display": "dropdown",
  "x-options": [
    {"value": "admin", "label": "Admin", "permissions": ["read", "write", "delete", "manage_users"]},
    {"value": "moderator", "label": "Moderator", "permissions": ["read", "write", "delete"]},
    {"value": "user", "label": "User", "permissions": ["read", "write"]},
    {"value": "guest", "label": "Guest", "permissions": ["read"]}
  ]
}
```

---

### 🔄 Serialization: Context-Aware Output
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/serialize/demo` | `POST` | Serialization modes & custom serializers | `model_dump` modes, `@field_serializer`, include/exclude |

**Context-Aware Serialization**:
```python
# Query param: ?context=public|admin|frontend|database

# public: Masked API response
{
  "id": 1,
  "username": "alice_dev",
  "email": "alice@example.com",
  "api_key": "sk_****"  // Masked
}

# admin: Full internal view
{
  "id": 1,
  "username": "alice_dev",
  "email": "alice@example.com",
  "api_key": "sk_test_1234567890abcdef",  // Full value
  "internal_notes": "VIP customer"  // Included
}

# frontend: Minimal UI payload
{
  "username": "alice_dev",
  "email": "alice@example.com",
  "theme": "dark"
}
```

---

### 🎮 Playground: Interactive Learning
| Endpoint | Method | Description | Key Features |
|----------|--------|-------------|-------------|
| `/lab/playground/validate` | `POST` | Universal validator: any model + payload | Live validation, structured errors |
| `/lab/playground/schema/{model}` | `GET` | Export JSON Schema for frontend forms | TypeScript codegen, auto-forms |
| `/lab/playground/examples/{model}` | `GET` | Get pre-filled example payloads | "Try it" button data |
| `/lab/playground/compare` | `POST` | Side-by-side validation comparison | Learn by comparing behaviors |

**Playground Validation Flow**:
```mermaid
graph LR
    A[User selects model] --> B[Fetch examples from /playground/examples/{model}]
    B --> C[Populate JSON editor]
    C --> D[User edits payload]
    D --> E[POST to /playground/validate?model=...]
    E --> F{Valid?}
    F -->|Yes| G[Show validated output + computed fields]
    F -->|No| H[Highlight fields using field_errors]
    H --> I[Show tips for fixing errors]
```

**Example Playground Response (Error)**:
```json
{
  "valid": false,
  "model": "basics.user",
  "input": {"id": "not-an-int", "username": "ab", "email": "invalid"},
  "field_errors": {
    "id": ["Input should be a valid integer"],
    "username": ["String should have at least 3 characters"],
    "email": ["String should match pattern"]
  },
  "error_count": 3,
  "schema": {...},
  "message": "✗ 3 validation error(s)",
  "tips": [
    "💡 Ensure numbers are not quoted: use `42` not `\"42\"`",
    "💡 Username must be 3-30 characters",
    "💡 Email must be format: user@domain.com"
  ]
}
```

---

## 🔧 OpenAPI Schema Export

### Export for Frontend Integration
```bash
# Download OpenAPI schema
curl http://127.0.0.1:8000/openapi.json -o openapi.json

# Generate TypeScript interfaces (using quicktype)
npm install -g quicktype
cat openapi.json | jq '.components.schemas' | quicktype --lang typescript --output src/types.ts

# Generate API client (using openapi-generator)
npm install -g @openapitools/openapi-generator-cli
openapi-generator-cli generate \
  -i http://127.0.0.1:8000/openapi.json \
  -g typescript-axios \
  -o ./frontend-client
```

### Generated TypeScript Example
```typescript
// src/types.ts (auto-generated from OpenAPI schema)
export interface UserBasic {
  id: number;
  username: string;
  email: string;
  role?: "admin" | "moderator" | "user" | "guest";
  api_key?: string | null;
  is_active?: boolean;
  address?: { [key: string]: string } | null;
  created_at?: string;
}

export interface ValidationErrorResponse {
  error: {
    type: "validation_error";
    code: "VALIDATION_ERROR";
    message: string;
    request_id: string;
    details: {
      field_errors: { [key: string]: string[] };
      total_errors: number;
    };
    playground: {
      highlight_fields: string[];
      tips: string[];
    };
  };
}
```

---

## 🧪 Testing the API

### Run the Test Suite
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app/models --cov-report=term-missing

# Run specific test file
pytest tests/test_routes.py -v
```

### Manual Testing with cURL
```bash
# 1. Health check
curl http://127.0.0.1:8000/api/lab/health | jq .

# 2. Validate basic user (valid)
curl -X POST http://127.0.0.1:8000/api/lab/basics/user \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "username": "alice_dev", "email": "alice@example.com"}' | jq .

# 3. Validate basic user (invalid - triggers errors)
curl -X POST http://127.0.0.1:8000/api/lab/basics/user \
  -H "Content-Type: application/json" \
  -d '{"id": "not-an-int", "username": "ab", "email": "invalid"}' | jq .

# 4. Playground validate with computed fields
curl -X POST "http://127.0.0.1:8000/api/lab/playground/validate?model=computed.profile" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Bob",
    "last_name": "Jones",
    "date_of_birth": "1985-12-25",
    "is_premium": false
  }' | jq .computed
```

---

## 🎯 For Recruiters: Technical Highlights

### ✅ Pydantic v2 Mastery Demonstrated
| Feature | File | Why It Matters |
|---------|------|---------------|
| `@field_validator(mode="before/after/wrap")` | `field_validators.py` | Shows deep understanding of validation pipeline stages |
| `@model_validator` for cross-field logic | `model_validators.py` | Demonstrates complex business rule enforcement |
| `@computed_field` for derived values | `computed.py` | Shows efficient, DRY pattern for calculated fields |
| `TypeAdapter` for dynamic validation | `type_adapters.py` | Proves ability to handle schema-less/external APIs |
| `ConfigDict(strict=True, extra="forbid")` | `strict_config.py` | Shows production-hardening mindset |
| `Annotated[T, ...]` composable constraints | `annotated_advanced.py` | Demonstrates scalable, reusable validation patterns |
| `Field(discriminator=...)` unions | `discriminated_unions.py` | Replaces fragile `if/else` with type-safe routing |

### ✅ Production-Ready Patterns
```python
# 1. Structured error handling with field paths
{
  "error": {
    "field_errors": {"username": ["Too short"]},  # Frontend can highlight
    "tips": ["💡 Username must be 3+ chars"]       # Helpful guidance
  }
}

# 2. Request ID correlation for tracing
# Every response includes: "request_id": "a1b2c3d4"
# Enables log correlation across microservices

# 3. Secret masking for security
# SecretStr auto-masks in logs: SecretStr('**********')
# Custom serializers mask API keys: "sk_****"

# 4. Context-aware serialization
def to_public_response(self):   # Masked, minimal for API
def to_admin_response(self):    # Full data for internal tools
def to_frontend_payload(self):  # UI-ready fields only
```

### ✅ Interactive Learning Foundation
- `/lab/playground/validate` accepts arbitrary JSON → returns structured errors
- `/lab/playground/schema/{model}` exports JSON Schema for auto-form generation
- Error responses include `field_errors` keys for editor highlighting
- Computed fields auto-update in playground preview
- All models include `PlaygroundConfig` metadata for frontend integration

---

## 🗂️ Project Structure
```
pydantic-mastery/
├── README.md                 # Project overview (this file is API.md)
├── API.md                    # This detailed API documentation
├── requirements.txt          # Python dependencies
├── app/
│   ├── main.py              # FastAPI entrypoint, wiring
│   ├── core/
│   │   ├── config.py        # Pydantic Settings, env overrides
│   │   └── exceptions.py    # Structured error handlers
│   ├── middleware/
│   │   └── request_id.py    # Request correlation ID middleware
│   ├── models/              # 11 focused Pydantic v2 feature files
│   ├── routes/
│   │   └── pydantic_lab.py  # 50+ learning & playground endpoints
│   ├── services/            # Optional: typed JSON storage
│   └── data/
│       ├── data.json        # Production-like test records
│       └── playground_examples.json # Valid/invalid payloads for UI
├── tests/                   # pytest suite: models, routes, middleware
└── docs/                    # (Optional) Static documentation output
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

**Code Standards**:
- Follow PEP 8 for Python style
- Add docstrings to all public functions/classes
- Include tests for new features
- Update this `API.md` for new endpoints

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgments

- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Excellent framework and docs
- [Pydantic Documentation](https://docs.pydantic.dev/) - Powerful validation library
- [Swagger UI](https://swagger.io/tools/swagger-ui/) - Beautiful interactive docs
- [ReDoc](https://redocly.com/) - Clean, readable API reference

---

> **Built with ❤️ for developers who believe type safety shouldn't slow them down.**  
> *Questions? Open an issue or reach out directly.*

---

## 🖼️ Swagger UI Screenshot (Placeholder)

*Since this is a static Markdown file, actual screenshots can't be embedded. When you run the server locally, visit [`/docs`](http://127.0.0.1:8000/docs) to see:*

```
┌─────────────────────────────────────────┐
│ 🎓 Pydantic v2 Mastery Lab              │
├─────────────────────────────────────────┤
│ 🔍 Search endpoints...                  │
│                                         │
│ 🧱 Basics                               │
│   • POST /lab/basics/user              │
│   • POST /lab/basics/constraints       │
│   • POST /lab/basics/methods           │
│                                         │
│ 🔍 Validators                           │
│   • POST /lab/validators/field         │
│   • POST /lab/validators/model         │
│                                         │
│ ... (11 feature categories)             │
└─────────────────────────────────────────┘
```

**Click any endpoint → "Try it out" → Fill payload → Execute → See live response!**

---

## 🚀 One-Command Demo

For recruiters or quick demos, run this to test the core flow:

```bash
# Start server in background
uvicorn app.main:app --reload &

# Wait for startup
sleep 3

# Test the universal playground validator
curl -s -X POST "http://127.0.0.1:8000/api/lab/playground/validate?model=basics.user" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "username": "demo", "email": "demo@example.com"}' | jq '{valid, model, message}'

# Output: {"valid":true,"model":"basics.user","message":"✓ Validation successful!"}

# Stop server
pkill -f "uvicorn app.main:app"
```
