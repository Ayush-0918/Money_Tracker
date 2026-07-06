"""
app/models/budget.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `budgets` table.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category_id", name="uq_budget_user_category_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )
    monthly_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    cached_spent: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    cached_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User")
    category: Mapped["Category"] = relationship("Category")

    def __repr__(self) -> str:
        return f"<Budget id={self.id} category_id={self.category_id} limit={self.monthly_limit}>"
