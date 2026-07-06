"""
app/models/family.py
─────────────────────────────────────────────────────────────────────────────
SQLAlchemy ORM models for Family Wallet collaborative finance.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class FamilyWallet(Base, TimestampMixin):
    __tablename__ = "family_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    members: Mapped[List["FamilyMember"]] = relationship("FamilyMember", back_populates="wallet", cascade="all, delete-orphan")
    expenses: Mapped[List["SharedExpense"]] = relationship("SharedExpense", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FamilyWallet id={self.id} name={self.name} invite_code={self.invite_code}>"


class FamilyMember(Base, TimestampMixin):
    __tablename__ = "family_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    family_wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="member")  # "owner", "member"

    wallet: Mapped["FamilyWallet"] = relationship("FamilyWallet", back_populates="members")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<FamilyMember id={self.id} user_id={self.user_id} role={self.role}>"


class SharedExpense(Base, TimestampMixin):
    __tablename__ = "shared_expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    family_wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    paid_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    wallet: Mapped["FamilyWallet"] = relationship("FamilyWallet", back_populates="expenses")
    paid_by: Mapped["User"] = relationship("User")
    category: Mapped[Optional["Category"]] = relationship("Category")

    def __repr__(self) -> str:
        return f"<SharedExpense id={self.id} amount={self.amount} desc={self.description[:20]}>"
