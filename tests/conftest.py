"""
tests/conftest.py
─────────────────────────────────────────────────────────────────────────────
Pytest configuration and shared fixtures.

Sets required environment variables BEFORE any app module is imported.
This prevents Pydantic Settings from raising ValidationError during test
collection (since there's no .env file in the test environment).

Must be at the tests/ directory root so pytest loads it first.
"""

import os

# ── Set required env vars before ANY app import ───────────────────────────────
# These are ONLY used during testing — never in production.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-minimum-32-characters-long-for-tests",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "100")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key-16-chars-min")
