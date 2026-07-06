import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.models.transaction import Transaction
from app.models.deleted_transaction import DeletedTransaction


@pytest.mark.asyncio
async def test_admin_auth_required(client: AsyncClient):
    response = await client.get("/admin/duplicates")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

    response = await client.get("/admin/duplicates", headers={"X-Admin-Key": "wrong_key"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid Admin API Key"


@pytest.mark.asyncio
async def test_duplicate_detection(client: AsyncClient, db_session: AsyncSession, admin_headers: dict):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    tx1 = Transaction(
        user_id=user_id,
        amount=500.0,
        merchant="Netflix",
        transaction_date=now,
        source="test",
        is_recurring=True,
        raw_text="test1",
    )
    tx2 = Transaction(
        user_id=user_id,
        amount=500.0,
        merchant="netflix",
        transaction_date=now + timedelta(seconds=60),
        source="test",
        is_recurring=False,
        raw_text="test2",
    )
    tx3 = Transaction(
        user_id=user_id,
        amount=501.0,
        merchant="Netflix",
        transaction_date=now,
        source="test",
        is_recurring=False,
        raw_text="test3",
    )
    tx4 = Transaction(
        user_id=user_id,
        amount=500.0,
        merchant="Netflix",
        transaction_date=now + timedelta(seconds=130),
        source="test",
        is_recurring=False,
        raw_text="test4",
    )

    db_session.add_all([tx1, tx2, tx3, tx4])
    await db_session.commit()

    response = await client.get(f"/admin/duplicates/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_groups"] == 1
    assert data["total_duplicates"] == 1
    group = data["groups"][0]

    assert group["original"]["amount"] == 500.0
    assert group["original"]["is_recurring"] == True
    assert len(group["duplicates"]) == 1


@pytest.mark.asyncio
async def test_duplicate_delete_dry_run(client: AsyncClient, db_session: AsyncSession, admin_headers: dict):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    tx1 = Transaction(
        user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now, source="test", raw_text="1"
    )
    tx2 = Transaction(
        user_id=user_id,
        amount=100.0,
        merchant="Amazon",
        transaction_date=now + timedelta(seconds=10),
        source="test",
        raw_text="2",
    )
    db_session.add_all([tx1, tx2])
    await db_session.commit()

    response = await client.delete(f"/admin/duplicates/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["dry_run"] is True
    assert data["deleted_count"] == 1

    result = await db_session.execute(select(func.count(Transaction.id)).where(Transaction.user_id == user_id))
    assert result.scalar() == 2


@pytest.mark.asyncio
async def test_duplicate_delete_confirm(client: AsyncClient, db_session: AsyncSession, admin_headers: dict):
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    tx1 = Transaction(
        user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now, source="test", raw_text="1"
    )
    tx2 = Transaction(
        user_id=user_id,
        amount=100.0,
        merchant="Amazon",
        transaction_date=now + timedelta(seconds=10),
        source="test",
        raw_text="2",
    )
    db_session.add_all([tx1, tx2])
    await db_session.commit()

    response = await client.delete(f"/admin/duplicates/{user_id}?confirm=true", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["dry_run"] is False
    assert data["deleted_count"] == 1

    deleted_id = data["deleted_ids"][0]

    result = await db_session.execute(select(func.count(Transaction.id)).where(Transaction.user_id == user_id))
    assert result.scalar() == 1

    backup_result = await db_session.execute(select(DeletedTransaction).where(DeletedTransaction.user_id == user_id))
    backup = backup_result.scalars().first()
    assert backup is not None
    assert backup.reason == "duplicate_cleanup"
    assert str(backup.original_transaction_id) != deleted_id
