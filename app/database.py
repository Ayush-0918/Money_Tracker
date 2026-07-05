"""
app/database.py
─────────────────────────────────────────────────────────────────────────────
Async SQLAlchemy database engine, session factory, and dependency provider.

We use SQLAlchemy 2.x with the async interface (create_async_engine +
AsyncSession) to avoid blocking the FastAPI event loop on every DB call.

The async driver used is asyncpg — specified in DATABASE_URL as:
    postgresql+asyncpg://<user>:<pass>@<host>/<db>

Usage (in routes via FastAPI dependency injection):
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# pool_pre_ping=True: Reconnect automatically if a connection drops (e.g., after
#   Supabase's idle timeout). Critical for long-running services.
# echo=False in production to avoid logging every SQL statement.
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.ENVIRONMENT == "development",
}

if "sqlite" in settings.DATABASE_URL:
    from sqlalchemy.pool import StaticPool
    engine_kwargs["poolclass"] = StaticPool
    # SQLite in-memory databases need check_same_thread=False (handled by aiosqlite natively)
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# ── Session Factory ───────────────────────────────────────────────────────────
# expire_on_commit=False: Keep ORM objects usable after commit without
#   triggering additional DB round-trips (important for async).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    The session is automatically committed on success and rolled back on
    any exception, then closed regardless of outcome.

    Yields:
        AsyncSession: A SQLAlchemy async session bound to the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
