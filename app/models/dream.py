"""
app/models/dream.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM model for the `dreams` table (AI Dream Planner).
"""

import uuid
from typing import TYPE_CHECKING, Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User


class Dream(Base, TimestampMixin):
    __tablename__ = "dreams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_savings: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"))
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    weekly_saving_target: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"))
    monthly_saving_target: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"))
    status: Mapped[str] = mapped_column(String(20), default="active")  # "active", "completed"
    ai_roadmap_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Dream id={self.id} name={self.name} target={self.target_amount} progress={self.current_savings}>"
