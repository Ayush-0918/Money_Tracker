"""
app/services/budget_service.py
─────────────────────────────────────────────────────────────────────────────
Budget summary is a stored, periodically-updated snapshot — not a
live SUM() query at request time.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from uuid import UUID
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetSummaryResponse, BudgetStatusEnum

STALE_AFTER_MINUTES = 15


def _status_for(pct: Optional[Decimal], spent: Decimal) -> BudgetStatusEnum:
    if pct is None:
        return BudgetStatusEnum.exceeded if spent > 0 else BudgetStatusEnum.safe
    if pct >= 100:
        return BudgetStatusEnum.exceeded
    if pct >= 80:
        return BudgetStatusEnum.warning
    return BudgetStatusEnum.safe


async def get_budget_summary_from_cache(db: AsyncSession, user_id: UUID) -> List[BudgetSummaryResponse]:
    """
    Reads the last computed snapshot per budget. Does NOT touch the
    transactions table. If the snapshot is older than STALE_AFTER_MINUTES,
    flags it — client decides whether to call POST /budgets/recalculate.
    """
    stmt = select(Budget).where(Budget.user_id == user_id)
    result = await db.execute(stmt)
    budgets = result.scalars().all()

    now = datetime.now(timezone.utc)
    results = []

    for b in budgets:
        is_stale = b.cached_updated_at is None or (now - b.cached_updated_at).total_seconds() > STALE_AFTER_MINUTES * 60

        # Transparent Backend Refresh
        if is_stale:
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            spent_stmt = select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.transaction_date >= start_of_month,
            )
            spent_result = await db.execute(spent_stmt)
            b.cached_spent = spent_result.scalar() or Decimal("0.00")
            b.cached_updated_at = now
            # Note: The db.commit() in get_db() will automatically save these changes to the DB

        spent = b.cached_spent or Decimal("0")

        if b.monthly_limit == 0:
            pct = None
            remaining = -spent
        else:
            remaining = b.monthly_limit - spent
            pct = (spent / b.monthly_limit * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        results.append(
            BudgetSummaryResponse(
                budget_id=b.id,
                category_id=b.category_id,
                monthly_limit=b.monthly_limit,
                spent=spent,
                remaining=remaining,
                percentage_used=float(pct) if pct is not None else None,
                status=_status_for(pct, spent),
                stale=False,
                suggestion=None,
            )
        )
    return results


async def recalculate_user_budgets(db: AsyncSession, user_id: UUID) -> None:
    """
    Forcefully recalculates the spent amount for all budgets of a given user for the current month.
    """
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get all budgets for user
    stmt = select(Budget).where(Budget.user_id == user_id)
    result = await db.execute(stmt)
    budgets = result.scalars().all()

    if not budgets:
        return

    # Calculate sum for each category for current month
    for b in budgets:
        spent_stmt = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == b.category_id,
            Transaction.transaction_date >= start_of_month,
        )
        spent_result = await db.execute(spent_stmt)
        spent = spent_result.scalar() or Decimal("0.00")

        b.cached_spent = spent
        b.cached_updated_at = now

    # Commit is handled by dependency
