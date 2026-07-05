"""idempotency_and_logs

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-04 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add missing columns to transactions with "IF NOT EXISTS" logic
    op.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128)")
    op.execute("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'INR' NOT NULL")

    # 2. Add idempotency index and constraint (using raw SQL for IF NOT EXISTS)
    op.execute("CREATE INDEX IF NOT EXISTS ix_transactions_idempotency_key ON transactions (idempotency_key)")

    # Unique constraint naming and check
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_transactions_user_idempotency') THEN
            ALTER TABLE transactions ADD CONSTRAINT uq_transactions_user_idempotency UNIQUE (user_id, idempotency_key);
        END IF;
    END $$;
    """)

    # 3. Create deleted_transactions_log table with "IF NOT EXISTS"
    op.execute("""
    CREATE TABLE IF NOT EXISTS deleted_transactions_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        original_transaction_id UUID NOT NULL,
        user_id UUID NOT NULL,
        amount NUMERIC(10, 2) NOT NULL,
        merchant TEXT NOT NULL,
        transaction_date TIMESTAMPTZ NOT NULL,
        source TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        reason TEXT NOT NULL,
        deleted_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_deleted_transactions_log_original_transaction_id ON deleted_transactions_log (original_transaction_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_deleted_transactions_log_user_id ON deleted_transactions_log (user_id)")


def downgrade():
    # Downgrade is best effort
    op.execute("DROP TABLE IF EXISTS deleted_transactions_log CASCADE")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS uq_transactions_user_idempotency")
    op.execute("DROP INDEX IF EXISTS ix_transactions_idempotency_key")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS currency")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS idempotency_key")
