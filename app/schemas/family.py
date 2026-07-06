"""
app/schemas/family.py
─────────────────────────────────────────────────────────────────────────────
Pydantic schemas for the collaborative Family Wallet feature.
"""

from __future__ import annotations

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid

from pydantic import BaseModel


class FamilyWalletCreateDto(BaseModel):
    name: str


class FamilyMemberDto(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: str          # "owner", "member"
    joined_at: datetime


class SharedExpenseCreateDto(BaseModel):
    amount: Decimal
    description: str
    category_id: Optional[uuid.UUID] = None


class SharedExpenseDto(BaseModel):
    id: uuid.UUID
    amount: float
    amount_formatted: str
    description: str
    paid_by_id: uuid.UUID
    paid_by_name: str
    category_id: Optional[uuid.UUID]
    category_name: Optional[str]
    transaction_date: datetime


class FamilyWalletDto(BaseModel):
    id: uuid.UUID
    name: str
    invite_code: str
    owner_id: uuid.UUID
    created_at: datetime
    members: List[FamilyMemberDto]
    expenses: List[SharedExpenseDto]
    total_spent: float
    total_spent_formatted: str


class FamilyLeaderboardItemDto(BaseModel):
    name: str
    rank: int
    saved_amount: float
    saved_amount_formatted: str
    avatar_emoji: str


class FamilySummaryDto(BaseModel):
    wallet_id: uuid.UUID
    name: str
    money_score: int
    leaderboard: List[FamilyLeaderboardItemDto]
    ai_insights: str
