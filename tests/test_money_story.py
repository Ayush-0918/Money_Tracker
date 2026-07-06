"""
tests/test_money_story.py
─────────────────────────────────────────────────────────────────────────────
Unit & integration tests for Sunday Money Story service and API endpoints.
"""

import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.money_story_service import (
    generate_money_story,
    _score_label,
    _financial_mood,
)


# ── Unit Tests ────────────────────────────────────────────────────────────────


def test_score_label():
    assert _score_label(90)[0] == "Excellent"
    assert _score_label(75)[0] == "Good"
    assert _score_label(60)[0] == "Fair"
    assert _score_label(30)[0] == "Poor"


def test_financial_mood():
    assert _financial_mood(90, True)[0] == "Super Saver 🎯"
    assert _financial_mood(75, True)[0] == "Balanced ⚖️"
    assert _financial_mood(55, False)[0] == "Unstable 🌪️"
    assert _financial_mood(30, False)[0] == "Spendthrift 🚨"


# ── Service Mock Setup ────────────────────────────────────────────────────────


def _make_db_mock(
    week_spend: Decimal = Decimal("5000"),
    prior_spend: Decimal = Decimal("4000"),
    cat_rows=None,
    merch_rows=None,
    daily_rows=None,
    budgets=None,
    subscriptions=None,
):
    """Helper that creates a mock AsyncSession returning controlled data."""
    if cat_rows is None:
        cat_rows = []
    if merch_rows is None:
        merch_rows = []
    if daily_rows is None:
        daily_rows = []
    if budgets is None:
        budgets = []
    if subscriptions is None:
        subscriptions = []

    call_results = []

    # 1. total_spend
    r1 = MagicMock()
    r1.scalar_one.return_value = week_spend
    call_results.append(r1)

    # 2. prior_spend
    r2 = MagicMock()
    r2.scalar_one.return_value = prior_spend
    call_results.append(r2)

    # 3. category rows
    r3 = MagicMock()
    r3.all.return_value = cat_rows
    call_results.append(r3)

    # 4. merchant rows
    r4 = MagicMock()
    r4.all.return_value = merch_rows
    call_results.append(r4)

    # 5. daily rows
    r5 = MagicMock()
    r5.all.return_value = daily_rows
    call_results.append(r5)

    # 6. budget query
    r6 = MagicMock()
    r6.scalars.return_value.all.return_value = budgets
    call_results.append(r6)

    # 7. subscription query
    r7 = MagicMock()
    r7.scalars.return_value.all.return_value = subscriptions
    call_results.append(r7)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=call_results)
    return db


# ── Integration Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_money_story_empty():
    """Generates Money Story when no data exists (empty state)."""
    db = _make_db_mock(week_spend=Decimal("0"), prior_spend=Decimal("0"))
    user_id = uuid.uuid4()

    with patch("app.services.money_story_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_money_story_ai.return_value = None
        mock_ai.return_value = mock_instance

        story = await generate_money_story(db=db, user_id=user_id)

    assert story.page_score.money_score == 100
    assert story.page_spending.total_spend == 0.0
    assert story.page_savings.savings_amount == 0.0
    assert story.page_achievements.earned_count == 1  # Sub Hunter (since budgets list is empty)
    assert story.page_mistakes.has_mistakes is False


@pytest.mark.asyncio
async def test_generate_money_story_with_ai():
    """Generates Money Story and populates AI narrative fields successfully."""
    db = _make_db_mock(week_spend=Decimal("2000"), prior_spend=Decimal("3000"))
    user_id = uuid.uuid4()

    ai_response = {
        "best_decision": "You bought groceries instead of dining out.",
        "worst_decision": "You spent heavily on apparel.",
        "prediction_next_week": "Spend likely to remain stable.",
        "tips": ["Limit impulse shopping.", "Track micro-transactions."],
        "weekly_challenge": "Spend under ₹200 tomorrow."
    }

    with patch("app.services.money_story_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_money_story_ai.return_value = ai_response
        mock_ai.return_value = mock_instance

        story = await generate_money_story(db=db, user_id=user_id)

    assert story.page_action.best_decision == "You bought groceries instead of dining out."
    assert story.page_mistakes.worst_decision == "You spent heavily on apparel."
    assert story.page_forecast.prediction_next_week == "Spend likely to remain stable."
    assert "Limit impulse shopping." in story.page_action.ai_tips
    assert story.page_action.weekly_challenge == "Spend under ₹200 tomorrow."


@pytest.mark.asyncio
async def test_generate_money_story_ai_fallback():
    """Fallback rules are triggered when AI service fails."""
    db = _make_db_mock(week_spend=Decimal("4000"), prior_spend=Decimal("3000"))
    user_id = uuid.uuid4()

    with patch("app.services.money_story_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_money_story_ai.side_effect = Exception("AI down")
        mock_ai.return_value = mock_instance

        story = await generate_money_story(db=db, user_id=user_id)

    assert story.page_action.best_decision != ""
    assert story.page_mistakes.worst_decision != ""
    assert story.page_forecast.prediction_next_week != ""
    assert len(story.page_action.ai_tips) >= 1
    assert story.page_action.weekly_challenge != ""


# ── Endpoint Security ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_story_endpoint_unauthorized(client):
    """Anonymous requests must return 401/403."""
    user_id = uuid.uuid4()
    response = await client.get(f"/money-story/{user_id}")
    assert response.status_code in [401, 403, 422]
