"""
app/services/money_story_service.py
─────────────────────────────────────────────────────────────────────────────
Generates the gamified, AI-powered Money Story (redefined Weekly Report).
Covers 7 interactive pages:
  1. Money Score + Financial Mood
  2. Weekly Spending (bar chart, categories, merchants)
  3. Savings progress (current vs last week)
  4. Achievements (gamified badges)
  5. Mistakes (AI narrative + budget exceeding)
  6. Next Week Forecast (upcoming bills, AI prediction)
  7. Action Plan (personalized tips, weekly challenge)
"""

import uuid
import datetime
from datetime import timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo
from typing import List, Dict, Optional, Any

from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.money_story import (
    MoneyStoryDto,
    MoneyScorePageDto,
    SpendingPageDto,
    SavingsPageDto,
    AchievementsPageDto,
    MistakesPageDto,
    ForecastPageDto,
    ActionPlanPageDto,
    AchievementBadgeDto,
)
from app.schemas.report import MerchantSpendDto, BudgetHealthDto, SubscriptionDto
from app.services.ai_service import get_ai_service
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _score_label(score: int) -> tuple[str, str]:
    """Return (label, hex_color) for a given money score."""
    if score >= 85:
        return "Excellent", "#4CAF7D"
    if score >= 70:
        return "Good", "#90CAF9"
    if score >= 50:
        return "Fair", "#F5A623"
    return "Poor", "#EF5350"


def _financial_mood(score: int, spend_decreased: bool) -> tuple[str, str]:
    """Return (mood_string, hex_color) based on financial behaviors."""
    if score >= 85 and spend_decreased:
        return "Super Saver 🎯", "#4CAF7D"
    if score >= 70:
        return "Balanced ⚖️", "#90CAF9"
    if score >= 50:
        return "Unstable 🌪️", "#F5A623"
    return "Spendthrift 🚨", "#EF5350"


