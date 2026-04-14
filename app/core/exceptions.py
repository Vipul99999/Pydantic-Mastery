"""
🎓 Production-Grade Exception Handling & Structured Errors

✅ Exports: setup_exception_handlers(), format_validation_error()
✅ Uses request.state.request_id from middleware
✅ Secure: No stack traces in production responses
"""

from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Dict, Any, List, Optional
import logging
import uuid
import traceback

logger = logging.getLogger(__name__)


# =============================================================================
# 📦 Custom Exception Classes
# =============================================================================

class AppBaseException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"{self.__class__.__name__.replace('Exception', '')}_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppBaseException):
    """Raised when Pydantic validation fails."""
    def __init__(self, errors: List[Dict], message: str = "Validation failed"):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details={"field_errors": errors})


class ResourceNotFoundException(AppBaseException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


# =============================================================================
# 🎯 Exception Handlers
# =============================================================================

def setup_exception_handlers(app) -> None:
    """Register all exception handlers with FastAPI."""
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with structured, frontend-ready format."""
        request_id = _get_request_id(request)
        errors = exc.errors(include_url=False, include_input=False)
        
        # Build field-path → messages mapping
        field_errors: Dict[str, List[str]] = {}
        for error in errors:
            path = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            field_errors.setdefault(path, []).append(error["msg"])
        
        logger.warning(f"[{request_id}] Validation failed: {field_errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed. Please correct the highlighted fields.",
                    "request_id": request_id,
                    "details": {
                        "field_errors": field_errors,
                        "total_errors": len(errors),
                        "model": exc.title or "unknown",
                    },
                    "playground": {
                        "highlight_fields": list(field_errors.keys()),
                        "tips": _generate_validation_tips(errors),
                        "schema_endpoint": f"/api/lab/playground/schema/{exc.title.lower().replace(' ', '_') if exc.title else 'unknown'}"
                    }
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Standardize FastAPI HTTP exceptions."""
        request_id = _get_request_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "request_id": request_id,
                    "details": {
                        "path": request.url.path,
                        "method": request.method,
                        "status": exc.status_code
                    }
                }
            }
        )
    
    @app.exception_handler(AppBaseException)
    async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
        """Handle custom application exceptions."""
        request_id = _get_request_id(request)
        logger.error(f"[{request_id}] App exception: {exc.message} | Code: {exc.error_code}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "app_error",
                    "code": exc.error_code,
                    "message": exc.message,
                    "request_id": request_id,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unexpected errors - secure production handling."""
        request_id = _get_request_id(request)
        is_prod = getattr(request.app.state, "settings", None) and request.app.state.settings.environment.value == "production"
        
        # Log full traceback internally
        logger.critical(f"[{request_id}] Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
        
        # Build safe response
        error_response = {
            "error": {
                "type": "internal_error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
                "details": {}
            }
        }
        
        # Development: include minimal debug info
        if not is_prod:
            error_response["error"]["details"]["exception_type"] = type(exc).__name__
            error_response["error"]["details"]["traceback_summary"] = traceback.format_exception_only(type(exc), exc)[-1]
            
        return JSONResponse(status_code=500, content=error_response)


# =============================================================================
# 🛠️ Utility Functions (✅ EXPORTED)
# =============================================================================

def _get_request_id(request: Request) -> str:
    """Extract or generate request ID for correlation."""
    header_id = request.headers.get("X-Request-ID")
    if header_id and len(header_id) <= 64:
        return header_id
    return getattr(request.state, "request_id", str(uuid.uuid4())[:8])


def _generate_validation_tips(errors: List[Dict]) -> List[str]:
    """Generate human-readable tips from Pydantic validation errors."""
    tips = []
    error_types = {e["type"] for e in errors}
    
    tip_map = {
        "int_parsing": "💡 Ensure numbers are not quoted: use `42` not `\"42\"`",
        "float_parsing": "💡 Remove quotes around decimal numbers",
        "string_too_short": "💡 Increase string length to meet minimum requirement",
        "string_too_long": "💡 Reduce string length to meet maximum requirement",
        "string_pattern_mismatch": "💡 Check regex pattern or input format",
        "value_error": "💡 Value violates custom validation rule",
        "missing": "💡 This field is required and must be provided",
        "extra_forbidden": "💡 Remove fields not defined in the model schema",
        "literal_error": "💡 Value must exactly match one of the allowed literals",
        "enum": "💡 Select a value from the allowed enum options",
    }
    
    for err_type in error_types:
        if err_type in tip_map:
            tips.append(tip_map[err_type])
            
    if not tips:
        tips.append("💡 Review the error messages and adjust your input accordingly")
        
    return list(dict.fromkeys(tips))


# ✅ EXPORTED: Format Pydantic error for frontend consumption
def format_validation_error(
    exc: ValidationError, 
    include_raw: bool = False
) -> Dict[str, Any]:
    """
    Format Pydantic error for frontend consumption.
    🎓 Used in playground responses and React/Vue error boundaries.
    """
    errors = []
    for error in exc.errors(include_url=False):
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input") if include_raw else None
        })
    
    return {
        "valid": False,
        "error_count": len(errors),
        "errors": errors,
        "model": exc.title if hasattr(exc, "title") else "unknown",
        "tips": _generate_validation_tips(errors)
    }


# ✅ Ensure __all__ exports the public API
__all__ = [
    "setup_exception_handlers",
    "format_validation_error",
    "AppBaseException",
    "ValidationException",
    "ResourceNotFoundException",
]