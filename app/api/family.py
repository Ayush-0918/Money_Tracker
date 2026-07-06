"""
app/api/family.py
─────────────────────────────────────────────────────────────────────────────
API Endpoints for collaborative Family Wallet operations.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.family import (
    FamilyWalletCreateDto,
    FamilyWalletDto,
    SharedExpenseCreateDto,
    SharedExpenseDto,
    FamilySummaryDto,
)
from app.services import family_service

router = APIRouter(prefix="/family", tags=["Family Wallet"])


@router.post(
    "/create",
    response_model=FamilyWalletDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Family Wallet",
)
async def create_wallet(
    dto: FamilyWalletCreateDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> FamilyWalletDto:
    try:
        wallet = await family_service.create_family_wallet(db, current_user_id, dto.name)
        return await family_service.get_family_wallet(db, wallet.id, current_user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/join",
    response_model=FamilyWalletDto,
    status_code=status.HTTP_200_OK,
    summary="Join a Family Wallet via invite code",
)
async def join_wallet(
    invite_code: str,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> FamilyWalletDto:
    try:
        wallet = await family_service.join_family_wallet(db, current_user_id, invite_code.strip())
        return await family_service.get_family_wallet(db, wallet.id, current_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/wallets",
    response_model=List[FamilyWalletDto],
    status_code=status.HTTP_200_OK,
    summary="List user's Family Wallets",
)
async def list_wallets(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[FamilyWalletDto]:
    return await family_service.get_user_family_wallets(db, current_user_id)


@router.get(
    "/{wallet_id}",
    response_model=FamilyWalletDto,
    status_code=status.HTTP_200_OK,
    summary="Get Family Wallet details",
)
async def get_wallet_details(
    wallet_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> FamilyWalletDto:
    try:
        return await family_service.get_family_wallet(db, wallet_id, current_user_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_430_FORBIDDEN if hasattr(status, "HTTP_430_FORBIDDEN") else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{wallet_id}/expense",
    response_model=SharedExpenseDto,
    status_code=status.HTTP_201_CREATED,
    summary="Add a split expense to Family Wallet",
)
async def add_expense(
    wallet_id: uuid.UUID,
    dto: SharedExpenseCreateDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> SharedExpenseDto:
    try:
        expense = await family_service.add_shared_expense(
            db, current_user_id, wallet_id, dto.amount, dto.description, dto.category_id
        )
        # Fetch fresh details to find user and category names
        wallet_dto = await family_service.get_family_wallet(db, wallet_id, current_user_id)
        for e in wallet_dto.expenses:
            if e.id == expense.id:
                return e
        raise HTTPException(status_code=500, detail="Failed to fetch registered expense.")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{wallet_id}/summary",
    response_model=FamilySummaryDto,
    status_code=status.HTTP_200_OK,
    summary="Get collaborative AI summary & leaderboard",
)
async def get_summary(
    wallet_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> FamilySummaryDto:
    try:
        return await family_service.get_family_summary(db, wallet_id, current_user_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
