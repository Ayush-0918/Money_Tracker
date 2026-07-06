"""
app/api/dreams.py
─────────────────────────────────────────────────────────────────────────────
API Endpoints for AI Dream Planner.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.dream import DreamCreateDto, DreamUpdateProgressDto, DreamDto
from app.services import dream_service

router = APIRouter(prefix="/dreams", tags=["AI Dream Planner"])


@router.post(
    "/create",
    response_model=DreamDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new financial dream goal",
)
async def create_new_dream(
    dto: DreamCreateDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> DreamDto:
    try:
        await dream_service.create_dream(
            db, current_user_id, dto.name, dto.target_amount, dto.deadline
        )
        # Fetch list to compile full roadmap details
        list_dreams = await dream_service.get_user_dreams(db, current_user_id)
        if list_dreams:
            return list_dreams[0]
        raise HTTPException(status_code=500, detail="Failed to retrieve created dream.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "",
    response_model=List[DreamDto],
    status_code=status.HTTP_200_OK,
    summary="List all user dreams",
)
async def get_dreams(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[DreamDto]:
    return await dream_service.get_user_dreams(db, current_user_id)


@router.post(
    "/{dream_id}/progress",
    response_model=DreamDto,
    status_code=status.HTTP_200_OK,
    summary="Log savings progress towards a dream",
)
async def add_progress(
    dream_id: uuid.UUID,
    dto: DreamUpdateProgressDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> DreamDto:
    try:
        await dream_service.update_dream_progress(db, dream_id, current_user_id, dto.amount)
        list_dreams = await dream_service.get_user_dreams(db, current_user_id)
        for d in list_dreams:
            if d.id == dream_id:
                return d
        raise HTTPException(status_code=404, detail="Dream details not found.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
