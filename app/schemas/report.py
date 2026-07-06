"""
app/schemas/report.py
─────────────────────────────────────────────────────────────────────────────
Pydantic response schemas for the reports endpoints matching Android UI.

MonthlyReportDto:       GET /reports/monthly/{user_id}
SubscriptionDto:        GET /reports/subscriptions/{user_id}
"""

from __future__ import annotations

from typing import Optional, List, Dict

from pydantic import BaseModel
from app.schemas.budget import BudgetSummaryResponse


# ── Monthly Report ────────────────────────────────────────────────────────────


class TransactionItemDto(BaseModel):
    id: str
    merchant: str
    amount_formatted: str
    date: str
    category: Optional[str]


class MonthlyReportDto(BaseModel):
    total_spend_formatted: str
    total_balance_formatted: str
    income_formatted: str
    savings_formatted: str
    spend_diff_text: str
    spend_diff_is_positive: bool
    categories: dict[str, float]
    recent_transactions: list[TransactionItemDto]


# ── Subscription Report ───────────────────────────────────────────────────────


class SubscriptionDto(BaseModel):
    id: str
    merchant: str
    amount_formatted: str
    next_billing_date: str
    countdown_days: int


class WeeklyActivityDto(BaseModel):
    average_per_day: float
    points: List[float]


class DashboardSummaryDto(BaseModel):
    total_balance: str
    monthly_income: str
    monthly_expense: str
    monthly_savings: str
    total_transactions: int
    latest_transactions: List[TransactionItemDto]
    top_categories: Dict[str, float]
    upcoming_subscriptions: List[SubscriptionDto]
    weekly_activity: WeeklyActivityDto
    budgets: List[BudgetSummaryResponse] = []
    ai_insights: Optional[str] = None
    saving_tips: Optional[str] = None


class CoachReportDto(BaseModel):
    insights: List[str]
    active_subscriptions: int
    financial_health_score: int
    budget_runout_days: Optional[int] = None
