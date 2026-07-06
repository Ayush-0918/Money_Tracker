"""
app/api/predictions.py
─────────────────────────────────────────────────────────────────────────────
Endpoints for AI-powered financial behavior predictions.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.prediction import AIPredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get(
    "",
    response_model=AIPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI financial predictions",
    description=(
        "Retrieves detailed financial forecasts for the next month. "
        "Includes expense predictions, cash flow risks, and budget status. "
        "Responses are cached for 24 hours."
    ),
)
async def get_predictions(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> AIPredictionResponse:
    service = PredictionService(db)
    return await service.get_predictions(current_user_id)


@router.post(
    "/refresh",
    response_model=AIPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Force refresh AI predictions",
    description="Clears the prediction cache and generates fresh AI forecasts based on the latest data.",
)
async def refresh_predictions(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> AIPredictionResponse:
    # To implement refresh, we could just clear the cache entry first
    from sqlalchemy import delete
    from app.models.user import PredictionCache

    await db.execute(delete(PredictionCache).where(PredictionCache.user_id == current_user_id))
    await db.commit()

    service = PredictionService(db)
    return await service.get_predictions(current_user_id)
