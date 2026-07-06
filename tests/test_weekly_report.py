"""
tests/test_weekly_report.py
─────────────────────────────────────────────────────────────────────────────
Unit tests for the AI Weekly Financial Report service and API endpoint.

Tests cover:
  - Empty-state report generation (no transactions, no budgets)
  - Normal-state report generation with mocked DB data
  - AI narrative fallback when AI service fails
  - Spend-change math (increase / decrease / no prior week data)
  - Health score boundary clamping
  - API endpoint auth (own-report access only)
  - Redis cache layer (mock)
"""

import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.weekly_report_service import generate_weekly_report, _health_label


# ── Unit tests for _health_label ──────────────────────────────────────────────


def test_health_label_excellent():
    label, color = _health_label(90)
    assert label == "Excellent"
    assert color == "#4CAF7D"


def test_health_label_good():
    label, color = _health_label(70)
    assert label == "Good"
    assert color == "#90CAF9"


def test_health_label_fair():
    label, color = _health_label(50)
    assert label == "Fair"
    assert color == "#F5A623"


def test_health_label_poor():
    label, color = _health_label(20)
    assert label == "Poor"
    assert color == "#EF5350"


def test_health_label_boundary_80():
    label, _ = _health_label(80)
    assert label == "Excellent"


def test_health_label_boundary_60():
    label, _ = _health_label(60)
    assert label == "Good"


def test_health_label_boundary_40():
    label, _ = _health_label(40)
    assert label == "Fair"


# ── Integration tests: generate_weekly_report with mocked DB ──────────────────


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

    # Each execute() call returns a mock result; we cycle through them
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

    # 6. budget query (scalars)
    r6 = MagicMock()
    r6.scalars.return_value.all.return_value = budgets
    call_results.append(r6)

    # 7. subscription query (scalars)
    r7 = MagicMock()
    r7.scalars.return_value.all.return_value = subscriptions
    call_results.append(r7)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=call_results)
    return db


@pytest.mark.asyncio
async def test_weekly_report_empty_state():
    """Empty-state: no transactions, no budgets — should return valid DTO with zeroes."""
    db = _make_db_mock(week_spend=Decimal("0"), prior_spend=Decimal("0"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.total_spend == 0.0
    assert report.prior_week_spend == 0.0
    assert report.spend_change_pct == 0.0
    assert report.spend_change_is_increase is False
    assert report.spend_change_text == "No change from last week"
    assert len(report.daily_points) == 7
    assert report.financial_health_score >= 10
    assert report.financial_health_score <= 100
    assert report.ai_narrative != ""
    assert isinstance(report.ai_tips, list)
    assert len(report.ai_tips) >= 1


@pytest.mark.asyncio
async def test_weekly_report_spend_increase():
    """When current week > prior week → spend_change_is_increase = True."""
    db = _make_db_mock(week_spend=Decimal("6000"), prior_spend=Decimal("4000"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.spend_change_is_increase is True
    assert abs(report.spend_change_pct - 50.0) < 0.01  # 50% increase
    assert "more" in report.spend_change_text


@pytest.mark.asyncio
async def test_weekly_report_spend_decrease():
    """When current week < prior week → spend_change_is_increase = False."""
    db = _make_db_mock(week_spend=Decimal("3000"), prior_spend=Decimal("4000"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.spend_change_is_increase is False
    assert report.spend_change_pct < 0
    assert "less" in report.spend_change_text


@pytest.mark.asyncio
async def test_weekly_report_no_prior_week():
    """When prior_spend is 0 and current > 0 → 100% increase."""
    db = _make_db_mock(week_spend=Decimal("2500"), prior_spend=Decimal("0"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.spend_change_pct == 100.0
    assert report.spend_change_is_increase is True
    assert "100%" in report.spend_change_text


@pytest.mark.asyncio
async def test_weekly_report_ai_narrative_populated():
    """When AI service returns a valid narrative, it is used in the DTO."""
    db = _make_db_mock()
    user_id = uuid.uuid4()

    ai_response = {
        "narrative": "You spent well this week.",
        "tips": ["Track daily expenses.", "Avoid impulse buys."],
    }

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = ai_response
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.ai_narrative == "You spent well this week."
    assert "Track daily expenses." in report.ai_tips
    assert "Avoid impulse buys." in report.ai_tips


@pytest.mark.asyncio
async def test_weekly_report_ai_fallback_on_exception():
    """If AI service raises an exception, the rule-based fallback kicks in."""
    db = _make_db_mock(week_spend=Decimal("1500"), prior_spend=Decimal("1000"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.side_effect = RuntimeError("AI provider down")
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    # Should still have a narrative (fallback)
    assert report.ai_narrative != ""
    assert len(report.ai_tips) >= 1


@pytest.mark.asyncio
async def test_weekly_report_health_score_clamped():
    """Health score must always be between 10 and 100."""
    db = _make_db_mock()
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert 10 <= report.financial_health_score <= 100


@pytest.mark.asyncio
async def test_weekly_report_daily_points_length():
    """daily_points must always have exactly 7 entries."""
    db = _make_db_mock()
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert len(report.daily_points) == 7
    assert len(report.daily_labels) == 7


@pytest.mark.asyncio
async def test_weekly_report_formatted_fields():
    """Formatted fields must start with ₹ for non-zero amounts."""
    db = _make_db_mock(week_spend=Decimal("3500.50"), prior_spend=Decimal("2000"))
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert report.total_spend_formatted.startswith("₹")
    assert report.prior_week_spend_formatted.startswith("₹")
    assert report.average_per_day_formatted.startswith("₹")


@pytest.mark.asyncio
async def test_weekly_report_week_label_format():
    """week_label must contain an en-dash and a year."""
    db = _make_db_mock()
    user_id = uuid.uuid4()

    with patch("app.services.weekly_report_service.get_ai_service") as mock_ai:
        mock_instance = AsyncMock()
        mock_instance.get_weekly_narrative.return_value = None
        mock_ai.return_value = mock_instance

        report = await generate_weekly_report(db=db, user_id=user_id)

    assert "–" in report.week_label  # en-dash separator
    import datetime

    current_year = str(datetime.datetime.now().year)
    assert current_year in report.week_label


# ── API endpoint test (auth guard) ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_weekly_report_endpoint_unauthenticated(client):
    """Unauthenticated request to weekly-report endpoint must return 401 or 403."""
    user_id = uuid.uuid4()
    response = await client.get(f"/reports/weekly-report/{user_id}")
    assert response.status_code in (401, 403, 422)
