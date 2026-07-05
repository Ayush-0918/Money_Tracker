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
    
    return DashboardSummaryDto(
        total_balance=monthly.total_balance_formatted,
        monthly_income=monthly.income_formatted,
        monthly_expense=monthly.total_spend_formatted,
        monthly_savings=monthly.savings_formatted,
        total_transactions=len(monthly.recent_transactions),
        latest_transactions=monthly.recent_transactions,
        top_categories=monthly.categories,
        upcoming_subscriptions=subs,
        weekly_activity=weekly
    )
