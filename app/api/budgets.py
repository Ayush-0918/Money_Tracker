"""
app/api/budgets.py
─────────────────────────────────────────────────────────────────────────────
Budget endpoints.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user_id, get_db
from app.config import settings
from app.utils.limiter import limiter
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetSummaryResponse
from app.services.budget_service import get_budget_summary_from_cache, recalculate_user_budgets
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post(
    "",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new budget",
)
@limiter.limit("10/minute")
async def create_budget(
    body: BudgetCreate,
    request: Request,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        new_budget = Budget(user_id=current_user_id, category_id=body.category_id, monthly_limit=body.monthly_limit)
        db.add(new_budget)
        await db.flush()  # flush to catch integrity errors

        # Trigger recalculation for this newly created budget
        await recalculate_user_budgets(db, current_user_id)

        logger.info("budgets: created | user_id=%s | category_id=%s", current_user_id, body.category_id)
        return new_budget
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A budget for this category already exists for this user."
        )


@router.get(
    "",
    response_model=List[BudgetResponse],
    status_code=status.HTTP_200_OK,
    summary="List all budgets for user",
)
async def list_budgets(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Budget).where(Budget.user_id == current_user_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/summary",
    response_model=List[BudgetSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get budget summaries (from cache)",
)
async def get_budget_summary(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_budget_summary_from_cache(db, current_user_id)


@router.post(
    "/recalculate",
    status_code=status.HTTP_200_OK,
    summary="Force recalculation of budget snapshots",
)
@limiter.limit("5/minute")
async def force_recalculate_budgets(
    request: Request,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await recalculate_user_budgets(db, current_user_id)
    return {"status": "ok", "message": "Budgets recalculated"}


@router.patch(
    "/{budget_id}",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
    summary="Update budget limit",
)
@limiter.limit("10/minute")
async def update_budget(
    budget_id: uuid.UUID,
    body: BudgetCreate,
    request: Request,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user_id)
    result = await db.execute(stmt)
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # No-op check: category and limit are identical
    if b.category_id == body.category_id and b.monthly_limit == body.monthly_limit:
        logger.info("budgets: update is no-op | budget_id=%s", budget_id)
        return b

    b.category_id = body.category_id
    b.monthly_limit = body.monthly_limit

    # Needs recalculation if category changed
    b.cached_updated_at = None

    return b


@router.delete(
    "/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete budget",
)
@limiter.limit("10/minute")
async def delete_budget(
    budget_id: uuid.UUID,
    request: Request,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user_id)
    result = await db.execute(stmt)
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    await db.delete(b)
    return None
