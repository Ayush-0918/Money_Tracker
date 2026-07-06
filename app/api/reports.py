"""
app/api/reports.py
─────────────────────────────────────────────────────────────────────────────
Report generation routes matching Android DTOs.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user_id, get_db
from app.models.user import User
from app.schemas.report import MonthlyReportDto, SubscriptionDto, WeeklyActivityDto
from app.services.report_service import get_monthly_report, get_subscription_report, get_weekly_activity
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _verify_user_owns_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own reports.",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )


@router.get(
    "/monthly/{user_id}",
    response_model=MonthlyReportDto,
    status_code=status.HTTP_200_OK,
)
async def monthly_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MonthlyReportDto:
    await _verify_user_owns_report(user_id, current_user_id, db)
    logger.info("reports: monthly report requested | user_id=%s", user_id)
    return await get_monthly_report(db=db, user_id=user_id)


@router.get(
    "/subscriptions/{user_id}",
    response_model=List[SubscriptionDto],
    status_code=status.HTTP_200_OK,
)
async def subscription_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionDto]:
    await _verify_user_owns_report(user_id, current_user_id, db)
    logger.info("reports: subscription report requested | user_id=%s", user_id)
    return await get_subscription_report(db=db, user_id=user_id)


@router.get(
    "/weekly/{user_id}",
    response_model=WeeklyActivityDto,
    status_code=status.HTTP_200_OK,
)
async def weekly_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeeklyActivityDto:
    await _verify_user_owns_report(user_id, current_user_id, db)
    logger.info("reports: weekly report requested | user_id=%s", user_id)
    return await get_weekly_activity(db=db, user_id=user_id)


from app.schemas.report import CoachReportDto
from app.services.report_service import get_coach_report


@router.get(
    "/coach/{user_id}",
    response_model=CoachReportDto,
    status_code=status.HTTP_200_OK,
)
async def coach_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CoachReportDto:
    await _verify_user_owns_report(user_id, current_user_id, db)
    logger.info("reports: coach report requested | user_id=%s", user_id)
    return await get_coach_report(db=db, user_id=user_id)
