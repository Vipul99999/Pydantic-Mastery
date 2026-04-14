"""
Demonstrates TypeAdapter in Pydantic v2.

Key concepts covered:
- TypeAdapter for validating non-Model types (list, dict, primitive)
- Runtime/dynamic validation without FastAPI auto-parsing
- validate_python() vs validate_json() vs validate_strings()
- dump_python() vs dump_json() for serialization
- Reusable adapter instances for performance
- Adapter with custom config (ConfigDict)
- Schema generation from TypeAdapter

Real-world use cases:
- Webhook payload validation (arbitrary JSON)
- Configuration file validation (YAML/JSON → Python)
- Plugin system: validate plugin config against schema
- Data pipeline: validate batches of records
- API gateway: validate requests before routing

🎓 INTERACTIVE LEARNING READY:
- TypeAdapter is perfect for "paste any JSON, see validation result" playground
- Can demonstrate validation of lists, dicts, primitives without defining models
- Schema export enables frontend form generation for any type
- Error messages include exact path for highlighting in editor
"""

from pydantic import TypeAdapter, ValidationError, BaseModel, Field, ConfigDict
from pydantic.type_adapter import T
from typing import List, Dict, Any, Optional, Union, Literal, get_origin, get_args
from datetime import datetime, date
from enum import StrEnum
import json
import re


# === Basic TypeAdapter Examples ===

# Adapter for simple types (no model definition needed)
IntListAdapter = TypeAdapter(List[int])
StrDictAdapter = TypeAdapter(Dict[str, str])
EmailAdapter = TypeAdapter(str)  # With constraints via Annotated


# === TypeAdapter with Annotated Constraints ===

from typing import Annotated
from pydantic import StringConstraints, AfterValidator, BeforeValidator

# Reusable constrained types
ConstrainedEmail = Annotated[
    str,
    StringConstraints(pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    BeforeValidator(lambda v: v.strip().lower() if isinstance(v, str) else v)
]

ConstrainedTag = Annotated[
    str,
    StringConstraints(min_length=2, max_length=30, pattern=r"^[a-z0-9-]+$")
]

# Create adapters for constrained types
EmailListAdapter = TypeAdapter(List[ConstrainedEmail])
TagListAdapter = TypeAdapter(List[ConstrainedTag])


# === TypeAdapter Demo Model ===

class TypeAdapterDemo(BaseModel):
    """
    Model demonstrating TypeAdapter usage patterns.
    
    🎓 Learning Focus: Show difference between model validation and adapter validation.
    """
    
    description: str = "TypeAdapter allows validation of arbitrary types at runtime"
    
    # 🎓 Interactive: Users can paste JSON and select target type
    @staticmethod
    def validate_dynamic(data: Any, target_type: str) -> Dict[str, Any]:
        """
        Validate arbitrary data against a named type.
        
        🎓 Playground Endpoint: POST /lab/dynamic/validate
        Frontend sends: {"data": [...], "target_type": "List[int]"}
        """
        # Type registry for playground
        type_registry = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "List[int]": List[int],
            "List[str]": List[str],
            "Dict[str, int]": Dict[str, int],
            "Dict[str, str]": Dict[str, str],
            "Email": ConstrainedEmail,
            "List[Email]": List[ConstrainedEmail],
            "Tag": ConstrainedTag,
            "List[Tag]": List[ConstrainedTag],
        }
        
        target = type_registry.get(target_type)
        if not target:
            return {
                "valid": False,
                "error": f"Unknown type: {target_type}",
                "available_types": list(type_registry.keys())
            }
        
        # Create adapter (cached in production)
        adapter = TypeAdapter(target)
        
        try:
            # Validate Python object
            validated = adapter.validate_python(data)
            
            # Serialize for JSON response
            serialized = adapter.dump_python(validated, mode="json")
            
            return {
                "valid": True,
                "type": target_type,
                "input": data,
                "validated": validated,
                "serialized": serialized,
                "schema": adapter.json_schema(),
            }
            
        except ValidationError as e:
            return {
                "valid": False,
                "type": target_type,
                "input": data,
                "errors": e.errors(include_url=False, include_input=False),
                "error_count": e.error_count(),
                "schema": adapter.json_schema(),
            }
    
    @staticmethod
    def validate_json_string(json_str: str, target_type: str) -> Dict[str, Any]:
        """
        Validate JSON string directly (without parsing first).
        
        🎓 Learning Point: validate_json() parses AND validates in one step.
        More efficient than json.loads() + validate_python().
        """
        type_registry = {
            "int": int,
            "List[int]": List[int],
            "Dict[str, str]": Dict[str, str],
            "Email": ConstrainedEmail,
        }
        
        target = type_registry.get(target_type)
        if not target:
            return {"valid": False, "error": f"Unknown type: {target_type}"}
        
        adapter = TypeAdapter(target)
        
        try:
            # Parse JSON string AND validate in one step
            validated = adapter.validate_json(json_str)
            return {
                "valid": True,
                "validated": adapter.dump_python(validated, mode="json"),
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": e.errors(include_url=False),
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON: {e.msg}",
            }


