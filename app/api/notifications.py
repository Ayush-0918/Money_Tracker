"""
app/api/notifications.py
─────────────────────────────────────────────────────────────────────────────
API Endpoints for FCM Push device token registration and alerts history.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.schemas.notification import DeviceTokenRegisterDto, NotificationDto
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    summary="Register user FCM device push token",
)
async def register_device(
    dto: DeviceTokenRegisterDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        await notification_service.register_device_token(
            db, current_user_id, dto.token, dto.device_type
        )
        return {"status": "success", "message": "Device registered for push notifications."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=List[NotificationDto],
    status_code=status.HTTP_200_OK,
    summary="Get user notifications list",
)
async def get_notifications(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationDto]:
    return await notification_service.get_user_notifications(db, current_user_id)


@router.post(
    "/read",
    status_code=status.HTTP_200_OK,
    summary="Mark notifications as read",
)
async def read_notifications(
    ids: List[uuid.UUID],
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        count = await notification_service.mark_notifications_as_read(db, current_user_id, ids)
        return {"status": "success", "count": count, "message": f"{count} notifications marked as read."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
