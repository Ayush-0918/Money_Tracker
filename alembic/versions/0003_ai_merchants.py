"""Add AI categorization tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create merchants table
    op.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL UNIQUE,
        parent_merchant_id UUID REFERENCES merchants(id) ON DELETE SET NULL,
        is_verified BOOLEAN DEFAULT false
    )
    """)

    # 2. Create merchant_aliases
    op.execute("""
    CREATE TABLE IF NOT EXISTS merchant_aliases (
        alias TEXT PRIMARY KEY,
        merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_merchant_aliases_merchant_id ON merchant_aliases (merchant_id)")

    # 3. Create merchant_rules
    op.execute("""
    CREATE TABLE IF NOT EXISTS merchant_rules (
        merchant_id UUID PRIMARY KEY REFERENCES merchants(id) ON DELETE CASCADE,
        category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
        confidence_weight INTEGER DEFAULT 80,
        CONSTRAINT chk_confidence_range CHECK (confidence_weight >= 0 AND confidence_weight <= 100)
    )
    """)

    # 4. Create user_overrides
    op.execute("""
    CREATE TABLE IF NOT EXISTS user_overrides (
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
        category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
        correction_count INTEGER DEFAULT 1,
        last_corrected TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (user_id, merchant_id)
    )
    """)

    # 5. Create learning_events
    op.execute("""
    CREATE TABLE IF NOT EXISTS learning_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
        merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
        old_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
        new_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
        feedback_source TEXT,
        processed BOOLEAN DEFAULT false
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_learning_events_transaction_id ON learning_events (transaction_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS learning_events CASCADE")
    op.execute("DROP TABLE IF EXISTS user_overrides CASCADE")
    op.execute("DROP TABLE IF EXISTS merchant_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS merchant_aliases CASCADE")
    op.execute("DROP TABLE IF EXISTS merchants CASCADE")
