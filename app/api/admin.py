from fastapi import APIRouter, Depends, Query, Body, Request
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import verify_admin_api_key
from app.schemas.admin import DuplicateReportResponse, DuplicateDeleteRequest, DuplicateDeleteResponse
from app.services import duplicate_cleanup_service
from app.utils.limiter import limiter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/duplicates", response_model=DuplicateReportResponse)
async def get_duplicates_all_users(db: AsyncSession = Depends(get_db), admin_key: str = Depends(verify_admin_api_key)):
    """Admin-only endpoint to report duplicates for ALL users."""
    return await duplicate_cleanup_service.get_duplicate_report(db, user_id=None)


@router.get("/duplicates/{user_id}", response_model=DuplicateReportResponse)
async def get_duplicates_for_user(
    user_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin_key: str = Depends(verify_admin_api_key)
):
    """Admin-only endpoint to report duplicates for a specific user."""
    return await duplicate_cleanup_service.get_duplicate_report(db, user_id=user_id)


@router.delete("/duplicates", response_model=DuplicateDeleteResponse)
@limiter.limit("5/minute")
async def delete_duplicates_all_users(
    request: Request,
    confirm: bool = Query(False, description="Set to true to actually delete. Otherwise, it's a dry run."),
    body_data: Optional[DuplicateDeleteRequest] = Body(None),
    db: AsyncSession = Depends(get_db),
    admin_key: str = Depends(verify_admin_api_key),
):
    """Delete duplicates across all users."""
    specific_ids = body_data.transaction_ids if body_data else None
    return await duplicate_cleanup_service.delete_duplicates(
        db, user_id=None, confirm=confirm, specific_ids=specific_ids
    )


@router.delete("/duplicates/{user_id}", response_model=DuplicateDeleteResponse)
@limiter.limit("5/minute")
async def delete_duplicates_for_user(
    user_id: uuid.UUID,
    request: Request,
    confirm: bool = Query(False, description="Set to true to actually delete. Otherwise, it's a dry run."),
    body_data: Optional[DuplicateDeleteRequest] = Body(None),
    db: AsyncSession = Depends(get_db),
    admin_key: str = Depends(verify_admin_api_key),
):
    """Delete duplicates for a specific user."""
    specific_ids = body_data.transaction_ids if body_data else None
    return await duplicate_cleanup_service.delete_duplicates(
        db, user_id=user_id, confirm=confirm, specific_ids=specific_ids
    )
