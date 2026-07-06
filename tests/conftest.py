"""
tests/conftest.py
─────────────────────────────────────────────────────────────────────────────
Pytest configuration and shared fixtures.
"""

import os
import uuid
import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set required env vars before ANY app import
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
os.environ.setdefault("ADMIN_API_KEY", "REDACTED_TEST_ADMIN_KEY")

from app.database import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Replace the real DB session with the test SQLite session."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client for the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a raw SQLAlchemy session for database operations in tests."""
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
def admin_headers() -> dict:
    """Authentication headers for admin endpoints."""
    return {"X-Admin-Key": "REDACTED_TEST_ADMIN_KEY"}
