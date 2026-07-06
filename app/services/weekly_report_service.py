"""
app/services/weekly_report_service.py
─────────────────────────────────────────────────────────────────────────────
Generates the AI-powered Weekly Financial Report for a given user.

Covers:
  - 7-day spend vs prior-7-day spend (% change)
  - Category breakdown (ranked)
  - Merchant ranking (top 5)
  - Daily 7-point activity data
  - Budget health per category
  - Subscriptions due within the next 7 days
  - AI-generated narrative + tips (with rule-based fallback)
  - Financial health score (0-100)
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.report import (
    WeeklyReportDto,
    MerchantSpendDto,
    BudgetHealthDto,
    SubscriptionDto,
)
from app.services.ai_service import get_ai_service
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Day-of-week short labels (Monday = 0)
_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _health_label(score: int) -> tuple[str, str]:
    """Return (label, hex_color) for a given health score."""
    if score >= 80:
        return "Excellent", "#4CAF7D"
    if score >= 60:
        return "Good", "#90CAF9"
    if score >= 40:
        return "Fair", "#F5A623"
    return "Poor", "#EF5350"


async def generate_weekly_report(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> WeeklyReportDto:
    """
    Compute and return a full WeeklyReportDto for the given user.

    All monetary sums are in Decimal/float (INR).
    Times are handled in IST (Asia/Kolkata) for display, UTC for DB queries.
    """
    ist_zone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(tz=ist_zone)

    # ── Time Boundaries ───────────────────────────────────────────────────────
    # Current week: last 7 days (day-6 at 00:00 → now)
    week_start_ist = (now_ist - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    # Prior week: 14 days ago → 7 days ago
    prior_start_ist = week_start_ist - timedelta(days=7)
    prior_end_ist = week_start_ist - timedelta(seconds=1)

    week_start_utc = week_start_ist.astimezone(timezone.utc)
    now_utc = now_ist.astimezone(timezone.utc)
    prior_start_utc = prior_start_ist.astimezone(timezone.utc)
    prior_end_utc = prior_end_ist.astimezone(timezone.utc)

    # Human-readable week label e.g. "30 Jun – 6 Jul 2025"
    week_label = f"{week_start_ist.strftime('%d %b')} – {now_ist.strftime('%d %b %Y')}"
    generated_at = now_ist.isoformat()

    # ── 1. Total Spend — Current & Prior Week ─────────────────────────────────
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

    # Spend change
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
    else:
        spend_change_pct = 0.0
        spend_change_text = "No change from last week"
        spend_change_is_increase = False

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
    for i in range(7):
        d = (week_start_ist + timedelta(days=i)).date()
        val = db_daily.get(d, 0.0)
        daily_points.append(val)
        week_total_for_avg += val
        daily_labels.append(_DAY_LABELS[d.weekday()])

    average_per_day = round(week_total_for_avg / 7.0, 2)

    # ── 5. Budget Health ──────────────────────────────────────────────────────
    budget_stmt = (
        select(Budget)
        .options(selectinload(Budget.category))
        .where(Budget.user_id == user_id)
    )
    budgets = (await db.execute(budget_stmt)).scalars().all()

    budget_health: list[BudgetHealthDto] = []
    exceeded_budget_count = 0

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

        # Use weekly proportion of monthly limit (limit / 4.33 ≈ weekly budget)
        weekly_limit = (b.monthly_limit / Decimal("4.33")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pct_used = float((week_spent / weekly_limit * 100)) if weekly_limit > 0 else 0.0
        is_exceeded = week_spent > weekly_limit

        if is_exceeded:
            exceeded_budget_count += 1

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

    # ── 6. Upcoming Subscriptions (next 7 days) ───────────────────────────────
    today = now_ist.date()
    seven_days_later = today + timedelta(days=7)

    sub_stmt = (
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status != "cancelled",
                Subscription.next_billing_date != None,  # noqa: E711
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
    active_sub_count = len(subs)

    # ── 7. Financial Health Score ─────────────────────────────────────────────
    health_score = 100
    health_score -= exceeded_budget_count * 15
    health_score -= active_sub_count * 3
    if spend_change_is_increase and spend_change_pct > 20:
        health_score -= 10
    health_score = max(10, min(100, health_score))
    health_label, health_color = _health_label(health_score)

    # ── 8. AI Narrative (with rule-based fallback) ────────────────────────────
    ai_summary_input = {
        "total_spend": float(total_spend),
        "prior_week_spend": float(prior_spend),
        "spend_change_pct": spend_change_pct,
        "top_categories": {k: round(v, 2) for k, v in list(top_categories.items())[:3]},
        "top_merchants": [m.merchant for m in top_merchants[:3]],
        "exceeded_budget_count": exceeded_budget_count,
        "active_subscriptions": active_sub_count,
        "financial_health_score": health_score,
    }

    ai_service = get_ai_service()
    ai_narrative = ""
    ai_tips: list[str] = []

    try:
        result = await ai_service.get_weekly_narrative(ai_summary_input)
        if result:
            ai_narrative = result.get("narrative", "")
            ai_tips = result.get("tips", [])
    except Exception as e:
        logger.error(f"Weekly report AI narrative failed: {e}")

    # Rule-based fallback if AI returns nothing
    if not ai_narrative:
        if total_spend == 0:
            ai_narrative = (
                "You had no recorded expenses this week — either you were very frugal or your transactions "
                "haven't been synced yet. Keep tracking your spending to unlock personalized insights."
            )
        else:
            direction_word = "increased" if spend_change_is_increase else "decreased"
            ai_narrative = (
                f"This week you spent ₹{total_spend:,.2f}, which has {direction_word} by "
                f"{abs(spend_change_pct):.1f}% compared to last week. "
            )
            if top_categories:
                top_cat = next(iter(top_categories))
                ai_narrative += (
                    f"Your highest spending category was {top_cat} "
                    f"(₹{top_categories[top_cat]:,.2f}). "
                )
            ai_narrative += (
                f"Your financial health score is {health_score}/100 ({health_label}). "
                "Keep monitoring your budgets to stay on track."
            )

    if not ai_tips:
        ai_tips = []
        if exceeded_budget_count > 0:
            ai_tips.append(f"You exceeded {exceeded_budget_count} budget(s) this week — review your limits.")
        if active_sub_count > 0:
            ai_tips.append(f"You have {active_sub_count} subscription(s) due soon — check for unused ones.")
        if spend_change_is_increase and spend_change_pct > 10:
            ai_tips.append("Consider setting a weekly spending cap to avoid end-of-month surprises.")
        if not ai_tips:
            ai_tips.append("Great financial discipline! Keep your budget limits in check.")

    return WeeklyReportDto(
        week_label=week_label,
        generated_at=generated_at,
        total_spend=float(total_spend),
        total_spend_formatted=f"₹ {total_spend:,.2f}",
        prior_week_spend=float(prior_spend),
        prior_week_spend_formatted=f"₹ {prior_spend:,.2f}",
        spend_change_pct=spend_change_pct,
        spend_change_text=spend_change_text,
        spend_change_is_increase=spend_change_is_increase,
        top_categories=top_categories,
        top_categories_formatted=top_categories_formatted,
        top_merchants=top_merchants,
        daily_points=daily_points,
        daily_labels=daily_labels,
        average_per_day=average_per_day,
        average_per_day_formatted=f"₹ {average_per_day:,.2f}",
        budget_health=budget_health,
        exceeded_budget_count=exceeded_budget_count,
        upcoming_subscriptions=upcoming_subscriptions,
        ai_narrative=ai_narrative,
        ai_tips=ai_tips,
        financial_health_score=health_score,
        health_score_label=health_label,
        health_score_color=health_color,
    )
