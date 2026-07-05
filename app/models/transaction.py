"""
app/models/transaction.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `transactions` table.

IMPORTANT — Money Precision:
    Amount is stored as NUMERIC(12, 2), NOT Float. Floating-point arithmetic
    is lossy and unsuitable for financial data. SQLAlchemy maps this to
    Python's `decimal.Decimal`, which is exact.

Source Enum:
    Tracks whether the notification came from an SMS or a push notification.

Idempotency / Duplicate Prevention:
    The `idempotency_key` column (unique per user) prevents duplicate
    transactions from Android network retries or app restarts.
    The Android client generates this key as:
        SHA256(user_id + raw_text + approximate_timestamp_hour)
    If the same key is submitted twice, the service returns the EXISTING
    transaction instead of inserting a duplicate (HTTP 200, not 201).
    The key is nullable for backwards-compatibility with clients that
    don't yet send it.

Currency:
    INR only in Phase 1-2. `currency` column added for future multi-currency
    support (Phase 3+). Always 'INR' for now.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category

# Valid values for the `source` column. Using a Python Literal + CHECK constraint
# instead of a PostgreSQL ENUM type makes the DB schema more portable.
SOURCE_VALUES = ("sms", "notification")


class Transaction(Base, TimestampMixin):
    """
    Records a single financial transaction parsed from an Android notification.

    Attributes:
        id:               UUID primary key.
        user_id:          Foreign key → users.id (owner of this transaction).
        amount:           Exact decimal amount (NUMERIC 12,2). Never a float.
        merchant:         Name of the merchant/payee as extracted from the text.
        category:         Spending category. NULL until Phase 3 AI categorizer
                          assigns it. Do not remove this field — it is intentional.
        transaction_date: When the transaction occurred (parsed from text or
                          defaults to insertion time).
        source:           Origin of the notification ('sms' | 'notification').
        is_recurring:     True if detected as a recurring subscription charge.
        raw_text:         Original notification text — stored ONLY after OTP
                          filter passes. Used for debugging parser failures.
        created_at:       Auto-set UTC creation timestamp (from TimestampMixin).
        user:             Relationship back to the owning User.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        # Prevent duplicate transactions from Android retries.
        UniqueConstraint(
            "user_id", "idempotency_key",
            name="uq_transactions_user_idempotency",
        ),
        # Composite index for fast budget calculations per month
        Index("idx_tx_user_date_cat", "user_id", "transaction_date", "category_id", "amount"),
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
        doc="Owner of this transaction.",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
        doc="Transaction amount. NUMERIC(12,2) — never Float.",
    )
    merchant: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Merchant/payee name extracted from notification text.",
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc=(
            "Spending category (e.g., 'Food', 'Transport'). "
            "NULL until Phase 3 AI categorizer runs. Intentionally deferred. "
            "Will be deprecated in favor of category_id."
        ),
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
        index=True,
    )
    transaction_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        doc="When the transaction occurred. Parsed from text; defaults to now().",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Origin of notification: 'sms' or 'notification'.",
    )
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="True if recurring-detection logic flagged this as a subscription.",
    )
    raw_text: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
        doc=(
            "Original notification text — stored ONLY after OTP filter passes. "
            "Useful for debugging parsing failures. Never store OTP messages."
        ),
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc=(
            "Client-generated deduplication key (SHA256 of user_id+raw_text+hour). "
            "Prevents duplicate inserts from Android network retries. "
            "Nullable for backwards-compatibility with older app versions."
        ),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        server_default="INR",
        doc=(
            "ISO 4217 currency code. Always 'INR' in Phase 1-2. "
            "Multi-currency support planned for Phase 3."
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    category_rel: Mapped[Optional["Category"]] = relationship("Category")

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} merchant={self.merchant!r} "
            f"amount={self.amount} user_id={self.user_id}>"
        )
