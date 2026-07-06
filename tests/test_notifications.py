"""
tests/test_notifications.py
─────────────────────────────────────────────────────────────────────────────
Unit & integration tests for push registration and budget/sub scanners.
"""

import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification_service import (
    register_device_token,
    create_notification,
    get_user_notifications,
    mark_notifications_as_read,
    scan_budget_thresholds,
    scan_subscription_dues,
)


@pytest.mark.asyncio
async def test_register_device_token():
    """register_device_token saves or updates token successfully."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    token = "test_fcm_token"

    # Token check returns None (no duplicate exists)
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    device = await register_device_token(db, user_id, token, "android")

    assert device.token == token
    assert device.user_id == user_id
    db.add.assert_called_once_with(device)


@pytest.mark.asyncio
async def test_create_notification():
    """create_notification successfully logs and inserts a push history."""
    db = AsyncMock()
    user_id = uuid.uuid4()

    notif = await create_notification(db, user_id, "Title", "Body", "alert")

    assert notif.title == "Title"
    assert notif.body == "Body"
    assert notif.notification_type == "alert"
    db.add.assert_called_once_with(notif)


@pytest.mark.asyncio
async def test_mark_notifications_as_read():
    """mark_notifications_as_read updates is_read flag."""
    db = AsyncMock()
    user_id = uuid.uuid4()
    notif_ids = [uuid.uuid4(), uuid.uuid4()]

    mock_res = MagicMock()
    mock_res.rowcount = 2
    db.execute.return_value = mock_res

    count = await mark_notifications_as_read(db, user_id, notif_ids)
    assert count == 2


@pytest.mark.asyncio
async def test_scan_budget_thresholds_alert():
    """scan_budget_thresholds triggers alert if spent >= 80% of weekly limit."""
    db = AsyncMock()

    # Mock Budget
    mock_budget = MagicMock()
    mock_budget.user_id = uuid.uuid4()
    mock_budget.category_id = uuid.uuid4()
    mock_budget.monthly_limit = Decimal("433")  # weekly limit = 100

    r1 = MagicMock()
    r1.scalars.return_value.all.return_value = [mock_budget]

    # spent = 85 (ratio = 85% >= 80%)
    r2 = MagicMock()
    r2.scalar_one.return_value = Decimal("85")

    # duplicate check returns None
    r3 = MagicMock()
    r3.scalar_one_or_none.return_value = None

    db.execute.side_effect = [r1, r2, r3]

    with patch("app.services.notification_service.create_notification") as mock_create:
        count = await scan_budget_thresholds(db)

    assert count == 1
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_scan_subscription_dues_alert():
    """scan_subscription_dues triggers alert if billing is tomorrow."""
    db = AsyncMock()

    # Mock Sub
    mock_sub = MagicMock()
    mock_sub.user_id = uuid.uuid4()
    mock_sub.merchant = "Netflix"
    mock_sub.amount = 199.0

    r1 = MagicMock()
    r1.scalars.return_value.all.return_value = [mock_sub]

    # duplicate check returns None
    r2 = MagicMock()
    r2.scalar_one_or_none.return_value = None

    db.execute.side_effect = [r1, r2]

    with patch("app.services.notification_service.create_notification") as mock_create:
        count = await scan_subscription_dues(db)

    assert count == 1
    mock_create.assert_called_once()


# ── API Endpoint Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notifications_endpoints_unauthorized(client):
    """Anonymous requests to notifications endpoints must return 401/403."""
    response = await client.get("/notifications")
    assert response.status_code in [401, 403, 422]
