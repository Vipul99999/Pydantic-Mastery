"""
🎓 Request ID Middleware (Starlette BaseHTTPMiddleware pattern)

✅ No reference to `app` at module level
✅ Reusable across any FastAPI/Starlette app
✅ Async-safe with proper type hints
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject correlation IDs into requests/responses.
    
    Behavior:
    - If client sends `X-Request-ID` header (≤64 chars): use it
    - Otherwise: generate short UUID (8 hex chars)
    - Attach to request.state for exception handlers/logging
    - Add to response headers for debugging/tracing
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate request ID
        header_id = request.headers.get("X-Request-ID")
        request_id = header_id if (header_id and len(header_id) <= 64) else str(uuid.uuid4())[:8]
        
        # Attach to request state for exception handlers & logging
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response