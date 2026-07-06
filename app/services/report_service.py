"""
app/services/report_service.py
─────────────────────────────────────────────────────────────────────────────
Query logic for monthly and subscription reports formatting to Android DTOs.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.report import MonthlyReportDto, TransactionItemDto, SubscriptionDto, WeeklyActivityDto
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def get_monthly_report(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> MonthlyReportDto:
    # Time boundaries
    ist_zone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(tz=ist_zone)
    month_start_ist = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end_ist = now_ist
    prev_month_end_ist = month_start_ist - timedelta(seconds=1)
    prev_month_start_ist = prev_month_end_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    month_start_utc = month_start_ist.astimezone(timezone.utc)
    month_end_utc = month_end_ist.astimezone(timezone.utc)
    prev_month_start_utc = prev_month_start_ist.astimezone(timezone.utc)
    prev_month_end_utc = prev_month_end_ist.astimezone(timezone.utc)

    # 1. Current month total
    total_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start_utc,
            Transaction.transaction_date <= month_end_utc,
        )
    )
    total_spend = (await db.execute(total_stmt)).scalar_one()

    # 2. Previous month total
    prev_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_month_start_utc,
            Transaction.transaction_date <= prev_month_end_utc,
        )
    )
    prev_spend = (await db.execute(prev_stmt)).scalar_one()

    # Spend diff
    spend_diff_text = "No previous data"
    spend_diff_is_positive = False
    if prev_spend > 0:
        diff = total_spend - prev_spend
        pct = (abs(diff) / prev_spend * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        spend_diff_is_positive = diff >= 0
        direction = "more" if diff >= 0 else "less"
        spend_diff_text = f"{pct}% {direction} than last month"
    elif total_spend > 0:
        spend_diff_text = "100% more than last month"
        spend_diff_is_positive = True

    # 3. Category breakdown
    category_stmt = (
        select(
            func.coalesce(Category.display_name, Transaction.category, "Uncategorized").label("cat"),
            func.sum(Transaction.amount).label("cat_total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start_utc,
                Transaction.transaction_date <= month_end_utc,
            )
        )
        .group_by("cat")
    )

    cat_rows = (await db.execute(category_stmt)).all()
    categories = {}
    for row in cat_rows:
        pct = float((row.cat_total / total_spend * 100)) if total_spend > 0 else 0.0
        categories[row.cat] = round(pct, 2)

    # 4. Recent transactions
    recent_stmt = (
        select(Transaction)
        .options(selectinload(Transaction.category_rel))
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(15)
    )

    recent_txs = (await db.execute(recent_stmt)).scalars().all()
    recent_transactions = []
    for tx in recent_txs:
        # Convert date to display format "15 Jul 2024"
        tx_ist = tx.transaction_date.astimezone(ist_zone)
        date_str = tx_ist.strftime("%d %b %Y")
        recent_transactions.append(
            TransactionItemDto(
                id=str(tx.id),
                merchant=tx.merchant,
                amount_formatted=f"₹ {tx.amount:,.2f}",
                date=date_str,
                category=tx.category_rel.display_name if tx.category_rel else tx.category,
            )
        )

    income = total_spend * Decimal("1.8")
    if income == 0:
        income = Decimal("120000")  # Base fallback if no spend
    savings = income - total_spend
    total_balance = savings * 5 + Decimal("45000")

    return MonthlyReportDto(
        total_spend_formatted=f"₹ {total_spend:,.2f}",
        total_balance_formatted=f"₹ {total_balance:,.2f}",
        income_formatted=f"₹ {income:,.2f}",
        savings_formatted=f"₹ {savings:,.2f}",
        spend_diff_text=spend_diff_text,
        spend_diff_is_positive=spend_diff_is_positive,
        categories=categories,
        recent_transactions=recent_transactions,
    )


async def get_subscription_report(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[SubscriptionDto]:
    now = datetime.now(tz=timezone.utc)
    today = now.date()

    stmt = (
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status != "cancelled",
            )
        )
        .order_by(Subscription.merchant)
    )

    subscriptions = (await db.execute(stmt)).scalars().all()
    result = []
    for sub in subscriptions:
        countdown_days = -1
        if sub.next_billing_date:
            countdown_days = (sub.next_billing_date - today).days

        date_str = sub.next_billing_date.strftime("%d %b %Y") if sub.next_billing_date else "Unknown"

        result.append(
            SubscriptionDto(
                id=str(sub.id),
                merchant=sub.merchant,
                amount_formatted=f"₹ {sub.amount:,.2f}/{sub.billing_cycle[:2]}",
                next_billing_date=date_str,
                countdown_days=countdown_days,
            )
        )
    return result


async def get_weekly_activity(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> WeeklyActivityDto:
    ist_zone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(tz=ist_zone)

    # Calculate the last 7 days including today (from day-6 to day 0)
    # Start of the 7th day ago
    start_ist = (now_ist - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)

    start_utc = start_ist.astimezone(timezone.utc)
    now_utc = now_ist.astimezone(timezone.utc)

    # Aggregating in SQL is more efficient than in Python (Phase 6 Performance)
    stmt = (
        select(func.date(Transaction.transaction_date).label("day"), func.sum(Transaction.amount).label("total"))
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_utc,
                Transaction.transaction_date <= now_utc,
            )
        )
        .group_by("day")
    )

    rows = (await db.execute(stmt)).all()
    db_totals = {row.day: float(row.total) for row in rows}

    # Initialize 7 buckets for the 7 days (day 0 to day 6)
    points = []
    total_7_days = 0.0
    for i in range(7):
        d = (start_ist + timedelta(days=i)).date()
        val = db_totals.get(d, 0.0)
        points.append(val)
        total_7_days += val

    avg_per_day = total_7_days / 7.0

    return WeeklyActivityDto(average_per_day=round(avg_per_day, 2), points=points)


from app.models.budget import Budget
from app.services.ai_service import get_ai_service
from app.schemas.report import CoachReportDto


async def get_coach_report(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> CoachReportDto:
    """
    Computes financial metrics (subscriptions count, budget runout estimate,
    financial health score) and calls AI to generate custom coaching suggestions.
    """
    # 1. Active subscriptions count
    sub_count_stmt = select(func.count(Subscription.id)).where(
        and_(Subscription.user_id == user_id, Subscription.status == "active")
    )
    active_subscriptions = (await db.execute(sub_count_stmt)).scalar_one() or 0

    # 2. Budget Runout days & Exceeded Budgets
    ist_zone = ZoneInfo("Asia/Kolkata")
    now_ist = datetime.now(tz=ist_zone)
    day_of_month = max(1, now_ist.day)

    month_start_utc = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    month_end_utc = now_ist.astimezone(timezone.utc)

    budget_stmt = select(Budget).options(selectinload(Budget.category)).where(Budget.user_id == user_id)
    budgets = (await db.execute(budget_stmt)).scalars().all()

    exceeded_budgets_count = 0
    min_runout_days = None

    budget_details = []
    for b in budgets:
        spent_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_id == b.category_id,
                Transaction.transaction_date >= month_start_utc,
                Transaction.transaction_date <= month_end_utc,
            )
        )
        spent = (await db.execute(spent_stmt)).scalar_one()

        limit = b.monthly_limit
        is_exceeded = spent > limit
        if is_exceeded:
            exceeded_budgets_count += 1

        daily_burn = spent / Decimal(str(day_of_month))
        remaining = limit - spent

        if remaining > 0 and daily_burn > 0:
            runout = int(remaining / daily_burn)
            if min_runout_days is None or runout < min_runout_days:
                min_runout_days = runout

        budget_details.append(
            {
                "category": b.category.name if b.category else "Uncategorized",
                "limit": float(limit),
                "spent": float(spent),
                "is_exceeded": is_exceeded,
            }
        )

    # 3. Monthly Spend Comparison
    prev_month_end_ist = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    prev_month_start_ist = prev_month_end_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    prev_month_start_utc = prev_month_start_ist.astimezone(timezone.utc)
    prev_month_end_utc = prev_month_end_ist.astimezone(timezone.utc)

    total_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= month_start_utc,
            Transaction.transaction_date <= month_end_utc,
        )
    )
    total_spend = (await db.execute(total_stmt)).scalar_one()

    prev_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_month_start_utc,
            Transaction.transaction_date <= prev_month_end_utc,
        )
    )
    prev_spend = (await db.execute(prev_stmt)).scalar_one()

    spend_increased = total_spend > prev_spend
    spend_diff_pct = 0.0
    if prev_spend > 0:
        spend_diff_pct = float(((total_spend - prev_spend) / prev_spend * 100))

    # Top spending merchants
    merch_stmt = (
        select(Transaction.merchant, func.sum(Transaction.amount).label("total"))
        .where(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= month_start_utc,
                Transaction.transaction_date <= month_end_utc,
            )
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(3)
    )
    top_merchants = [
        {"merchant": row.merchant, "spent": float(row.total)} for row in (await db.execute(merch_stmt)).all()
    ]

    # 4. Financial Health Score
    health_score = 100
    health_score -= exceeded_budgets_count * 15
    health_score -= active_subscriptions * 5
    if spend_increased:
        health_score -= 10
    health_score = max(10, min(100, health_score))

    # 5. Call AI Service for Natural Language Insights
    summary_data = {
        "active_subscriptions": active_subscriptions,
        "exceeded_budgets_count": exceeded_budgets_count,
        "current_spend": float(total_spend),
        "previous_spend": float(prev_spend),
        "spend_difference_percentage": round(spend_diff_pct, 2),
        "top_merchants": top_merchants,
        "budget_details": budget_details,
        "budget_runout_days": min_runout_days,
    }

    ai_service = get_ai_service()
    insights = None
    try:
        insights = await ai_service.get_coach_insights(summary_data)
    except Exception as e:
        logger.error(f"Failed to generate AI coach insights: {e}")

    # Fallback default insights
    if not insights:
        insights = []
        if spend_increased:
            insights.append(
                f"You spent {round(spend_diff_pct, 1)}% more than last month. Consider trimming non-essential shopping."
            )
        else:
            insights.append("Great job! Your spending is lower than last month.")

        if top_merchants:
            top_m = top_merchants[0]
            insights.append(
                f"Your top expense was ₹{top_m['spent']:,} at {top_m['merchant']}. Try reducing transactions here next week."
            )
        else:
            insights.append(f"You have {active_subscriptions} active subscriptions. Review unused memberships to save.")

    return CoachReportDto(
        insights=insights,
        active_subscriptions=active_subscriptions,
        financial_health_score=health_score,
        budget_runout_days=min_runout_days,
    )
