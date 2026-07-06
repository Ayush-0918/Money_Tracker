"""
tests/test_family.py
─────────────────────────────────────────────────────────────────────────────
Unit & integration tests for collaborative Family Wallet services and endpoints.
"""

import uuid
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.family_service import (
    create_family_wallet,
    join_family_wallet,
    get_family_wallet,
    add_shared_expense,
    get_family_summary,
)


@pytest.mark.asyncio
async def test_create_family_wallet_creates_members():
    """create_family_wallet creates the wallet and registers the owner as member."""
    db = AsyncMock()
    owner_id = uuid.uuid4()
    wallet_name = "test_fam"

    # Mock DB query to say no existing wallet has the generated invite code
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    wallet = await create_family_wallet(db, owner_id, wallet_name)

    assert wallet.name == wallet_name
    assert wallet.owner_id == owner_id
    assert wallet.invite_code.startswith("FAM-")
    assert db.add.call_count == 2  # Added Wallet + Member


@pytest.mark.asyncio
async def test_join_family_wallet_success():
    """join_family_wallet adds a member to the wallet with invite code."""
    db = AsyncMock()
    user_id = uuid.uuid4()

    # Setup mock wallet query
    mock_wallet = MagicMock()
    mock_wallet.id = uuid.uuid4()
    mock_wallet.name = "test_fam"

    # First query for wallet, second query for member check (returns None)
    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = mock_wallet

    mock_res2 = MagicMock()
    mock_res2.scalar_one_or_none.return_value = None

    db.execute.side_effect = [mock_res1, mock_res2]

    wallet = await join_family_wallet(db, user_id, "FAM-12345")

    assert wallet.name == "test_fam"
    db.add.assert_called_once()  # Added FamilyMember


@pytest.mark.asyncio
async def test_join_family_wallet_already_member():
    """join_family_wallet raises ValueError if already a member."""
    db = AsyncMock()
    user_id = uuid.uuid4()

    mock_wallet = MagicMock()
    mock_wallet.id = uuid.uuid4()

    mock_res1 = MagicMock()
    mock_res1.scalar_one_or_none.return_value = mock_wallet

    # Member check returns existing member
    mock_res2 = MagicMock()
    mock_res2.scalar_one_or_none.return_value = MagicMock()

    db.execute.side_effect = [mock_res1, mock_res2]

    with pytest.raises(ValueError, match="already a member"):
        await join_family_wallet(db, user_id, "FAM-12345")


@pytest.mark.asyncio
async def test_get_family_wallet_access_denied():
    """get_family_wallet raises PermissionError if user is not in wallet."""
    db = AsyncMock()
    wallet_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Member check returns None
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(PermissionError, match="not a member"):
        await get_family_wallet(db, wallet_id, user_id)


# ── API Endpoint Tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_family_endpoints_unauthorized(client):
    """Anonymous requests to family endpoints must return 401/403."""
    response = await client.get("/family/wallets")
    assert response.status_code in [401, 403, 422]
