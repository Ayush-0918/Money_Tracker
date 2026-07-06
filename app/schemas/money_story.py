"""
app/schemas/money_story.py
─────────────────────────────────────────────────────────────────────────────
Pydantic response schemas for the Money Story endpoints.

MoneyStoryDto:  GET /money-story/{user_id}

The Money Story is the next evolution of the Weekly Report — a gamified,
AI-narrated 7-page interactive story experience surfaced every Sunday.
"""

from __future__ import annotations

from typing import List, Dict, Optional

from pydantic import BaseModel


# ── Badge ─────────────────────────────────────────────────────────────────────


class AchievementBadgeDto(BaseModel):
    """A single achievement badge earned this week."""

    id: str            # e.g. "saver_mode"
    label: str         # e.g. "Saver Mode"
    description: str   # e.g. "You spent less than last week"
    icon: str          # emoji or material icon name
    color: str         # hex color
    earned: bool       # True = displayed prominently


# ── Page-level DTOs ───────────────────────────────────────────────────────────


class MoneyScorePageDto(BaseModel):
    """Page 1 — Money Score ring + summary sentence."""

    money_score: int              # 0–100 gamified score
    score_label: str              # "Excellent" / "Good" / "Fair" / "Poor"
    score_color: str              # hex color for the ring
    score_headline: str           # e.g. "You're a Money Master this week! 🎯"
    show_confetti: bool           # True when score >= 80
    financial_mood: str           # e.g. "Saver Mode 🎯" / "Splurger Alert 🚨"
    mood_color: str               # hex color for mood badge


class SpendingPageDto(BaseModel):
    """Page 2 — Weekly Spending chart + comparison."""

    total_spend: float
    total_spend_formatted: str
    prior_week_spend: float
    prior_week_spend_formatted: str
    spend_change_pct: float
    spend_change_text: str
    spend_change_is_increase: bool
    daily_points: List[float]       # 7-point bar chart
    daily_labels: List[str]         # ["Mon", "Tue", …, "Sun"]
    average_per_day_formatted: str
    top_categories: Dict[str, float]
    top_categories_formatted: Dict[str, str]


class SavingsPageDto(BaseModel):
    """Page 3 — Savings progress ring."""

    savings_amount: float             # how much was NOT spent vs prior week
    savings_amount_formatted: str
    savings_vs_last_week: float       # delta (positive = saved more)
    savings_vs_last_week_formatted: str
    savings_is_positive: bool
    savings_headline: str             # e.g. "You saved ₹2,430 more than last week!"
    savings_trend: List[float]        # 7-point savings trend
    savings_rate_pct: float           # savings as % of income (0 if no income data)


class AchievementsPageDto(BaseModel):
    """Page 4 — Achievement badges + confetti."""

    badges: List[AchievementBadgeDto]
    earned_count: int
    show_confetti: bool      # True when earned_count >= 2
    headline: str            # e.g. "You earned 3 badges this week! 🏆"


class MistakesPageDto(BaseModel):
    """Page 5 — AI explains what went wrong."""

    worst_decision: str           # AI text: biggest financial mistake this week
    exceeded_budgets: List[str]   # category names that busted budget
    overspend_categories: List[str]  # categories with >30% increase vs last week
    improvement_tip: str          # single focused tip to fix the biggest mistake
    has_mistakes: bool            # False = show congratulations instead


class ForecastPageDto(BaseModel):
    """Page 6 — Next week spending forecast."""

    prediction_next_week: str        # AI-generated text prediction
    predicted_spend_formatted: str   # formatted predicted amount
    spend_trend_direction: str       # "up" / "down" / "stable"
    upcoming_subscriptions_count: int
    upcoming_subscriptions_total_formatted: str
    risk_level: str                  # "Low" / "Medium" / "High"
    risk_color: str                  # hex


class ActionPlanPageDto(BaseModel):
    """Page 7 — Personalized action plan."""

    ai_tips: List[str]             # 3-5 actionable tips
    best_decision: str             # AI text: best financial move this week
    weekly_challenge: str          # next week's personalized challenge
    share_card_text: str           # shareable summary text


# ── Main Money Story DTO ──────────────────────────────────────────────────────


class MoneyStoryDto(BaseModel):
    """
    Full AI Money Story returned by GET /money-story/{user_id}.

    Designed for a 7-page swipeable story experience on Android.
    """

    # Metadata
    week_label: str           # "30 Jun – 6 Jul 2025"
    generated_at: str         # ISO-8601 timestamp

    # 7 Pages
    page_score: MoneyScorePageDto
    page_spending: SpendingPageDto
    page_savings: SavingsPageDto
    page_achievements: AchievementsPageDto
    page_mistakes: MistakesPageDto
    page_forecast: ForecastPageDto
    page_action: ActionPlanPageDto

    # Dashboard preview card fields (shown on home screen before user taps in)
    card_headline: str          # "✨ Your Money Story is Ready"
    card_score: int             # money_score for the home card ring
    card_summary: str           # e.g. "You saved ₹2,430 more than last week."
    card_score_color: str       # hex color for the mini ring
    card_badge_count: int       # number of badges earned (shown as chip)