async def generate_money_story(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> MoneyStoryDto:
    """
    Compute and return a full MoneyStoryDto for the given user.
    """
    ist_zone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.datetime.now(tz=ist_zone)

    # ── Time Boundaries ───────────────────────────────────────────────────────
    week_start_ist = (now_ist - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    prior_start_ist = week_start_ist - timedelta(days=7)
    prior_end_ist = week_start_ist - timedelta(seconds=1)

    week_start_utc = week_start_ist.astimezone(timezone.utc)
    now_utc = now_ist.astimezone(timezone.utc)
    prior_start_utc = prior_start_ist.astimezone(timezone.utc)
    prior_end_utc = prior_end_ist.astimezone(timezone.utc)

    week_label = f"{week_start_ist.strftime('%d %b')} – {now_ist.strftime('%d %b %Y')}"
    generated_at = now_ist.isoformat()

    # ── 1. Spend & Savings Logic ──────────────────────────────────────────────
    def _spend_stmt(start, end):
        return select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
            )
        )

    total_spend: Decimal = (await db.execute(_spend_stmt(week_start_utc, now_utc))).scalar_one()
    prior_spend: Decimal = (await db.execute(_spend_stmt(prior_start_utc, prior_end_utc))).scalar_one()

    # Spend comparison change
    spend_change_pct = 0.0
    spend_change_is_increase = False
    spend_change_text = "No change from last week"

    if prior_spend > 0:
        raw_pct = float(((total_spend - prior_spend) / prior_spend * 100))
        spend_change_pct = round(raw_pct, 2)
        direction = "more" if spend_change_pct >= 0 else "less"
        spend_change_text = f"{abs(spend_change_pct):.1f}% {direction} than last week"
        spend_change_is_increase = spend_change_pct >= 0
    elif total_spend > 0:
        spend_change_pct = 100.0
        spend_change_text = "100% more than last week"
        spend_change_is_increase = True

    # ── 2. Category Breakdown ─────────────────────────────────────────────────
    cat_stmt = (
        select(
            func.coalesce(Category.display_name, Transaction.category, "Uncategorized").label("cat"),
            func.sum(Transaction.amount).label("cat_total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= week_start_utc,
                Transaction.transaction_date <= now_utc,
            )
        )
        .group_by("cat")
        .order_by(func.sum(Transaction.amount).desc())
        .limit(6)
    )
    cat_rows = (await db.execute(cat_stmt)).all()
    top_categories: dict[str, float] = {}
    top_categories_formatted: dict[str, str] = {}
    for row in cat_rows:
        top_categories[row.cat] = float(row.cat_total)
        top_categories_formatted[row.cat] = f"₹ {row.cat_total:,.2f}"

    # ── 3. Top Merchants ──────────────────────────────────────────────────────
    merch_stmt = (
        select(Transaction.merchant, func.sum(Transaction.amount).label("total"))
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= week_start_utc,
                Transaction.transaction_date <= now_utc,
            )
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
    )
    merch_rows = (await db.execute(merch_stmt)).all()
    top_merchants = [
        MerchantSpendDto(
            rank=i + 1,
            merchant=row.merchant,
            amount=float(row.total),
            amount_formatted=f"₹ {row.total:,.2f}",
        )
        for i, row in enumerate(merch_rows)
    ]

    # ── 4. Daily Activity (7-point) ───────────────────────────────────────────
    daily_stmt = (
        select(func.date(Transaction.transaction_date).label("day"), func.sum(Transaction.amount).label("total"))
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= week_start_utc,
                Transaction.transaction_date <= now_utc,
            )
        )
        .group_by("day")
    )
    daily_rows = (await db.execute(daily_stmt)).all()
    db_daily: dict = {row.day: float(row.total) for row in daily_rows}

    daily_points: list[float] = []
    daily_labels: list[str] = []
    week_total_for_avg = 0.0
    active_days_count = 0
    for i in range(7):
        d = (week_start_ist + timedelta(days=i)).date()
        val = db_daily.get(d, 0.0)
        daily_points.append(val)
        week_total_for_avg += val
        if val > 0.0:
            active_days_count += 1
        daily_labels.append(_DAY_LABELS[d.weekday()])

    average_per_day = round(week_total_for_avg / 7.0, 2)
    average_per_day_formatted = f"₹ {average_per_day:,.2f}"

    # ── 5. Budget Health ──────────────────────────────────────────────────────
    budget_stmt = (
        select(Budget)
        .options(selectinload(Budget.category))
        .where(Budget.user_id == user_id)
    )
    budgets = (await db.execute(budget_stmt)).scalars().all()

    budget_health: list[BudgetHealthDto] = []
    exceeded_budget_count = 0
    exceeded_budget_categories = []
    total_budget_limit = Decimal("0")

    for b in budgets:
        cat_name = b.category.name if b.category else "Uncategorized"
        cat_id = b.category_id

        week_spent_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_id == cat_id,
                Transaction.transaction_date >= week_start_utc,
                Transaction.transaction_date <= now_utc,
            )
        )
        week_spent: Decimal = (await db.execute(week_spent_stmt)).scalar_one()

        weekly_limit = (b.monthly_limit / Decimal("4.33")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_budget_limit += weekly_limit

        pct_used = float((week_spent / weekly_limit * 100)) if weekly_limit > 0 else 0.0
        is_exceeded = week_spent > weekly_limit

        if is_exceeded:
            exceeded_budget_count += 1
            exceeded_budget_categories.append(cat_name)

        budget_health.append(
            BudgetHealthDto(
                category=cat_name,
                limit=float(weekly_limit),
                spent=float(week_spent),
                percent_used=round(pct_used, 1),
                is_exceeded=is_exceeded,
                limit_formatted=f"₹ {weekly_limit:,.2f}",
                spent_formatted=f"₹ {week_spent:,.2f}",
            )
        )

    # ── 6. Subscriptions (next 7 days) ────────────────────────────────────────
    today = now_ist.date()
    seven_days_later = today + timedelta(days=7)

    sub_stmt = (
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status != "cancelled",
                Subscription.next_billing_date != None,
                Subscription.next_billing_date >= today,
                Subscription.next_billing_date <= seven_days_later,
            )
        )
        .order_by(Subscription.next_billing_date)
    )
    subs = (await db.execute(sub_stmt)).scalars().all()
    upcoming_subscriptions = [
        SubscriptionDto(
            id=str(s.id),
            merchant=s.merchant,
            amount_formatted=f"₹ {s.amount:,.2f}/{s.billing_cycle[:2]}",
            next_billing_date=s.next_billing_date.strftime("%d %b %Y"),
            countdown_days=(s.next_billing_date - today).days,
        )
        for s in subs
    ]
    upcoming_subscriptions_count = len(subs)
    upcoming_subscriptions_total = sum(s.amount for s in subs)
    upcoming_subscriptions_total_formatted = f"₹ {upcoming_subscriptions_total:,.2f}"

    # ── 7. Money Score Calculation ────────────────────────────────────────────
    money_score = 100
    money_score -= exceeded_budget_count * 15
    money_score -= upcoming_subscriptions_count * 3
    if spend_change_is_increase and spend_change_pct > 15:
        money_score -= 10
    if average_per_day > 2000:
        money_score -= 5
    money_score = max(10, min(100, money_score))

    score_label, score_color = _score_label(money_score)
    mood, mood_color = _financial_mood(money_score, not spend_change_is_increase)

    # Headlines based on score
    if money_score >= 85:
        score_headline = "Excellent work! You're a money master this week. 🎯"
    elif money_score >= 70:
        score_headline = "Good job! A solid week of financial management. 👍"
    elif money_score >= 50:
        score_headline = "Fair performance. You have some room to improve. ⚖️"
    else:
        score_headline = "Tough week! Let's get your budget back on track. 🚨"

    # ── 8. Savings Page Calculations ──────────────────────────────────────────
    # Savings is calculated as prior week spend minus this week spend
    savings_vs_last_week = float(prior_spend - total_spend)
    savings_amount = max(0.0, savings_vs_last_week)
    savings_is_positive = savings_vs_last_week > 0

    savings_amount_formatted = f"₹ {savings_amount:,.2f}"
    savings_vs_last_week_formatted = f"₹ {abs(savings_vs_last_week):,.2f}"

    if savings_is_positive:
        savings_headline = f"You saved {savings_vs_last_week_formatted} more than last week!"
    else:
        savings_headline = f"You saved {savings_vs_last_week_formatted} less than last week."

    # Generate a savings trend array (mocking daily savings rate based on budget proportions)
    savings_trend = []
    for pt in daily_points:
        daily_limit = float(total_budget_limit / 7) if total_budget_limit > 0 else 1000.0
        daily_savings = max(0.0, daily_limit - pt)
        savings_trend.append(daily_savings)

    # ── 9. Gamified Achievement Badges ────────────────────────────────────────
    badges = []
    # Badge 1: Saver Mode
    badges.append(
        AchievementBadgeDto(
            id="saver_mode",
            label="Saver Mode",
            description="Spent less than last week",
            icon="💰",
            color="#4CAF7D",
            earned=not spend_change_is_increase and total_spend > 0,
        )
    )
    # Badge 2: Budget Master
    badges.append(
        AchievementBadgeDto(
            id="budget_master",
            label="Budget Master",
            description="No budget limits exceeded",
            icon="🛡️",
            color="#90CAF9",
            earned=exceeded_budget_count == 0 and len(budgets) > 0,
        )
    )
    # Badge 3: Frugal Frenzy
    badges.append(
        AchievementBadgeDto(
            id="frugal_frenzy",
            label="Frugal Frenzy",
            description="Average daily spend under ₹1,000",
            icon="⚡",
            color="#CE93D8",
            earned=average_per_day < 1000 and total_spend > 0,
        )
    )
    # Badge 4: Subscription Hunter
    badges.append(
        AchievementBadgeDto(
            id="subscription_hunter",
            label="Sub Hunter",
            description="Zero upcoming subscriptions due",
            icon="🎯",
            color="#F5A623",
            earned=upcoming_subscriptions_count == 0,
        )
    )
    # Badge 5: Consistent Tracker
    badges.append(
        AchievementBadgeDto(
            id="consistent_tracker",
            label="Consistent Tracker",
            description="Logged expenses on 5+ days",
            icon="🔥",
            color="#FF7043",
            earned=active_days_count >= 5,
        )
    )
    # Badge 6: Smart Shopper
    badges.append(
        AchievementBadgeDto(
            id="smart_shopper",
            label="Smart Shopper",
            description="Fewer than 4 transactions this week",
            icon="🛒",
            color="#AB47BC",
            earned=0 < len(top_merchants) < 4,
        )
    )

    earned_badges = [b for b in badges if b.earned]
    earned_count = len(earned_badges)
    show_confetti_badges = earned_count >= 2

    if earned_count > 0:
        badges_headline = f"You earned {earned_count} badges this week! 🏆"
    else:
        badges_headline = "No badges earned this week. Let's aim for one next week! 💪"

    # ── 10. AI Narrative Queries with fallback ────────────────────────────────
    ai_input = {
        "total_spend": float(total_spend),
        "prior_week_spend": float(prior_spend),
        "spend_change_pct": spend_change_pct,
        "top_categories": {k: round(v, 2) for k, v in list(top_categories.items())[:3]},
        "top_merchants": [m.merchant for m in top_merchants[:3]],
        "exceeded_budget_count": exceeded_budget_count,
        "upcoming_subscriptions_count": upcoming_subscriptions_count,
        "money_score": money_score,
    }

    ai_service = get_ai_service()
    ai_story = None

    try:
        ai_story = await ai_service.get_money_story_ai(ai_input)
    except Exception as e:
        logger.error(f"Money Story AI generation failed: {e}")

    # Fallback to rule-based insights if AI fails or returns empty
    if not ai_story:
        # Best decision rule
        if not spend_change_is_increase and total_spend > 0:
            best_decision = "You managed to cut down your overall expenses compared to last week. Splendid discipline!"
        elif exceeded_budget_count == 0 and len(budgets) > 0:
            best_decision = "You stayed 100% inside your budget boundaries this week. Excellent planning!"
        else:
            best_decision = "You kept your daily transaction counts low, avoiding impulse friction points."

        # Worst decision rule
        if exceeded_budget_count > 0:
            worst_decision = f"Exceeding your budget in {', '.join(exceeded_budget_categories[:2])} increased your wallet pressure."
        elif spend_change_is_increase and spend_change_pct > 20:
            worst_decision = f"Your weekly spending shot up by {spend_change_pct}%. Try to keep caps on non-essentials."
        else:
            worst_decision = "No major mistakes! Just watch out for small recurring subscriptions."

        # Prediction next week rule
        predicted_spend = float(total_spend) * (0.95 if not spend_change_is_increase else 1.05)
        predicted_spend_formatted = f"₹ {predicted_spend:,.2f}"
        prediction_next_week = f"Based on this week's trends, you are projected to spend around {predicted_spend_formatted} next week."

        # Action plan tips
        tips = []
        if exceeded_budget_count > 0:
            tips.append("Lower your daily budget limits by 10% next week to compensate for recent overruns.")
        if upcoming_subscriptions_count > 0:
            tips.append(f"Prepare ₹{upcoming_subscriptions_total:,.2f} for upcoming bills to avoid balance shocks.")
        if spend_change_is_increase:
            tips.append("Try a 'No-Spend Weekend' challenge next week to restore budget health.")
        if not tips:
            tips.append("Set aside 20% of your budget immediately into savings at the start of next week.")

        weekly_challenge = "Frugal Friday: Spend exactly ₹0 on non-essentials this coming Friday!"
    else:
        best_decision = ai_story.get("best_decision", "")
        worst_decision = ai_story.get("worst_decision", "")
        prediction_next_week = ai_story.get("prediction_next_week", "")
        tips = ai_story.get("tips", [])
        weekly_challenge = ai_story.get("weekly_challenge", "")

    # Calculate predicted spend
    predicted_spend = float(total_spend) * (0.95 if not spend_change_is_increase else 1.05)
    predicted_spend_formatted = f"₹ {predicted_spend:,.2f}"

    # Determine risk level
    if money_score >= 80:
        risk_level = "Low"
        risk_color = "#4CAF7D"
    elif money_score >= 60:
        risk_level = "Medium"
        risk_color = "#F5A623"
    else:
        risk_level = "High"
        risk_color = "#EF5350"

    # Headline formatting
    share_card_text = (
        f"My Sunday Money Story: Money Score of {money_score}/100! "
        f"Mood: {mood}. Total spend: {f'₹ {total_spend:,.2f}'}. #MoneyTracker"
    )

    # ── 11. Compose Story Pages ───────────────────────────────────────────────
    page_score = MoneyScorePageDto(
        money_score=money_score,
        score_label=score_label,
        score_color=score_color,
        score_headline=score_headline,
        show_confetti=(money_score >= 80),
        financial_mood=mood,
        mood_color=mood_color,
    )

    page_spending = SpendingPageDto(
        total_spend=float(total_spend),
        total_spend_formatted=f"₹ {total_spend:,.2f}",
        prior_week_spend=float(prior_spend),
        prior_week_spend_formatted=f"₹ {prior_spend:,.2f}",
        spend_change_pct=spend_change_pct,
        spend_change_text=spend_change_text,
        spend_change_is_increase=spend_change_is_increase,
        daily_points=daily_points,
        daily_labels=daily_labels,
        average_per_day_formatted=average_per_day_formatted,
        top_categories=top_categories,
        top_categories_formatted=top_categories_formatted,
    )

    page_savings = SavingsPageDto(
        savings_amount=savings_amount,
        savings_amount_formatted=savings_amount_formatted,
        savings_vs_last_week=savings_vs_last_week,
        savings_vs_last_week_formatted=savings_vs_last_week_formatted,
        savings_is_positive=savings_is_positive,
        savings_headline=savings_headline,
        savings_trend=savings_trend,
        savings_rate_pct=0.0,  # default placeholder until income streams are loaded
    )

    page_achievements = AchievementsPageDto(
        badges=badges,
        earned_count=earned_count,
        show_confetti=show_confetti_badges,
        headline=badges_headline,
    )

    page_mistakes = MistakesPageDto(
        worst_decision=worst_decision,
        exceeded_budgets=exceeded_budget_categories,
        overspend_categories=[cat for cat, amt in top_categories.items() if spend_change_is_increase and spend_change_pct > 30],
        improvement_tip=tips[0] if tips else "Track every expense instantly.",
        has_mistakes=(exceeded_budget_count > 0 or (spend_change_is_increase and spend_change_pct > 20)),
    )

    page_forecast = ForecastPageDto(
        prediction_next_week=prediction_next_week,
        predicted_spend_formatted=predicted_spend_formatted,
        spend_trend_direction="down" if not spend_change_is_increase else "up",
        upcoming_subscriptions_count=upcoming_subscriptions_count,
        upcoming_subscriptions_total_formatted=upcoming_subscriptions_total_formatted,
        risk_level=risk_level,
        risk_color=risk_color,
    )

    page_action = ActionPlanPageDto(
        ai_tips=tips,
        best_decision=best_decision,
        weekly_challenge=weekly_challenge,
        share_card_text=share_card_text,
    )

    return MoneyStoryDto(
        week_label=week_label,
        generated_at=generated_at,
        page_score=page_score,
        page_spending=page_spending,
        page_savings=page_savings,
        page_achievements=page_achievements,
        page_mistakes=page_mistakes,
        page_forecast=page_forecast,
        page_action=page_action,
        card_headline="✨ Your Money Story is Ready",
        card_score=money_score,
        card_summary=f"You saved {savings_vs_last_week_formatted} {'more' if savings_is_positive else 'less'} than last week.",
        card_score_color=score_color,
        card_badge_count=earned_count,
    )
