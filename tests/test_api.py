"""
tests/test_api.py
─────────────────────────────────────────────────────────────────────────────
Integration tests for the API endpoints.

Uses FastAPI's TestClient with dependency overrides to replace the real
PostgreSQL database with an in-memory SQLite database (via aiosqlite).

Test flow:
  1. Register a user → get JWT token.
  2. POST a transaction → verify parsed fields returned.
  3. POST an OTP message → verify 400 rejection.
  4. POST unparseable message → verify 422 response.
  5. GET monthly report → verify structure.
  6. GET subscription report → verify structure.
  7. Test auth: missing token, wrong user_id.

To run:
    pytest tests/test_api.py -v
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base

# ── Test Client Helper ────────────────────────────────────────────────────────


# ── Registration Helper ───────────────────────────────────────────────────────

async def register_user(client: AsyncClient, phone: str = "+919876543210") -> tuple[str, str]:
    """
    Register a test user and return (access_token, user_id_str).

    Args:
        client: The async test client.
        phone:  Phone number to register (defaults to a test number).

    Returns:
        Tuple of (JWT token string, user_id UUID string).
    """
    response = await client.post(
        "/auth/register",
        json={"phone_number": phone, "name": "Test User", "language_preference": "en"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    return data["access_token"], data["user_id"]


# ── Authentication Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient):
    """Registering a new user returns 200 with a JWT token and user_id."""
    response = await client.post(
        "/auth/register",
        json={"phone_number": "+911234567890", "name": "Aayu", "language_preference": "hi"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert data["name"] == "Aayu"


@pytest.mark.asyncio
async def test_register_idempotent(client: AsyncClient):
    """Registering twice with the same phone number returns a token both times."""
    response1 = await client.post(
        "/auth/register",
        json={"phone_number": "+919999999999", "name": "User"},
    )
    response2 = await client.post(
        "/auth/register",
        json={"phone_number": "+919999999999", "name": "User"},
    )
    assert response1.status_code == 200
    assert response2.status_code == 200
    # Same user_id returned for the same phone
    assert response1.json()["user_id"] == response2.json()["user_id"]


@pytest.mark.asyncio
async def test_register_invalid_phone(client: AsyncClient):
    """Invalid phone number format returns 422."""
    response = await client.post(
        "/auth/register",
        json={"phone_number": "not-a-phone", "name": "User"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ── Transaction Tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_transaction_success(client: AsyncClient):
    """Valid payment notification is parsed and saved successfully."""
    token, user_id = await register_user(client)

    response = await client.post(
        "/transactions",
        json={
            "user_id": user_id,
            "raw_text": "Rs.499 debited from your account for Netflix via UPI.",
            "source": "notification",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert str(data["amount"]) == "499"
    assert "Netflix" in data["merchant"]
    assert data["source"] == "notification"
    assert data["user_id"] == user_id
    assert data["category"] is None  # Phase 3 — intentionally null


@pytest.mark.asyncio
async def test_post_transaction_otp_rejected(client: AsyncClient):
    """OTP message returns 400 and nothing is saved."""
    token, user_id = await register_user(client)

    response = await client.post(
        "/transactions",
        json={
            "user_id": user_id,
            "raw_text": "Your OTP is 123456. Valid for 10 minutes. Do not share.",
            "source": "sms",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["error"] == "OTP_REJECTED"


@pytest.mark.asyncio
async def test_post_transaction_parse_failed(client: AsyncClient):
    """Unparseable notification returns 422 with PARSE_FAILED error."""
    token, user_id = await register_user(client)

    response = await client.post(
        "/transactions",
        json={
            "user_id": user_id,
            "raw_text": "This is just some random text with no financial data.",
            "source": "sms",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"]["error"] == "PARSE_FAILED"


@pytest.mark.asyncio
async def test_post_transaction_no_auth(client: AsyncClient):
    """Request without Authorization header returns 401."""
    response = await client.post(
        "/transactions",
        json={
            "user_id": str(uuid.uuid4()),
            "raw_text": "Rs.500 debited to Netflix.",
            "source": "notification",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_post_transaction_wrong_user_id(client: AsyncClient):
    """Submitting a transaction for a different user_id returns 403."""
    token, _ = await register_user(client, phone="+911111111111")

    response = await client.post(
        "/transactions",
        json={
            "user_id": str(uuid.uuid4()),  # Different user's ID
            "raw_text": "Rs.500 debited to Netflix.",
            "source": "notification",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Report Tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_monthly_report_empty(client: AsyncClient):
    """Monthly report for a user with no transactions returns zero totals."""
    token, user_id = await register_user(client)

    response = await client.get(
        f"/reports/monthly/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_spend_formatted" in data
    assert "categories" in data
    assert data["recent_transactions"] == []


@pytest.mark.asyncio
async def test_monthly_report_with_transaction(client: AsyncClient):
    """Monthly report reflects a saved transaction."""
    token, user_id = await register_user(client)

    # Save a transaction first
    await client.post(
        "/transactions",
        json={
            "user_id": user_id,
            "raw_text": "Rs.299 debited for Spotify subscription.",
            "source": "notification",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        f"/reports/monthly/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["recent_transactions"]) == 1
    assert "299" in data["total_spend_formatted"]


@pytest.mark.asyncio
async def test_monthly_report_wrong_user(client: AsyncClient):
    """Cannot view another user's monthly report — returns 403."""
    token, _ = await register_user(client, phone="+912222222222")
    other_user_id = str(uuid.uuid4())

    response = await client.get(
        f"/reports/monthly/{other_user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_subscription_report_empty(client: AsyncClient):
    """Subscription report with no subscriptions returns empty lists."""
    token, user_id = await register_user(client)

    response = await client.get(
        f"/reports/subscriptions/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert data == []


# ── Health Check ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
