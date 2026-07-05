"""
alembic/versions/0001_initial_schema.py
─────────────────────────────────────────────────────────────────────────────
Initial database schema migration.

Creates tables: users, transactions, subscriptions.
Includes all indexes and constraints defined in the ORM models.

If you prefer using supabase_setup.sql directly in the Supabase Dashboard,
you can skip running this migration. Both produce identical schemas.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Alembic metadata
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and constraints."""

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("language_preference", sa.String(5), server_default="en", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
        sa.CheckConstraint("char_length(phone_number) >= 7", name="chk_phone_length"),
    )
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)

    # ── transactions ──────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("merchant", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "transaction_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("is_recurring", sa.Boolean, server_default="false", nullable=False),
        sa.Column("raw_text", sa.String(2000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="chk_txn_amount_positive"),
        sa.CheckConstraint("source IN ('sms', 'notification')", name="chk_source_values"),
    )
    op.create_index("idx_transactions_user_date", "transactions", ["user_id", "transaction_date"])
    op.create_index("idx_transactions_merchant", "transactions", ["user_id", "merchant"])

    # ── subscriptions ─────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merchant", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("billing_cycle", sa.String(20), server_default="monthly", nullable=False),
        sa.Column("next_billing_date", sa.Date, nullable=True),
        sa.Column("last_used_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "merchant", name="uq_subscriptions_user_merchant"),
        sa.CheckConstraint("amount > 0", name="chk_sub_amount_positive"),
        sa.CheckConstraint(
            "billing_cycle IN ('monthly', 'weekly', 'yearly')",
            name="chk_billing_cycle",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'cancelled')",
            name="chk_status",
        ),
    )
    op.create_index("idx_subscriptions_user_status", "subscriptions", ["user_id", "status"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_index("idx_subscriptions_user_status", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("idx_transactions_merchant", table_name="transactions")
    op.drop_index("idx_transactions_user_date", table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("ix_users_phone_number", table_name="users")
    op.drop_table("users")
