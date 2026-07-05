"""db_hardening

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Hardened Composite Index for Dashboard (Covering Index)
    # Optimized for: select amount, merchant from transactions where user_id = ? order by date desc
    # This reduces IO by including necessary columns in the index itself.
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_transactions_dashboard_optimized
    ON transactions (user_id, transaction_date DESC)
    INCLUDE (amount, merchant, category_id);
    """)

    # 2. Hardened Foreign Keys for Categories (Restrict deletion of active categories)
    # We prevent categories from being deleted if they are currently linked to budgets or rules.
    op.execute("ALTER TABLE budgets DROP CONSTRAINT IF EXISTS budgets_category_id_fkey")
    op.execute("""
    ALTER TABLE budgets
    ADD CONSTRAINT budgets_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    """)

    op.execute("ALTER TABLE merchant_rules DROP CONSTRAINT IF EXISTS merchant_rules_category_id_fkey")
    op.execute("""
    ALTER TABLE merchant_rules
    ADD CONSTRAINT merchant_rules_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
    """)

def downgrade():
    op.drop_index('idx_transactions_dashboard_optimized', table_name='transactions')

    # Budgets FK Revert
    op.execute("ALTER TABLE budgets DROP CONSTRAINT IF EXISTS budgets_category_id_fkey")
    op.execute("""
    ALTER TABLE budgets
    ADD CONSTRAINT budgets_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id);
    """)

    # Merchant Rules FK Revert
    op.execute("ALTER TABLE merchant_rules DROP CONSTRAINT IF EXISTS merchant_rules_category_id_fkey")
    op.execute("""
    ALTER TABLE merchant_rules
    ADD CONSTRAINT merchant_rules_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id);
    """)
