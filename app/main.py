"""
🎓 Application Entry Point & Integration Hub
Connects: Middleware → Exception Handlers → Routes → Settings
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# ✅ Import middleware CLASS (not function)
from app.middleware.request_id import RequestIDMiddleware
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.routes.pydantic_lab import router as lab_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup & shutdown hooks."""
    # Startup
    print(f"🚀 Starting {settings.api_title} v{settings.api_version} | Env: {settings.environment}")
    settings.database.data_path.parent.mkdir(parents=True, exist_ok=True)
    settings.database.backup_path.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    print("🛑 Shutting down application...")


# Initialize FastAPI
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="🎓 Pydantic v2 Mastery Lab: Interactive validation, serialization, and dynamic schemas",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 1️⃣ Attach settings globally
app.state.settings = settings

# 2️⃣ Add CORS
app.add_middleware(
    CORSMiddleware,
    **settings.get_cors_config()
)

# ✅ 3️⃣ Add Request ID middleware (CLASS, not decorator)
app.add_middleware(RequestIDMiddleware)

# 4️⃣ Register exception handlers
setup_exception_handlers(app)

# 5️⃣ Mount routes
app.include_router(lab_router, prefix="/api")

# 6️⃣ Root endpoint
@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "running",
        "service": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "lab": "/api/lab/",
        "health": "/api/lab/health"
    }