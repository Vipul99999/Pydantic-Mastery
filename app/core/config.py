"""
🎓 Pydantic Settings & Configuration Management

Demonstrates:
- Environment-specific configuration (dev/test/prod)
- Secret management with SecretStr
- Path/URL validation with Pydantic custom types
- Cross-field validation with @model_validator
- Default factories & dynamic field resolution
- Settings validation for production readiness

🎓 INTERACTIVE LEARNING READY:
- /lab/config/schema: Export settings as JSON Schema
- /lab/config/validate: Test environment config validation
- Frontend can read env constraints to generate config forms
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import (
    Field, field_validator, model_validator, 
    SecretStr, HttpUrl, DirectoryPath, ValidationError
)
from typing import List, Optional, Literal, Self
from pathlib import Path
from enum import StrEnum
import os


class Environment(StrEnum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class DatabaseConfig(BaseSettings):
    """Database & file storage configuration."""
    
    data_path: Path = Field(
        default=Path("data/data.json"),
        description="Primary JSON data store path"
    )
    backup_path: Path = Field(
        default=Path("data/backups"),
        description="Backup directory path"
    )
    auto_backup: bool = Field(default=True, description="Enable automatic backups on write")
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="Max JSON file size in MB")
    
    @field_validator("data_path", "backup_path")
    @classmethod
    def resolve_absolute_paths(cls, v: Path) -> Path:
        """Convert to absolute path and ensure parent directory exists."""
        abs_path = v.resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return abs_path
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=False,
        extra="ignore"
    )


class SecurityConfig(BaseSettings):
    """Security & authentication settings."""
    
    api_secret: Optional[SecretStr] = Field(default=None, description="Internal API secret key")
    jwt_secret: Optional[SecretStr] = Field(default=None, description="JWT signing secret")
    cors_max_age: int = Field(default=3600, ge=0, le=86400, description="CORS preflight cache duration")
    rate_limit_enabled: bool = Field(default=False, description="Enable request rate limiting")
    rate_limit_requests: int = Field(default=100, ge=1, description="Max requests per window")
    
    model_config = SettingsConfigDict(
        env_prefix="SEC_",
        case_sensitive=False,
        extra="ignore"
    )


class AppSettings(BaseSettings):
    """
    🎓 Master Application Configuration
    
    Demonstrates advanced Pydantic v2 settings patterns:
    - Environment-aware defaults
    - Custom type validation (HttpUrl, Path, SecretStr)
    - Cross-field business rules
    - Strict production validation
    """
    
    # === Core Identity ===
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    api_title: str = Field(default="Pydantic Mastery API")
    api_version: str = Field(default="2.0.0", pattern=r"^\d+\.\d+\.\d+$")
    debug: bool = Field(default=False)
    
    # === Server ===
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, le=8, description="Uvicorn workers")
    
    # === CORS & Network ===
    allowed_origins: List[HttpUrl] = Field(
        default_factory=lambda: [HttpUrl("http://localhost:3000"), HttpUrl("http://localhost:8080")],
        description="Allowed CORS origins"
    )
    trusted_proxies: List[str] = Field(default_factory=list, description="Trusted reverse proxy IPs")
    
    # === Logging ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_format: Literal["json", "text"] = Field(default="text", description="Log output format")
    
    # === Nested Configs ===
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # === Validators ===
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins_env(cls, v) -> List[HttpUrl]:
        """
        Parse comma-separated or JSON array from environment variables.
        Handles: ALLOWED_ORIGINS="http://localhost:3000,https://app.example.com"
        """
        if isinstance(v, str):
            try:
                # Try parsing as JSON array first
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [HttpUrl(u) for u in parsed if isinstance(u, str)]
            except json.JSONDecodeError:
                pass
            # Fallback to comma-separated
            return [HttpUrl(u.strip()) for u in v.split(",") if u.strip()]
        return v
    
    @field_validator("api_version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Ensure semantic versioning format."""
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("API version must follow semver: X.Y.Z")
        return v
    
    @model_validator(mode="after")
    def apply_environment_overrides(self) -> Self:
        """
        Apply environment-specific configuration overrides.
        
        Production rules:
        - debug must be False
        - secrets are required
        - localhost origins blocked
        """
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode cannot be enabled in production")
            if not self.security.api_secret or not self.security.api_secret.get_secret_value():
                raise ValueError("SEC_API_SECRET is required in production")
            # Block localhost in production CORS
            self.allowed_origins = [
                url for url in self.allowed_origins
                if "localhost" not in str(url) and "127.0.0.1" not in str(url)
            ]
        elif self.environment == Environment.TESTING:
            # Testing defaults
            self.log_level = "WARNING"
            self.rate_limit_enabled = False
            
        return self
    
    @model_validator(mode="before")
    @classmethod
    def load_dotenv_paths(cls, values: dict) -> dict:
        """
        Auto-resolve .env file paths relative to project root.
        """
        if "env_file" not in values:
            project_root = Path(__file__).resolve().parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                values["env_file"] = str(env_file)
        return values
    
    # === Pydantic Settings Config ===
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=False  # Allow runtime updates if needed
    )
    
    # === Helper Methods ===
    
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION
    
    def to_safe_dict(self) -> dict:
        """Serialize settings with secrets masked (for logging/admin UI)."""
        data = self.model_dump(mode="json")
        # Mask secrets
        if data.get("security", {}).get("api_secret"):
            data["security"]["api_secret"] = "********"
        if data.get("security", {}).get("jwt_secret"):
            data["security"]["jwt_secret"] = "********"
        return data
    
    def get_cors_config(self) -> dict:
        """Generate FastAPI CORS middleware config."""
        return {
            "allow_origins": [str(url) for url in self.allowed_origins],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "max_age": self.security.cors_max_age,
        }


# === Singleton Instance ===
settings = AppSettings()