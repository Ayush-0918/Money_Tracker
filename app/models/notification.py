"""
app/models/notification.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM models for FCM Device Tokens and Notifications history.
"""

import uuid
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User


class DeviceToken(Base, TimestampMixin):
    """Stores user device tokens for push notification routing."""
    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(20), default="android")  # "android", "ios"

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<DeviceToken user_id={self.user_id} device={self.device_type}>"


class Notification(Base, TimestampMixin):
    """Notification history and read status tracking."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(30), default="alert") # "alert", "insight", "subscription"
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} title={self.title} is_read={self.is_read}>"
