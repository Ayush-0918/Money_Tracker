"""
app/api/dashboard.py
─────────────────────────────────────────────────────────────────────────────
Dashboard routes matching Android Home UI.
"""

import uuid
import asyncio
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.report import DashboardSummaryDto
from app.services.report_service import get_monthly_report, get_subscription_report, get_weekly_activity
from app.services.ai_service import ai_service
from app.services.budget_service import get_budget_summary_from_cache
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get(
    "/summary",
    response_model=DashboardSummaryDto,
    status_code=status.HTTP_200_OK,
    summary="Dashboard Summary",
    description="Aggregate data for the Android Home screen. Single source of truth.",
)
async def get_dashboard_summary(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummaryDto:
    logger.info("dashboard: summary requested | user_id=%s", current_user_id)
    
    # Run concurrent queries to reduce latency (Critical for Dashboard P99)
    monthly_task = get_monthly_report(db=db, user_id=current_user_id)
    subs_task = get_subscription_report(db=db, user_id=current_user_id)
    weekly_task = get_weekly_activity(db=db, user_id=current_user_id)

    monthly, subs, weekly = await asyncio.gather(monthly_task, subs_task, weekly_task)

    # AI Analysis (Async)
    # We fetch budget status for saving tips
    budgets = await get_budget_summary_from_cache(db=db, user_id=current_user_id)

    # Prepare data for AI
    transaction_list = [
        {"merchant": t.merchant, "amount": t.amount_formatted, "category": t.category}
        for t in monthly.recent_transactions
    ]
    budget_list = [
        {"category": b.category_id, "limit": b.monthly_limit, "spent": b.spent}
        for b in budgets
    ]

    ai_insights_task = ai_service.get_spending_insights(transaction_list)
    saving_tips_task = ai_service.get_saving_tips({"budgets": budget_list})

    ai_insights, saving_tips = await asyncio.gather(ai_insights_task, saving_tips_task)

    return DashboardSummaryDto(
        total_balance=monthly.total_balance_formatted,
        monthly_income=monthly.income_formatted,
        monthly_expense=monthly.total_spend_formatted,
        monthly_savings=monthly.savings_formatted,
        total_transactions=len(monthly.recent_transactions),
        latest_transactions=monthly.recent_transactions,
        top_categories=monthly.categories,
        upcoming_subscriptions=subs,
        weekly_activity=weekly,
        budgets=budgets,
        ai_insights=ai_insights,
        saving_tips=saving_tips
    )
