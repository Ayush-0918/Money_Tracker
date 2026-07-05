"""
app/models/user.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `users` table.

A User represents a phone-number-identified account that owns transactions
and receives WhatsApp reports. One phone number → one account.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    # Avoid circular imports — only used for type hints
    from app.models.transaction import Transaction
    from app.models.subscription import Subscription


class User(Base, TimestampMixin):
    """
    Represents an application user.

    Attributes:
        id:                  UUID primary key, generated in Python.
        phone_number:        User's WhatsApp-capable phone number (E.164 format
                             recommended, e.g. "+919876543210"). Must be unique.
        name:                Display name for the user.
        language_preference: Two-letter language code for report language
                             (e.g. "en", "hi"). Defaults to "en".
        created_at:          Auto-set UTC creation timestamp (from TimestampMixin).
        transactions:        Lazy-loaded list of all transactions by this user.
        subscriptions:       Lazy-loaded list of all subscriptions by this user.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
        doc="UUID primary key, generated in Python.",
    )
    phone_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="User's phone number — used for WhatsApp report delivery.",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name of the user.",
    )
    language_preference: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
        server_default="en",
        doc="Two-letter language code for report generation (default: 'en').",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.phone_number}>"
