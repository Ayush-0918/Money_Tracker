import pytest
import uuid
from fastapi import status
from httpx import AsyncClient
from tests.test_api import register_user

@pytest.mark.asyncio
async def test_coach_report_unauthorized(client: AsyncClient):
    """Accessing coach report without authorization returns 401."""
    user_id = str(uuid.uuid4())
    response = await client.get(f"/reports/coach/{user_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_coach_report_forbidden(client: AsyncClient):
    """Accessing someone else's coach report returns 403."""
    token, _ = await register_user(client, phone="+919800000000")
    other_user_id = str(uuid.uuid4())
    
    response = await client.get(
        f"/reports/coach/{other_user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_coach_report_success(client: AsyncClient):
    """Accessing own coach report returns 200 with the correct metrics."""
    token, user_id = await register_user(client, phone="+919811111111")
    
    response = await client.get(
        f"/reports/coach/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "insights" in data
    assert isinstance(data["insights"], list)
    assert "active_subscriptions" in data
    assert "financial_health_score" in data
    assert data["financial_health_score"] >= 0
