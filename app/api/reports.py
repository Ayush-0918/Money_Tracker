"""
app/api/reports.py
─────────────────────────────────────────────────────────────────────────────
Report generation routes matching Android DTOs.
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.api.deps import get_current_user_id, get_db
from app.models.user import User
from app.schemas.report import MonthlyReportDto, SubscriptionDto, WeeklyActivityDto, WeeklyReportDto
from app.schemas.report import CoachReportDto
from app.services.report_service import get_monthly_report, get_subscription_report, get_weekly_activity, get_coach_report
from app.services.weekly_report_service import generate_weekly_report
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])

# ── Redis cache helper ────────────────────────────────────────────────────────
try:
    import redis.asyncio as aioredis
    from app.config import settings as _cfg

    _redis: Optional[aioredis.Redis] = aioredis.from_url(_cfg.REDIS_URL, decode_responses=True) if _cfg.REDIS_URL else None
except Exception:
    _redis = None

_WEEKLY_REPORT_TTL = 3600  # 60 minutes


async def _get_cached_weekly_report(user_id: uuid.UUID) -> Optional[WeeklyReportDto]:
    if _redis is None:
        return None
    try:
        key = f"weekly_report:{user_id}"
        raw = await _redis.get(key)
        if raw:
            return WeeklyReportDto(**json.loads(raw))
    except Exception as e:
        logger.warning("Redis weekly report cache read failed: %s", e)
    return None


async def _set_cached_weekly_report(user_id: uuid.UUID, report: WeeklyReportDto) -> None:
    if _redis is None:
        return
    try:
        key = f"weekly_report:{user_id}"
        await _redis.setex(key, _WEEKLY_REPORT_TTL, report.model_dump_json())
    except Exception as e:
        logger.warning("Redis weekly report cache write failed: %s", e)


# ─────────────────────────────────────────────────────────────────────────────


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


@router.get(
    "/weekly-report/{user_id}",
    response_model=WeeklyReportDto,
    status_code=status.HTTP_200_OK,
    summary="AI Weekly Financial Report",
    description=(
        "Returns a full AI-narrated weekly financial report including spend summary, "
        "category breakdown, top merchants, budget health, upcoming subscriptions, "
        "and an AI-generated narrative with tips. Cached for 60 minutes per user."
    ),
)
async def ai_weekly_report(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WeeklyReportDto:
    await _verify_user_owns_report(user_id, current_user_id, db)
    logger.info("reports: AI weekly report requested | user_id=%s", user_id)

    # 1. Check Redis cache
    cached = await _get_cached_weekly_report(user_id)
    if cached:
        logger.info("reports: AI weekly report cache hit | user_id=%s", user_id)
        return cached

    # 2. Generate fresh
    report = await generate_weekly_report(db=db, user_id=user_id)

    # 3. Store in cache
    await _set_cached_weekly_report(user_id, report)

    return report
