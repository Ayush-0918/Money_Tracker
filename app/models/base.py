"""
app/models/base.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy declarative base and shared mixins used by all ORM models.

Every table in Money Tracker inherits from Base (for SQLAlchemy metadata
registration) and optionally TimestampMixin (for automatic created_at).
"""

import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Central SQLAlchemy declarative base.

    All ORM model classes must inherit from this Base so that
    Alembic can discover them for auto-generated migrations.
    """


class TimestampMixin:
    """
    Mixin that adds an auto-populated `created_at` column to any model.

    Uses the database server's current timestamp (server_default) rather than
    Python time to avoid timezone inconsistencies between application servers.
    """

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when this record was created (set by DB server).",
    )


def new_uuid() -> uuid.UUID:
    """
    Generate a new random UUID v4.

    Used as the default factory for primary key columns across all models,
    ensuring IDs are created in Python (not DB) for predictability in tests.
    """
    return uuid.uuid4()
