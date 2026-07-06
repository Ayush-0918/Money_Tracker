"""
app/schemas/notification.py
─────────────────────────────────────────────────────────────────────────────
Pydantic schemas for Device Registration and Notification histories.
"""

from __future__ import annotations

from datetime import datetime
import uuid

from pydantic import BaseModel


class DeviceTokenRegisterDto(BaseModel):
    token: str
    device_type: str = "android"  # "android", "ios"


class NotificationDto(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    notification_type: str         # "alert", "insight", "subscription"
    is_read: bool
    created_at: datetime
