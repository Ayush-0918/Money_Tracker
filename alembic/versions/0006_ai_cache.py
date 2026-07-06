"""ai_cache

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-06 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

def upgrade():
    # Drop table if it was auto-created by development lifespan metadata.create_all
    op.execute("DROP TABLE IF EXISTS ai_categorization_caches CASCADE")
    
    # 1. Create AI Categorization Cache table
    op.create_table(
        'ai_categorization_caches',
        sa.Column('merchant_name', sa.String(), nullable=False),
        sa.Column('category_name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('merchant_name')
    )

    # 2. Create budget index on category_id
    op.execute("DROP INDEX IF EXISTS idx_budgets_category_id")
    op.create_index('idx_budgets_category_id', 'budgets', ['category_id'])

def downgrade():
    op.drop_index('idx_budgets_category_id', table_name='budgets')
    op.drop_table('ai_categorization_caches')
