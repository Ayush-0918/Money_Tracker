import pytest
from httpx import AsyncClient
from fastapi import status
from .test_api import register_user

@pytest.mark.asyncio
async def test_budget_recalculate_rate_limiting(client: AsyncClient):
    """Verify that calling the budget recalculate route repeatedly triggers a 429."""
    token, user_id = await register_user(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trigger recalculation multiple times rapidly
    # Limit is 5/minute, so the 6th call should return 429
    responses = []
    for _ in range(6):
        resp = await client.post("/budgets/recalculate", headers=headers)
        responses.append(resp.status_code)

    # Assert that at least one of the requests received 429
    assert status.HTTP_429_TOO_MANY_REQUESTS in responses
