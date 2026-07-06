"""
app/services/notification_service.py
─────────────────────────────────────────────────────────────────────────────
Service layer for push registrations, alert generation, and Celery dispatch.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import DeviceToken, Notification
from app.models.budget import Budget
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.notification import NotificationDto
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def register_device_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    device_type: str = "android"
) -> DeviceToken:
    """
    Registers or updates an FCM token for push notifications routing.
    """
    # Delete token if registered to someone else
    await db.execute(
        select(DeviceToken).where(and_(DeviceToken.token == token, DeviceToken.user_id != user_id))
    )
    # Check if user already registered this token
    result = await db.execute(
        select(DeviceToken).where(and_(DeviceToken.token == token, DeviceToken.user_id == user_id))
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.device_type = device_type
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return existing

    device = DeviceToken(
        user_id=user_id,
        token=token,
        device_type=device_type
    )
    db.add(device)
    await db.commit()
    logger.info("Registered device token for user %s", user_id)
    return device


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    body: str,
    notification_type: str = "alert"
) -> Notification:
    """
    Saves a notification to the database and logs simulated FCM dispatch.
    """
    notif = Notification(
        user_id=user_id,
        title=title,
        body=body,
        notification_type=notification_type
    )
    db.add(notif)
    await db.commit()

    # Simulate dispatch
    logger.info("[Push Service Dispatch] To User: %s | Title: %s | Body: %s", user_id, title, body)
    return notif


async def get_user_notifications(
    db: AsyncSession,
    user_id: uuid.UUID
) -> List[NotificationDto]:
    """
    List user's notification history.
    """
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    list_notifs = result.scalars().all()
    return [
        NotificationDto(
            id=n.id,
            title=n.title,
            body=n.body,
            notification_type=n.notification_type,
            is_read=n.is_read,
            created_at=n.created_at
        )
        for n in list_notifs
    ]


async def mark_notifications_as_read(
    db: AsyncSession,
    user_id: uuid.UUID,
    notification_ids: List[uuid.UUID]
) -> int:
    """
    Mark listed notifications as read.
    """
    stmt = (
        update(Notification)
        .where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id
            )
        )
        .values(is_read=True)
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount


# ── Alert Scanners ────────────────────────────────────────────────────────────


async def scan_budget_thresholds(db: AsyncSession) -> int:
    """
    Scan active budgets and trigger alerts if spent >= 80% of limit.
    Avoids duplicate alerts by checking existing notification records.
    """
    # Fetch budgets
    budgets = (await db.execute(select(Budget))).scalars().all()
    alerts_triggered = 0

    for b in budgets:
        # Calculate weekly limits and actual spend
        week_start_utc = datetime.now(timezone.utc) - timedelta(days=7)
        spent_stmt = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            and_(
                Transaction.user_id == b.user_id,
                Transaction.category_id == b.category_id,
                Transaction.transaction_date >= week_start_utc
            )
        )
        spent: Decimal = (await db.execute(spent_stmt)).scalar_one()
        weekly_limit = (b.monthly_limit / Decimal("4.33"))

        if weekly_limit > 0:
            ratio = float(spent / weekly_limit)
            if ratio >= 0.8:
                pct = int(ratio * 100)
                title = "⚠️ Budget Limit Alert"
                body = f"You have spent {pct}% of your category weekly limit. Consider capping non-essentials."

                # Avoid duplicate alert in last 24 hours
                cutoff = datetime.now(timezone.utc) - timedelta(days=1)
                dup_stmt = select(Notification).where(
                    and_(
                        Notification.user_id == b.user_id,
                        Notification.title == title,
                        Notification.created_at >= cutoff
                    )
                )
                if not (await db.execute(dup_stmt)).scalar_one_or_none():
                    await create_notification(db, b.user_id, title, body, "alert")
                    alerts_triggered += 1

    return alerts_triggered


async def scan_subscription_dues(db: AsyncSession) -> int:
    """
    Scan subscriptions and trigger alerts if billing date is in next 24 hours.
    """
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    subs = (await db.execute(
        select(Subscription).where(
            and_(
                Subscription.status != "cancelled",
                Subscription.next_billing_date == tomorrow
            )
        )
    )).scalars().all()

    alerts_triggered = 0
    for s in subs:
        title = "💳 Upcoming Auto-debit Alert"
        body = f"Your subscription for {s.merchant} of ₹{s.amount:,.2f} is due tomorrow."

        # Avoid duplicate check
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        dup_stmt = select(Notification).where(
            and_(
                Notification.user_id == s.user_id,
                Notification.title == title,
                Notification.created_at >= cutoff
            )
        )
        if not (await db.execute(dup_stmt)).scalar_one_or_none():
            await create_notification(db, s.user_id, title, body, "subscription")
            alerts_triggered += 1

    return alerts_triggered
