"""
app/worker.py
─────────────────────────────────────────────────────────────────────────────
Celery worker and beat-scheduler configuration.

Registered tasks:
  - generate_ai_coach_insights  (on-demand)
  - weekly_financial_report     (Celery Beat: every Sunday 09:00 IST → 03:30 UTC)
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery("tasks", broker=settings.CELERY_BROKER_URL, backend=settings.REDIS_URL)

# ── Celery Configuration ──────────────────────────────────────────────────────
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # ── Beat Schedule ─────────────────────────────────────────────────────────
    # Weekly Financial Report — every Sunday at 09:00 IST (03:30 UTC)
    beat_schedule={
        "weekly-financial-report-sunday": {
            "task": "generate_weekly_financial_report",
            "schedule": crontab(hour=3, minute=30, day_of_week=0),  # Sunday 03:30 UTC = 09:00 IST
        },
        "money-story-sunday": {
            "task": "generate_sunday_money_story",
            "schedule": crontab(hour=3, minute=30, day_of_week=0),  # Sunday 03:30 UTC = 09:00 IST
        },
        "scan-budgets-beat": {
            "task": "scan_budgets_task",
            "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
        },
        "scan-subscriptions-beat": {
            "task": "scan_subscriptions_task",
            "schedule": crontab(minute=30, hour=1),  # daily at 01:30 UTC
        },
    },
)


# ── Tasks ─────────────────────────────────────────────────────────────────────


@celery_app.task(name="generate_ai_coach_insights")
def generate_ai_coach_insights(user_id: str):
    """
    Celery task running in a separate worker container to handle heavy
    background processing (e.g. calculating financial insights or reports).
    """
    print(f"[Celery Worker] Generating coach insights task triggered for user: {user_id}")
    # In future development phases, this will write results directly to a Cache/DB.
    return f"Completed insights generation for user {user_id}"


@celery_app.task(name="generate_weekly_financial_report")
def generate_weekly_financial_report():
    """
    Celery Beat task — runs every Sunday at 09:00 IST (03:30 UTC).

    Pre-computes and caches the AI Weekly Financial Report for all active users,
    so the first Android request on Monday morning returns instantly from Redis.

    Full async execution is handled inside an event loop; Celery tasks are
    synchronous wrappers around the async service layer.
    """
    import asyncio
    import uuid as _uuid

    async def _run():
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy import select, text

        from app.models.user import User
        from app.services.weekly_report_service import generate_weekly_report
        from app.config import settings as _cfg

        engine = create_async_engine(_cfg.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(select(User.id))
            user_ids = result.scalars().all()

        processed = 0
        for uid in user_ids:
            try:
                async with async_session() as session:
                    report = await generate_weekly_report(db=session, user_id=uid)

                # Write to Redis cache
                try:
                    import redis as sync_redis
                    import json

                    r = sync_redis.from_url(_cfg.REDIS_URL, decode_responses=True)
                    key = f"weekly_report:{uid}"
                    r.setex(key, 3600, report.model_dump_json())
                    processed += 1
                except Exception as cache_err:
                    print(f"[WeeklyReport] Redis cache write failed for {uid}: {cache_err}")
            except Exception as e:
                print(f"[WeeklyReport] Failed for user {uid}: {e}")

        await engine.dispose()
        return processed

    count = asyncio.run(_run())
    print(f"[WeeklyReport] Sunday pre-computation complete. Reports generated: {count}")
    return f"Weekly reports pre-computed for {count} users"


@celery_app.task(name="generate_sunday_money_story")
def generate_sunday_money_story():
    """
    Celery Beat task — runs every Sunday at 09:00 IST (03:30 UTC).

    Pre-computes and caches the Sunday Money Story for all active users.
    """
    import asyncio
    import uuid as _uuid

    async def _run():
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy import select

        from app.models.user import User
        from app.services.money_story_service import generate_money_story
        from app.config import settings as _cfg

        engine = create_async_engine(_cfg.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(select(User.id))
            user_ids = result.scalars().all()

        processed = 0
        for uid in user_ids:
            try:
                async with async_session() as session:
                    story = await generate_money_story(db=session, user_id=uid)

                # Write to Redis cache
                try:
                    import redis as sync_redis
                    r = sync_redis.from_url(_cfg.REDIS_URL, decode_responses=True)
                    key = f"money_story:{uid}"
                    r.setex(key, 3600, story.model_dump_json())
                    processed += 1
                except Exception as cache_err:
                    print(f"[MoneyStory] Redis cache write failed for {uid}: {cache_err}")
            except Exception as e:
                print(f"[MoneyStory] Failed for user {uid}: {e}")

        await engine.dispose()
        return processed

    count = asyncio.run(_run())
    print(f"[MoneyStory] Sunday pre-computation complete. Stories generated: {count}")
    return f"Sunday Money Stories pre-computed for {count} users"


@celery_app.task(name="scan_budgets_task")
def scan_budgets_task():
    """
    Celery Beat task running every 6 hours to scan budget thresholds
    and dispatch push alerts if spent >= 80%.
    """
    import asyncio

    async def _run():
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from app.config import settings as _cfg
        from app.services.notification_service import scan_budget_thresholds

        engine = create_async_engine(_cfg.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            count = await scan_budget_thresholds(db=session)

        await engine.dispose()
        return count

    count = asyncio.run(_run())
    print(f"[Worker] Budget scanners triggered. Alerts created: {count}")
    return f"Triggered {count} budget alerts"


@celery_app.task(name="scan_subscriptions_task")
def scan_subscriptions_task():
    """
    Celery Beat task running daily to check subscriptions due in 24 hours
    and dispatch auto-debit alerts.
    """
    import asyncio

    async def _run():
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from app.config import settings as _cfg
        from app.services.notification_service import scan_subscription_dues

        engine = create_async_engine(_cfg.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            count = await scan_subscription_dues(db=session)

        await engine.dispose()
        return count

    count = asyncio.run(_run())
    print(f"[Worker] Subscription scanners triggered. Alerts created: {count}")
    return f"Triggered {count} auto-debit alerts"