# === Advanced: TypeAdapter for Model Lists ===

class BatchValidator:
    """
    Reusable validator for batches of Pydantic models.
    
    🎓 Use Case: Validate CSV import, webhook batch, API bulk endpoint.
    """
    
    def __init__(self, model: type[BaseModel]):
        """
        Initialize with target model.
        
        Adapter is created once and reused for performance.
        """
        self.model = model
        # Adapter for list of models
        self.adapter = TypeAdapter(List[model])
        # Adapter for single model (for error context)
        self.single_adapter = TypeAdapter(model)
    
    def validate_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of items against the model.
        
        Returns detailed results for each item + summary.
        🎓 Interactive: Show which items failed and why.
        """
        results = {
            "total": len(items),
            "valid": 0,
            "invalid": 0,
            "items": [],
            "errors": []
        }
        
        for idx, item in enumerate(items):
            try:
                # Validate single item with index context
                validated = self.single_adapter.validate_python(item)
                results["valid"] += 1
                results["items"].append({
                    "index": idx,
                    "valid": True,
                    "data": validated.model_dump(mode="json")
                })
            except ValidationError as e:
                results["invalid"] += 1
                results["errors"].append({
                    "index": idx,
                    "errors": e.errors(include_url=False, include_input=False)
                })
                results["items"].append({
                    "index": idx,
                    "valid": False,
                    "input": item
                })
        
        results["success_rate"] = round(results["valid"] / results["total"] * 100, 1) if results["total"] > 0 else 0
        return results
    
    def validate_and_filter(self, items: List[Dict[str, Any]]) -> List[BaseModel]:
        """
        Validate batch and return only valid items.
        
        🎓 Use Case: Import wizard - show errors, let user fix, retry.
        """
        valid_items = []
        for item in items:
            try:
                validated = self.single_adapter.validate_python(item)
                valid_items.append(validated)
            except ValidationError:
                # Skip invalid items (log in production)
                pass
        return valid_items


# === TypeAdapter with Custom Config ===

class StrictAdapter:
    """
    TypeAdapter with strict validation config.
    
    🎓 Learning Point: ConfigDict works with TypeAdapter too!
    """
    
    def __init__(self, target_type, strict: bool = True, extra: str = "forbid"):
        self.adapter = TypeAdapter(
            target_type,
            config=ConfigDict(
                strict=strict,        # No type coercion
                extra=extra,          # Forbid unknown fields
                validate_assignment=True,
            )
        )
    
    def validate(self, data: Any) -> Dict[str, Any]:
        """Validate with strict config."""
        try:
            result = self.adapter.validate_python(data)
            return {
                "valid": True,
                "data": self.adapter.dump_python(result, mode="json"),
                "config": "strict"
            }
        except ValidationError as e:
            return {
                "valid": False,
                "errors": e.errors(include_url=False),
                "config": "strict"
            }


# === Playground-Specific Adapter ===

class PlaygroundAdapter:
    """
    Adapter designed for interactive learning playground.
    
    🎓 Frontend Integration:
    - Returns schema for form generation
    - Includes examples for each type
    - Provides human-readable error messages
    - Supports "try it" with sample data
    """
    
    # Registry of types with examples and descriptions
    PLAYGROUND_TYPES = {
        "int": {
            "type": int,
            "description": "Integer number",
            "examples": [42, -10, 0],
            "schema_hint": {"type": "integer"}
        },
        "float": {
            "type": float,
            "description": "Floating point number",
            "examples": [3.14, -0.5, 100.0],
            "schema_hint": {"type": "number"}
        },
        "str": {
            "type": str,
            "description": "Text string",
            "examples": ["hello", "Pydantic v2", "user@example.com"],
            "schema_hint": {"type": "string"}
        },
        "bool": {
            "type": bool,
            "description": "True or false value",
            "examples": [True, False],
            "schema_hint": {"type": "boolean"}
        },
        "List[int]": {
            "type": List[int],
            "description": "List of integers",
            "examples": [[1, 2, 3], [42], []],
            "schema_hint": {"type": "array", "items": {"type": "integer"}}
        },
        "Dict[str, str]": {
            "type": Dict[str, str],
            "description": "Dictionary with string keys and values",
            "examples": [{"name": "Alice", "role": "admin"}, {}],
            "schema_hint": {"type": "object", "additionalProperties": {"type": "string"}}
        },
        "Email": {
            "type": ConstrainedEmail,
            "description": "Validated email address (RFC compliant)",
            "examples": ["user@example.com", "admin@company.org"],
            "schema_hint": {"type": "string", "format": "email", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
        },
        "List[Email]": {
            "type": List[ConstrainedEmail],
            "description": "List of validated email addresses",
            "examples": [["a@b.com", "c@d.org"]],
            "schema_hint": {"type": "array", "items": {"type": "string", "format": "email"}}
        },
    }
    
    @classmethod
    def get_type_info(cls, type_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a playground type."""
        info = cls.PLAYGROUND_TYPES.get(type_name)
        if not info:
            return None
        
        # Generate JSON schema for frontend form
        adapter = TypeAdapter(info["type"])
        schema = adapter.json_schema()
        
        return {
            "name": type_name,
            "description": info["description"],
            "examples": info["examples"],
            "schema": schema,
            "schema_hint": info["schema_hint"],
        }
    
    @classmethod
    def validate_with_feedback(cls, data: Any, type_name: str) -> Dict[str, Any]:
        """
        Validate with playground-friendly error messages.
        
        🎓 Frontend: Use this to show inline validation errors.
        """
        info = cls.get_type_info(type_name)
        if not info:
            return {"valid": False, "error": f"Unknown type: {type_name}"}
        
        adapter = TypeAdapter(info["type"])
        
        try:
            validated = adapter.validate_python(data)
            return {
                "valid": True,
                "message": "✓ Validation successful!",
                "input": data,
                "validated": adapter.dump_python(validated, mode="json"),
                "type": type_name,
            }
        except ValidationError as e:
            # Format errors for frontend highlighting
            field_errors = {}
            for error in e.errors(include_url=False, include_input=False):
                # error["loc"] is tuple like ('body', 'field_name')
                field_path = ".".join(str(loc) for loc in error["loc"] if loc != "body")
                if field_path not in field_errors:
                    field_errors[field_path] = []
                field_errors[field_path].append(error["msg"])
            
            return {
                "valid": False,
                "message": f"✗ {e.error_count()} validation error(s)",
                "input": data,
                "field_errors": field_errors,
                "raw_errors": e.errors(include_url=False),
                "type": type_name,
                "tips": cls._get_validation_tips(type_name, e.errors()),
            }
    
    @staticmethod
    def _get_validation_tips(type_name: str, errors: List[dict]) -> List[str]:
        """
        Generate helpful tips based on validation errors.
        
        🎓 Learning: Turn errors into teaching moments.
        """
        tips = []
        error_types = set(err["type"] for err in errors)
        
        if "int_parsing" in error_types or "float_parsing" in error_types:
            tips.append("💡 Tip: Make sure numbers don't have quotes: use 42, not \"42\"")
        
        if "string_pattern_mismatch" in error_types:
            if "Email" in type_name:
                tips.append("💡 Tip: Email must be format: user@domain.com")
        
        if "list_type" in error_types:
            tips.append("💡 Tip: Lists use square brackets: [1, 2, 3]")
        
        if "dict_type" in error_types:
            tips.append("💡 Tip: Objects use curly braces: {\"key\": \"value\"}")
        
        if "extra_forbidden" in error_types:
            tips.append("💡 Tip: Remove fields not defined in the schema")
        
        return tips if tips else ["💡 Tip: Check the error messages above for details"]


