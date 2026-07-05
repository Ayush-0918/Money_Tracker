import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from collections.abc import AsyncGenerator
import uuid

from app.main import app
from app.database import get_db
from app.models import Base
from app.models.transaction import Transaction
from app.models.deleted_transaction import DeletedTransaction

# ── Test Database Setup ───────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
def admin_headers():
    return {"X-Admin-Key": "super_secret_admin_key_12345"}

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
    
    tx1 = Transaction(user_id=user_id, amount=500.0, merchant="Netflix", transaction_date=now, source="test", is_recurring=True, raw_text="test1")
    tx2 = Transaction(user_id=user_id, amount=500.0, merchant="netflix", transaction_date=now + timedelta(seconds=60), source="test", is_recurring=False, raw_text="test2")
    tx3 = Transaction(user_id=user_id, amount=501.0, merchant="Netflix", transaction_date=now, source="test", is_recurring=False, raw_text="test3")
    tx4 = Transaction(user_id=user_id, amount=500.0, merchant="Netflix", transaction_date=now + timedelta(seconds=130), source="test", is_recurring=False, raw_text="test4")
    
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
    
    tx1 = Transaction(user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now, source="test", raw_text="1")
    tx2 = Transaction(user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now + timedelta(seconds=10), source="test", raw_text="2")
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
    
    tx1 = Transaction(user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now, source="test", raw_text="1")
    tx2 = Transaction(user_id=user_id, amount=100.0, merchant="Amazon", transaction_date=now + timedelta(seconds=10), source="test", raw_text="2")
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
