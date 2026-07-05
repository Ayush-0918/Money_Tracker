"""
app/models/subscription.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `subscriptions` table.

A Subscription is auto-created (or updated) when the recurring-detection
service identifies that a merchant charges the user on a regular cycle.
Users can also manually pause or cancel subscriptions.

Unique Constraint:
    (user_id, merchant) — one subscription record per merchant per user.
    New recurring transactions update the existing record rather than
    creating duplicates.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User

# Allowed values for billing_cycle and status columns.
BILLING_CYCLE_VALUES = ("monthly", "weekly", "yearly")
STATUS_VALUES = ("active", "paused", "cancelled")


class Subscription(Base, TimestampMixin):
    """
    Tracks a detected recurring subscription for a user.

    Attributes:
        id:                     UUID primary key.
        user_id:                Foreign key → users.id.
        merchant:               Name of the subscription provider (e.g., "Netflix").
        amount:                 Expected charge amount (NUMERIC 12,2).
        billing_cycle:          How often the charge recurs: 'monthly', 'weekly',
                                or 'yearly'.
        next_billing_date:      Estimated next charge date (nullable — inferred
                                from last transaction + billing cycle).
        last_used_confirmed_at: Timestamp when the user last confirmed they still
                                actively use this subscription. If older than 60
                                days, the subscription is flagged as "unused" in
                                reports.
        status:                 'active' | 'paused' | 'cancelled'.
        created_at:             Auto-set UTC creation timestamp.
        user:                   Relationship back to the owning User.
    """

    __tablename__ = "subscriptions"

    __table_args__ = (
        UniqueConstraint("user_id", "merchant", name="uq_subscriptions_user_merchant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=new_uuid,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    merchant: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Subscription provider name (matched from transaction merchant).",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        doc="Expected recurring charge amount. NUMERIC(12,2) — never Float.",
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        doc="Charge frequency: 'monthly' | 'weekly' | 'yearly'.",
    )
    next_billing_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc=(
            "Estimated next charge date. Inferred as last_transaction_date + "
            "billing_cycle_days. Null if insufficient data."
        ),
    )
    last_used_confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc=(
            "When the user last confirmed they still actively use this service. "
            "If > 60 days old (or null), flagged as 'unused' in reports."
        ),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        doc="Subscription state: 'active' | 'paused' | 'cancelled'.",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")

    def __repr__(self) -> str:
        return (
            f"<Subscription id={self.id} merchant={self.merchant!r} "
            f"status={self.status} user_id={self.user_id}>"
        )
