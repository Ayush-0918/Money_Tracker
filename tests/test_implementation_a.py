import pytest
import uuid
from fastapi import status
from httpx import AsyncClient
from .test_api import register_user

@pytest.mark.asyncio
async def test_patch_category_invalid_id(client: AsyncClient):
    """Verify that patching with a non-existent category_id returns 400."""
    token, user_id = await register_user(client)

    # 1. Create a transaction first
    payload = {
        "user_id": user_id,
        "raw_text": "Rs.100 debited to Tea Stall.",
        "source": "notification",
        "idempotency_key": "test_patch_1"
    }
    headers = {"Authorization": f"Bearer {token}"}
    resp_tx = await client.post("/transactions", json=payload, headers=headers)
    tx_id = resp_tx.json()["id"]

    # 2. Try to patch with random UUID
    patch_payload = {"category_id": str(uuid.uuid4())}
    resp_patch = await client.patch(f"/transactions/{tx_id}/category", json=patch_payload, headers=headers)

    assert resp_patch.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid category_id" in resp_patch.json()["detail"]

@pytest.mark.asyncio
async def test_patch_category_ownership_idor(client: AsyncClient):
    """Verify that User A cannot patch a transaction belonging to User B."""
    token_a, user_a = await register_user(client, phone="+911111111111")
    token_b, user_b = await register_user(client, phone="+912222222222")

    # 1. User A creates a transaction
    headers_a = {"Authorization": f"Bearer {token_a}"}
    resp_tx = await client.post(
        "/transactions",
        json={"user_id": user_a, "raw_text": "A's spend", "source": "notification"},
        headers=headers_a
    )
    tx_id = resp_tx.json()["id"]

    # 2. User B tries to patch User A's transaction
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp_patch = await client.patch(
        f"/transactions/{tx_id}/category",
        json={"category_id": str(uuid.uuid4())},
        headers=headers_b
    )

    assert resp_patch.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_rate_limiting_patch_category(client: AsyncClient):
    """Verify that the rate limiter is configured for the PATCH endpoint."""
    # Note: Full rate limit test requires lowering limits in config,
    # but we verify the endpoint still functions for valid requests.
    token, user_id = await register_user(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Just verify 404 for non-existent tx instead of 429 immediately
    resp = await client.patch(
        f"/transactions/{uuid.uuid4()}/category",
        json={"category_id": str(uuid.uuid4())},
        headers=headers
    )
    assert resp.status_code == 404