# === Example: Webhook Validator with TypeAdapter ===

class WebhookValidator:
    """
    Validate arbitrary webhook payloads with TypeAdapter.
    
    🎓 Real-World: GitHub, Stripe, Slack webhooks have dynamic schemas.
    """
    
    # Registry of known webhook schemas
    WEBHOOK_SCHEMAS = {
        "user.created": TypeAdapter(Dict[str, Any]),  # Simplified
        "order.paid": TypeAdapter(Dict[str, Any]),
        "payment.failed": TypeAdapter(Dict[str, Any]),
    }
    
    @classmethod
    def validate_webhook(cls, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate webhook payload against known schema.
        
        🎓 Interactive: Select event type, paste payload, see validation.
        """
        adapter = cls.WEBHOOK_SCHEMAS.get(event_type)
        if not adapter:
            return {
                "valid": False,
                "error": f"Unknown event type: {event_type}",
                "known_events": list(cls.WEBHOOK_SCHEMAS.keys())
            }
        
        try:
            validated = adapter.validate_python(payload)
            return {
                "valid": True,
                "event_type": event_type,
                "validated": validated,
                # In production: route to handler based on event_type
            }
        except ValidationError as e:
            return {
                "valid": False,
                "event_type": event_type,
                "errors": e.errors(include_url=False),
            }