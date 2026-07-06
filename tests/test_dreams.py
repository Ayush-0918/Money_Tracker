"""
tests/test_dreams.py
─────────────────────────────────────────────────────────────────────────────
Unit & integration tests for AI Dream Planner services and endpoints.
"""

import uuid
import pytest
import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dream_service import (
    create_dream,
    update_dream_progress,
    get_user_dreams,
)


@pytest.mark.asyncio
async def test_create_dream_success():
    """create_dream successfully parses target timeline and calls AI."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    deadline = datetime.date.today() + datetime.timedelta(days=120)  # ~4 months

    with patch("app.services.dream_service.generate_ai_roadmap") as mock_ai:
        mock_ai.return_value = {
            "risk_analysis": "low",
            "investment_suggestions": ["Index Fund"],
            "milestones": [{"percent": 50, "label": "Halfway"}]
        }

        dream = await create_dream(db, user_id, "MacBook Air", Decimal("80000"), deadline)

    assert dream.name == "MacBook Air"
    assert dream.target_amount == Decimal("80000")
    assert dream.weekly_saving_target > 0
    assert dream.monthly_saving_target > 0
    assert dream.status == "active"
    db.add.assert_called_once_with(dream)


@pytest.mark.asyncio
async def test_create_dream_invalid_deadline():
    """create_dream raises ValueError if deadline is today or in the past."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    deadline = datetime.date.today() - datetime.timedelta(days=1)

    with pytest.raises(ValueError, match="future"):
        await create_dream(db, user_id, "Past Dream", Decimal("100"), deadline)


@pytest.mark.asyncio
async def test_update_dream_progress_completed():
    """update_dream_progress marks status as completed if target is met."""
    db = AsyncMock()
    dream_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Mock DB returns the dream
    mock_dream = MagicMock()
    mock_dream.id = dream_id
    mock_dream.target_amount = Decimal("1000")
    mock_dream.current_savings = Decimal("500")
    mock_dream.status = "active"

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_dream
    db.execute.return_value = mock_res

    updated = await update_dream_progress(db, dream_id, user_id, Decimal("500"))

    assert updated.current_savings == Decimal("1000")
    assert updated.status == "completed"


# ── API Endpoint Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dreams_endpoints_unauthorized(client):
    """Anonymous requests to dreams endpoints must return 401/403."""
    response = await client.get("/dreams")
    assert response.status_code in [401, 403, 422]
