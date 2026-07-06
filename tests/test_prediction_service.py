import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.prediction_service import PredictionService
from app.schemas.prediction import AIPredictionResponse


@pytest.mark.asyncio
async def test_prediction_service_fallback():
    # Mock Result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No cache
    mock_result.scalars.return_value.all.return_value = []  # No transactions

    # Mock DB
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    # Mock AI Provider to fail
    from app.services.ai_service import AIService

    mock_ai = MagicMock(spec=AIService)
    mock_ai.provider = MagicMock()
    mock_ai.provider.get_completion = AsyncMock(return_value=None)

    # Patch get_ai_service
    import app.services.prediction_service as ps

    original_get_ai = ps.get_ai_service
    ps.get_ai_service = lambda: mock_ai

    try:
        service = PredictionService(mock_db)
        user_id = uuid.uuid4()
        predictions = await service.get_predictions(user_id)

        assert isinstance(predictions, AIPredictionResponse)
        assert predictions.user_id == user_id
        assert "Statistical fallback" in predictions.ai_insights[0]
    finally:
        ps.get_ai_service = original_get_ai


@pytest.mark.asyncio
async def test_prediction_service_cache_hit():
    user_id = uuid.uuid4()
    cached_data = {
        "user_id": str(user_id),
        "expense_forecast": {
            "next_day": 100.0,
            "next_week": 700.0,
            "next_month": 3000.0,
            "category_forecast": {"Food": 500.0},
            "confidence_percentage": 90.0,
        },
        "cash_flow_forecast": {
            "predicted_balance": [],
            "estimated_inflow": 5000.0,
            "estimated_outflow": 3000.0,
            "negative_balance_risk_dates": [],
        },
        "budget_forecast": [],
        "salary_prediction": {
            "is_detected": True,
            "expected_date": "2024-08-01",
            "expected_amount": 50000.0,
            "confidence": 0.95,
        },
        "ai_insights": ["Insight 1"],
    }

    # Mock Cache
    mock_cache = MagicMock()
    mock_cache.updated_at = datetime.now(timezone.utc)
    mock_cache.predictions = cached_data

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cache

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    service = PredictionService(mock_db)
    predictions = await service.get_predictions(user_id)

    assert predictions.expense_forecast.next_day == 100.0
    assert predictions.salary_prediction.is_detected is True
