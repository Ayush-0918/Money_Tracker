"""
alembic/env.py
─────────────────────────────────────────────────────────────────────────────
Alembic migration environment configuration.

Reads the DATABASE_URL from app.config (which reads from .env) so the
connection string is NEVER hardcoded in alembic.ini.

Configured for async SQLAlchemy (asyncpg driver). Alembic itself runs
synchronously, so we use run_sync to bridge async/sync.

Usage:
    # Apply all pending migrations
    alembic upgrade head

    # Create a new migration (auto-detect model changes)
    alembic revision --autogenerate -m "describe_your_change"

    # Rollback one migration
    alembic downgrade -1
"""

import asyncio
import os
import sys
from logging.config import fileConfig

# Add the project root directory to sys.path so Alembic can find the 'app' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Alembic can detect them for autogenerate
from app.config import settings
from app.models import Base  # noqa: F401 — registers all models

# Alembic Config object — gives access to alembic.ini values
config = context.config

# Override sqlalchemy.url with the value from .env (never hardcoded)
url = settings.DATABASE_URL
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Escape '%' for configparser interpolation
config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate comparison
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode (generate SQL scripts without a DB connection).

    Useful for reviewing migration SQL before applying it to production.
    Run with: alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure and run migrations with an active DB connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode with an async engine.

    Creates an async engine, obtains a sync connection via run_sync,
    and runs migrations within a transaction.
    """
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,  # Use NullPool for migrations (single-use)
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
