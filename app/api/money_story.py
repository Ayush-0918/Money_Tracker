"""
app/api/money_story.py
─────────────────────────────────────────────────────────────────────────────
Money Story router. Surfaces the 7-page interactive swipeable Sunday story.
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.models.user import User
from app.schemas.money_story import MoneyStoryDto
from app.services.money_story_service import generate_money_story
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/money-story", tags=["Money Story"])

# ── Redis Cache Helper ────────────────────────────────────────────────────────
try:
    import redis.asyncio as aioredis
    from app.config import settings as _cfg

    _redis: Optional[aioredis.Redis] = aioredis.from_url(_cfg.REDIS_URL, decode_responses=True) if _cfg.REDIS_URL else None
except Exception:
    _redis = None

_STORY_TTL = 3600  # 60 minutes


async def _get_cached_story(user_id: uuid.UUID) -> Optional[MoneyStoryDto]:
    if _redis is None:
        return None
    try:
        key = f"money_story:{user_id}"
        raw = await _redis.get(key)
        if raw:
            return MoneyStoryDto(**json.loads(raw))
    except Exception as e:
        logger.warning("Redis money story cache read failed: %s", e)
    return None


async def _set_cached_story(user_id: uuid.UUID, story: MoneyStoryDto) -> None:
    if _redis is None:
        return
    try:
        key = f"money_story:{user_id}"
        await _redis.setex(key, _STORY_TTL, story.model_dump_json())
    except Exception as e:
        logger.warning("Redis money story cache write failed: %s", e)


async def _clear_cached_story(user_id: uuid.UUID) -> None:
    if _redis is None:
        return
    try:
        key = f"money_story:{user_id}"
        await _redis.delete(key)
    except Exception as e:
        logger.warning("Redis money story cache clear failed: %s", e)


async def _verify_user_owns_story(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own Money Story.",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found.",
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get(
    "/{user_id}",
    response_model=MoneyStoryDto,
    status_code=status.HTTP_200_OK,
    summary="Get Sunday Money Story",
    description="Returns the 7-page interactive Sunday Money Story. Cached for 60 minutes.",
)
async def get_story(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MoneyStoryDto:
    await _verify_user_owns_story(user_id, current_user_id, db)
    logger.info("money_story: story requested | user_id=%s", user_id)

    # 1. Check Cache
    cached = await _get_cached_story(user_id)
    if cached:
        logger.info("money_story: cache hit | user_id=%s", user_id)
        return cached

    # 2. Generate Fresh
    story = await generate_money_story(db=db, user_id=user_id)

    # 3. Cache
    await _set_cached_story(user_id, story)

    return story


@router.post(
    "/{user_id}/refresh",
    response_model=MoneyStoryDto,
    status_code=status.HTTP_200_OK,
    summary="Regenerate Sunday Money Story",
    description="Forces regeneration of the Sunday Money Story, clearing the Redis cache.",
)
async def refresh_story(
    user_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MoneyStoryDto:
    await _verify_user_owns_story(user_id, current_user_id, db)
    logger.info("money_story: story refresh requested | user_id=%s", user_id)

    # 1. Clear Cache
    await _clear_cached_story(user_id)

    # 2. Generate Fresh
    story = await generate_money_story(db=db, user_id=user_id)

    # 3. Cache
    await _set_cached_story(user_id, story)

    return story
