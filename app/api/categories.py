"""
app/api/categories.py
─────────────────────────────────────────────────────────────────────────────
Category endpoints.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.api.deps import get_current_user_id, get_db
from app.models.category import Category
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get(
    "",
    response_model=List[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all categories available to user",
)
async def list_categories(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns system categories first, then user categories.
    Alphabetically sorted inside each section.
    """
    stmt = select(Category).where(
        or_(Category.system == True, Category.user_id == current_user_id)
    ).order_by(
        Category.system.desc(), # True comes before False in DESC
        Category.sort_order.asc(),
        Category.display_name.asc()
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()
