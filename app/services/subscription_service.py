"""
app/services/subscription_service.py
─────────────────────────────────────────────────────────────────────────────
Recurring transaction detection and subscription management.

Detection Algorithm (clearly specified — no ambiguity):
  Given a new (merchant, amount, date) triple for a user:
  1. Fetch the last 5 transactions for the EXACT same merchant name.
  2. If fewer than 2 prior transactions exist → not enough data, skip.
  3. Amount proximity check:
       All prior amounts must be within ±10% of the current amount.
       Formula: lower = current * 0.90, upper = current * 1.10
       Rationale: Indian subscriptions vary due to GST changes, price hikes,
       or currency rounding. ±5% was too tight; ±10% is the sweet spot.
       Example: ₹499 and ₹549 (Spotify GST) → 10% gap → accepted.
  4. Time gap check (monthly cycle detection):
       Compute gaps (in days) between consecutive transaction dates.
       Average gap must be between 25 and 35 days (inclusive).
       25 days minimum: short months (Feb) or early billing.
       35 days maximum: billing date drift, weekends, bank delays.
       This range covers ONLY monthly billing. Weekly (7 days) and yearly
       (365 days) detection is reserved for Phase 3.
  5. If both checks pass → mark as recurring, upsert subscriptions table.

Currency assumption: INR only. All amounts treated as Indian Rupees.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# ── Recurring Detection Thresholds (explicit, documented) ────────────────────
# Change these only with corresponding test updates.
_MIN_PRIOR_TRANSACTIONS = 2
"""Minimum number of prior transactions required to detect a recurring pattern.
Set to 2: with only 1 prior, we cannot compute a meaningful time gap."""

_AMOUNT_TOLERANCE_PERCENT = Decimal("0.10")
"""Amount must be within ±10% of prior transactions to be considered the same
subscription. Covers GST changes, price adjustments, rounding. NOT ±5%."""

_MIN_GAP_DAYS = 25
"""Minimum average gap (days) between transactions to classify as monthly.
Covers February (28 days) and early billing cycles."""

_MAX_GAP_DAYS = 35
"""Maximum average gap (days) between transactions to classify as monthly.
Covers billing date drift, weekends, bank processing delays."""


async def check_and_update_recurring(
    db: AsyncSession,
    user_id: uuid.UUID,
    merchant: str,
    amount: Decimal,
    transaction_date: datetime,
) -> bool:
    """
    Detect if this transaction is part of a recurring subscription pattern.

    If recurring is detected, upsert a subscription record for this
    (user_id, merchant) pair and return True.

    Args:
        db:               Async database session.
        user_id:          UUID of the transaction owner.
        merchant:         Parsed merchant name (normalised/title-cased).
        amount:           Parsed transaction amount (Decimal).
        transaction_date: When this transaction occurred.

    Returns:
        True if this transaction was classified as recurring, False otherwise.
    """
    # Fetch last 5 prior transactions for this merchant (excluding current one
    # which hasn't been committed yet — we flush()ed but not committed)
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.merchant == merchant,
        )
        .order_by(Transaction.transaction_date.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    prior_transactions = result.scalars().all()

    if len(prior_transactions) < _MIN_PRIOR_TRANSACTIONS:
        logger.debug(
            "subscription_service: insufficient prior transactions for recurring "
            "check | merchant=%r | prior_count=%d",
            merchant,
            len(prior_transactions),
        )
        return False

    # ── Amount Proximity Check ─────────────────────────────────────────────────
    lower_bound = amount * (1 - _AMOUNT_TOLERANCE_PERCENT)
    upper_bound = amount * (1 + _AMOUNT_TOLERANCE_PERCENT)

    amounts_in_range = all(lower_bound <= txn.amount <= upper_bound for txn in prior_transactions)
    if not amounts_in_range:
        logger.debug(
            "subscription_service: amount variance too high — not recurring | " "merchant=%r | current_amount=%s",
            merchant,
            amount,
        )
        return False

    # ── Time Gap Check ─────────────────────────────────────────────────────────
    # Sort dates chronologically (oldest first) and compute gaps
    dates = sorted(
        [txn.transaction_date for txn in prior_transactions],
        reverse=False,  # oldest → newest
    )
    # Include the current transaction date for gap calculation
    all_dates = dates + [transaction_date]
    all_dates_sorted = sorted(all_dates)

    gaps: list[int] = []
    for i in range(1, len(all_dates_sorted)):
        gap = (all_dates_sorted[i] - all_dates_sorted[i - 1]).days
        gaps.append(gap)

    if not gaps:
        return False

    avg_gap = sum(gaps) / len(gaps)
    if not (_MIN_GAP_DAYS <= avg_gap <= _MAX_GAP_DAYS):
        logger.debug(
            "subscription_service: average gap %d days outside monthly range " "[%d, %d] | merchant=%r",
            avg_gap,
            _MIN_GAP_DAYS,
            _MAX_GAP_DAYS,
            merchant,
        )
        return False

    # ── Recurring Pattern Confirmed — Upsert Subscription ────────────────────
    logger.info(
        "subscription_service: recurring pattern detected | merchant=%r | " "avg_gap_days=%.1f | amount=%s",
        merchant,
        avg_gap,
        amount,
    )

    next_billing = _estimate_next_billing(transaction_date, billing_cycle="monthly")
    await _upsert_subscription(
        db=db,
        user_id=user_id,
        merchant=merchant,
        amount=amount,
        billing_cycle="monthly",
        next_billing_date=next_billing,
    )

    return True


async def _upsert_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    merchant: str,
    amount: Decimal,
    billing_cycle: str,
    next_billing_date: date | None,
) -> None:
    """
    Insert a new subscription or update the existing one for this
    (user_id, merchant) pair.

    Uses PostgreSQL's INSERT ... ON CONFLICT DO UPDATE for an atomic upsert.
    This avoids race conditions if two transactions arrive simultaneously.

    Args:
        db:               Async database session.
        user_id:          UUID of the subscription owner.
        merchant:         Merchant/service name.
        amount:           Latest known billing amount.
        billing_cycle:    'monthly', 'weekly', or 'yearly'.
        next_billing_date: Estimated next charge date.
    """
    stmt = (
        pg_insert(Subscription)
        .values(
            user_id=user_id,
            merchant=merchant,
            amount=amount,
            billing_cycle=billing_cycle,
            next_billing_date=next_billing_date,
            status="active",
        )
        .on_conflict_do_update(
            index_elements=["user_id", "merchant"],  # unique constraint columns
            set_={
                "amount": amount,
                "billing_cycle": billing_cycle,
                "next_billing_date": next_billing_date,
                "status": "active",  # Reactivate if was paused/cancelled
            },
        )
    )
    await db.execute(stmt)
    logger.info(
        "subscription_service: subscription upserted | user_id=%s | merchant=%r | " "next_billing=%s",
        user_id,
        merchant,
        next_billing_date,
    )


def _estimate_next_billing(last_date: datetime, billing_cycle: str) -> date:
    """
    Estimate the next billing date based on the last transaction and billing cycle.

    Args:
        last_date:     Date of the most recent charge.
        billing_cycle: 'monthly', 'weekly', or 'yearly'.

    Returns:
        Estimated next billing date as a date object.
    """
    cycle_days = {
        "monthly": 30,
        "weekly": 7,
        "yearly": 365,
    }
    days = cycle_days.get(billing_cycle, 30)
    return (last_date + timedelta(days=days)).date()
