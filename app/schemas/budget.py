"""
app/schemas/budget.py
─────────────────────────────────────────────────────────────────────────────
Pydantic schemas for Budgets.
"""

from typing import Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal


class BudgetStatusEnum(str, Enum):
    safe = "safe"
    warning = "warning"
    exceeded = "exceeded"


class BudgetCreate(BaseModel):
    category_id: UUID
    monthly_limit: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    monthly_limit: Decimal


class BudgetSummaryResponse(BaseModel):
    budget_id: UUID
    category_id: UUID
    monthly_limit: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: Optional[float]
    status: BudgetStatusEnum
    stale: bool
    suggestion: Optional[str]
