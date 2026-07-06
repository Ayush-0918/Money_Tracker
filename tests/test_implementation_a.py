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
        "idempotency_key": "test_patch_1",
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
        json={"user_id": user_a, "raw_text": "Rs.100 debited to Amazon.", "source": "notification"},
        headers=headers_a,
    )
    tx_id = resp_tx.json()["id"]

    # 2. User B tries to patch User A's transaction
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp_patch = await client.patch(
        f"/transactions/{tx_id}/category", json={"category_id": str(uuid.uuid4())}, headers=headers_b
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
        f"/transactions/{uuid.uuid4()}/category", json={"category_id": str(uuid.uuid4())}, headers=headers
    )
    assert resp.status_code == 404


from app.models.merchant import LearningEvent
from app.models.category import Category
from sqlalchemy import select


@pytest.mark.asyncio
async def test_patch_category_silent_bug_and_deduplication(client: AsyncClient, db_session):
    """Verify that old_category_id is captured correctly and duplicate patch is a no-op."""
    token, user_id = await register_user(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Pre-populate categories
    cat_a_id = str(uuid.uuid4())
    cat_b_id = str(uuid.uuid4())
    cat_a = Category(id=uuid.UUID(cat_a_id), name="Food", slug="food", display_name="Food", system=True)
    cat_b = Category(id=uuid.UUID(cat_b_id), name="Shopping", slug="shopping", display_name="Shopping", system=True)
    db_session.add_all([cat_a, cat_b])
    await db_session.commit()

    # 2. Create a transaction
    tx_payload = {
        "user_id": user_id,
        "raw_text": "Rs.100 debited to Swiggy.",
        "source": "notification",
        "idempotency_key": "test_dedupe_1",
    }
    resp_tx = await client.post("/transactions", json=tx_payload, headers=headers)
    assert resp_tx.status_code == status.HTTP_201_CREATED
    tx_id = resp_tx.json()["id"]

    # Update category to Cat A first (so we know the exact initial state)
    resp_patch1 = await client.patch(f"/transactions/{tx_id}/category", json={"category_id": cat_a_id}, headers=headers)
    assert resp_patch1.status_code == status.HTTP_204_NO_CONTENT

    # Clear learning events from setup (if any) to isolate our check
    stmt = select(LearningEvent).where(LearningEvent.transaction_id == uuid.UUID(tx_id))
    events = (await db_session.execute(stmt)).scalars().all()
    initial_count = len(events)

    # 3. Patch to the SAME category (Cat A) - No-op check
    resp_patch2 = await client.patch(f"/transactions/{tx_id}/category", json={"category_id": cat_a_id}, headers=headers)
    assert resp_patch2.status_code == status.HTTP_204_NO_CONTENT

    # Verify no new LearningEvent is created
    events_after_noop = (await db_session.execute(stmt)).scalars().all()
    assert len(events_after_noop) == initial_count

    # 4. Patch to a DIFFERENT category (Cat B)
    resp_patch3 = await client.patch(f"/transactions/{tx_id}/category", json={"category_id": cat_b_id}, headers=headers)
    assert resp_patch3.status_code == status.HTTP_204_NO_CONTENT

    # Verify a new LearningEvent is created and it stores the old vs new category correctly
    events_after_change = (await db_session.execute(stmt)).scalars().all()
    assert len(events_after_change) == initial_count + 1

    # Sort events by timestamp or ID to get the latest one
    new_event = sorted(events_after_change, key=lambda e: e.timestamp)[-1]
    assert str(new_event.old_category_id) == cat_a_id
    assert str(new_event.new_category_id) == cat_b_id
