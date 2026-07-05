"""
app/models/category.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `categories` table.
Reference table for transaction categorization.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

if TYPE_CHECKING:
    from app.models.user import User

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False, doc="Canonical machine key, e.g. 'food'")
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, doc="Immutable URL-safe identifier")
    display_name: Mapped[str] = mapped_column(String, nullable=False, doc="Shown in UI, e.g. 'Food & Dining'")
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    parent_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r} system={self.system}>"
