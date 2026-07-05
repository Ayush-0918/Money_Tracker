"""categories_budgets

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-04 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create categories table
    op.execute("""
    create table if not exists categories (
        id uuid primary key default gen_random_uuid(),
        name text not null,
        slug text not null unique,
        display_name text not null,
        icon text,
        color text,
        sort_order integer not null default 0,
        system boolean not null default false,
        parent_category_id uuid references categories(id) on delete restrict,
        user_id uuid references users(id) on delete cascade,
        created_at timestamptz not null default now(),

        constraint chk_categories_name_not_blank check (length(trim(name)) > 0)
    )
    """)

    op.execute("""
    create unique index if not exists ux_categories_system_name
        on categories (lower(name))
        where system = true
    """)

    op.execute("""
    create unique index if not exists ux_categories_user_name
        on categories (user_id, lower(name))
        where system = false
    """)

    op.execute("create index if not exists ix_categories_user_id on categories (user_id)")

    # 2. Seed system categories
    op.execute("""
    insert into categories (name, slug, display_name, icon, color, sort_order, system) values
        ('food', 'food-dining', 'Food & Dining', 'restaurant', '#4CAF7D', 10, true),
        ('shopping', 'shopping', 'Shopping', 'shopping_bag', '#90CAF9', 20, true),
        ('bills', 'bills-utilities', 'Bills & Utilities', 'receipt', '#F5A623', 30, true),
        ('transport', 'transport', 'Transport', 'directions_car', '#B36B00', 40, true),
        ('entertainment', 'entertainment', 'Entertainment', 'movie', '#1E3A5F', 50, true)
    on conflict do nothing
    """)

    # 3. Add category_id to transactions and backfill
    op.execute("alter table transactions add column if not exists category_id uuid references categories(id)")

    op.execute("""
    update transactions t
    set category_id = c.id
    from (
        values
            ('food', 'food'),
            ('dining', 'food'),
            ('restaurant', 'food'),
            ('restaurants', 'food'),
            ('food & dining', 'food'),
            ('shopping', 'shopping'),
            ('bills', 'bills'),
            ('transport', 'transport'),
            ('entertainment', 'entertainment')
    ) as mapping(synonym, target_name)
    join categories c on c.name = mapping.target_name and c.system = true
    where lower(trim(t.category)) = mapping.synonym
    """)

    op.execute("create index if not exists ix_transactions_category_id on transactions (category_id)")

    # 4. Create budgets table
    op.execute("""
    create table if not exists budgets (
        id uuid primary key default gen_random_uuid(),
        user_id uuid not null references users(id) on delete cascade,
        category_id uuid not null references categories(id),
        monthly_limit numeric(12, 2) not null check (monthly_limit > 0),
        cached_spent numeric(12, 2),
        cached_updated_at timestamptz,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        constraint uq_budget_user_category_id unique (user_id, category_id)
    )
    """)
    op.execute("create index if not exists ix_budgets_user_id on budgets(user_id)")


def downgrade():
    op.execute("drop table if exists budgets cascade")
    op.execute("alter table transactions drop column if exists category_id cascade")
    op.execute("drop table if exists categories cascade")
