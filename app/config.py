"""
app/config.py
─────────────────────────────────────────────────────────────────────────────
Application configuration using Pydantic BaseSettings.

All values are read from environment variables (or a .env file at project
root).  This is the SINGLE source of truth for configuration — no secrets
are ever hardcoded elsewhere in the codebase.

Usage:
    from app.config import settings
    print(settings.DATABASE_URL)
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings loaded from environment variables / .env file.

    All fields are validated by Pydantic on startup; the application will
    refuse to start if required values are missing or malformed.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        ...,
        description="Async PostgreSQL connection URL (postgresql+asyncpg://...)",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Strong secret key for signing JWTs. Min 32 chars.",
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(
        default=10080,
        gt=0,
        description="Token validity in minutes (default: 7 days).",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins.",
    )

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=20,
        gt=0,
        description="Max POST /transactions calls per user per minute.",
    )

    # ── Environment ───────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "production"] = Field(
        default="development"
    )

    # ── Admin Auth ────────────────────────────────────────────────────────────
    ADMIN_API_KEY: str = Field(
        ...,
        min_length=16,
        description="Secure key for accessing admin-only endpoints.",
    )

    # ── Azure OpenAI ──────────────────────────────────────────────────────────
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default="gpt-4o")

    # ── GitHub Models ─────────────────────────────────────────────────────────
    GITHUB_TOKEN: Optional[str] = Field(default=None)
    GITHUB_MODEL: str = Field(default="openai/gpt-5")
    GITHUB_MODELS_ENDPOINT: str = Field(default="https://models.github.ai/inference")

    # ── Groq AI Provider ──────────────────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    GROQ_API_URL: str = Field(default="https://api.groq.com/openai/v1")

    AI_ENABLED: bool = Field(default=True)
    AI_TIMEOUT_GROQ: float = Field(default=10.0, gt=0.0)
    AI_TIMEOUT_GITHUB: float = Field(default=10.0, gt=0.0)

    # ── DevOps & Monitoring ──────────────────────────────────────────────────
    SENTRY_DSN: Optional[str] = Field(default=None)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def secret_must_not_be_placeholder(cls, v: str) -> str:
        """Prevent deploying with the example placeholder secret."""
        if "CHANGE_ME" in v or "change_me" in v.lower():
            raise ValueError(
                "JWT_SECRET_KEY is still set to the example placeholder. "
                "Generate a real secret with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a Python list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Return the application settings singleton.

    Uses lru_cache so the .env file is read only once per process lifetime.
    In tests, call get_settings.cache_clear() before overriding env vars.
    """
    return Settings()


# Module-level alias for convenience
settings: Settings = get_settings()
