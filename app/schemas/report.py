"""
app/schemas/report.py
─────────────────────────────────────────────────────────────────────────────
Pydantic response schemas for the reports endpoints matching Android UI.

MonthlyReportDto:       GET /reports/monthly/{user_id}
SubscriptionDto:        GET /reports/subscriptions/{user_id}
WeeklyReportDto:        GET /reports/weekly-report/{user_id}
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


# ── Weekly Financial Report ───────────────────────────────────────────────────


class MerchantSpendDto(BaseModel):
    """Ranked merchant spend entry."""

    rank: int
    merchant: str
    amount: float
    amount_formatted: str


class BudgetHealthDto(BaseModel):
    """Per-category budget health for the current week."""

    category: str
    limit: float
    spent: float
    percent_used: float
    is_exceeded: bool
    limit_formatted: str
    spent_formatted: str


class WeeklyReportDto(BaseModel):
    """
    Full AI-powered weekly financial report returned by
    GET /reports/weekly-report/{user_id}.
    """

    # Period labels
    week_label: str  # e.g. "30 Jun – 6 Jul 2025"
    generated_at: str  # ISO-8601 timestamp

    # Spend summary
    total_spend: float
    total_spend_formatted: str
    prior_week_spend: float
    prior_week_spend_formatted: str
    spend_change_pct: float  # positive = spent more, negative = spent less
    spend_change_text: str  # e.g. "12.5% more than last week"
    spend_change_is_increase: bool

    # Category breakdown (category_name -> amount)
    top_categories: Dict[str, float]
    top_categories_formatted: Dict[str, str]  # category_name -> "₹ 1,250.00"

    # Top merchants (ranked)
    top_merchants: List[MerchantSpendDto]

    # Daily activity (7 points, index 0 = 6 days ago, index 6 = today)
    daily_points: List[float]
    daily_labels: List[str]  # e.g. ["Mon", "Tue", ..., "Sun"]
    average_per_day: float
    average_per_day_formatted: str

    # Budget health
    budget_health: List[BudgetHealthDto]
    exceeded_budget_count: int

    # Subscriptions due within next 7 days
    upcoming_subscriptions: List[SubscriptionDto]

    # AI narrative
    ai_narrative: str  # 3-5 sentence personalized summary from AI
    ai_tips: List[str]  # 2-3 actionable tips

    # Financial health score
    financial_health_score: int  # 0-100
    health_score_label: str  # "Excellent" / "Good" / "Fair" / "Poor"
    health_score_color: str  # hex color for Android UI
