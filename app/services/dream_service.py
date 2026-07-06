"""
app/services/dream_service.py
─────────────────────────────────────────────────────────────────────────────
AI Dream Planner service layer. Generates saving roadmaps, predictions,
and motivational timelines for user financial goals.
"""

import uuid
import json
import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dream import Dream
from app.schemas.dream import (
    DreamDto,
    DreamRoadmapDto,
    DreamMilestoneDto,
)
from app.services.ai_service import get_ai_service
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


async def generate_ai_roadmap(
    dream_name: str,
    target: Decimal,
    months: int,
    weekly: Decimal,
    monthly: Decimal
) -> Optional[dict]:
    """
    Query the AI to construct a personalized financial dream roadmap.
    """
    ai_service = get_ai_service()
    if not ai_service.enabled:
        return None

    system_msg = (
        "You are an inspiring AI Financial Planner. Create a roadmap, risk analysis, "
        "and SIP mutual fund/index fund investment suggestion for the user's financial dream. "
        "Output JSON exactly matching: "
        '{"risk_analysis": "text", "investment_suggestions": ["tip1", "tip2"], '
        '"milestones": [{"percent": 25, "label": "text"}, {"percent": 50, "label": "text"}, '
        '{"percent": 75, "label": "text"}, {"percent": 100, "label": "text"}]}'
    )
    prompt = (
        f"Dream Name: {dream_name}. Target: ₹{target:,.2f}. "
        f"Timeline: {months} months. Monthly savings required: ₹{monthly:,.2f}. "
        "Provide inspiring, motivating labels and risk forecasts."
    )

    try:
        res = await ai_service.provider.get_completion(prompt, system_msg)
        if res:
            return json.loads(res)
    except Exception as e:
        logger.error("AI Dream Roadmap generation failed: %s", e)
    return None


async def create_dream(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    target_amount: Decimal,
    deadline: datetime.date
) -> Dream:
    """
    Register a new financial dream, compute required savings metrics,
    query the AI roadmap, and save everything.
    """
    today = datetime.date.today()
    days = (deadline - today).days
    if days <= 0:
        raise ValueError("Deadline must be in the future.")

    months = max(1, round(days / 30.4))
    weeks = max(1, round(days / 7.0))

    monthly_saving = (target_amount / Decimal(months)).quantize(Decimal("0.01"))
    weekly_saving = (target_amount / Decimal(weeks)).quantize(Decimal("0.01"))

    # Generate AI Roadmap
    ai_roadmap = None
    try:
        ai_roadmap = await generate_ai_roadmap(name, target_amount, months, weekly_saving, monthly_saving)
    except Exception as e:
        logger.warning("AI Roadmap failed, falling back to rules: %s", e)

    if not ai_roadmap:
        # Rules-based fallback
        ai_roadmap = {
            "risk_analysis": (
                "Low risk. Staying on track with weekly caps will ensure you meet your deadline. "
                "Watch out for unplanned lifestyle upgrades."
            ),
            "investment_suggestions": [
                f"Allocate ₹{(monthly_saving * Decimal('0.6')):,.2f} into low-cost Index Funds monthly.",
                f"Put ₹{(monthly_saving * Decimal('0.4')):,.2f} in a High-Yield Savings Account / Liquid Fund."
            ],
            "milestones": [
                {"percent": 25, "label": "25%: Off to a great start! Milestone 1 achieved. 🚀"},
                {"percent": 50, "label": "50%: Halfway there! You are making serious progress. 👏"},
                {"percent": 75, "label": "75%: So close! The finish line is in sight. 🏁"},
                {"percent": 100, "label": "100%: Congratulations! You achieved your dream! 🏆"}
            ]
        }

    dream = Dream(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        deadline=deadline,
        weekly_saving_target=weekly_saving,
        monthly_saving_target=monthly_saving,
        status="active",
        ai_roadmap_json=json.dumps(ai_roadmap)
    )
    db.add(dream)
    await db.commit()
    return dream


async def update_dream_progress(
    db: AsyncSession,
    dream_id: uuid.UUID,
    user_id: uuid.UUID,
    amount: Decimal
) -> Dream:
    """
    Log savings progress towards a dream. Sets status to 'completed' if target is met.
    """
    result = await db.execute(
        select(Dream).where(
            and_(
                Dream.id == dream_id,
                Dream.user_id == user_id
            )
        )
    )
    dream = result.scalar_one_or_none()
    if not dream:
        raise ValueError("Dream not found.")

    dream.current_savings = (dream.current_savings + amount).quantize(Decimal("0.01"))
    if dream.current_savings >= dream.target_amount:
        dream.status = "completed"

    await db.commit()
    return dream


async def get_user_dreams(
    db: AsyncSession,
    user_id: uuid.UUID
) -> List[DreamDto]:
    """
    List all active and completed dreams for a user.
    """
    result = await db.execute(
        select(Dream).where(Dream.user_id == user_id).order_by(Dream.created_at.desc())
    )
    dreams = result.scalars().all()

    dtos = []
    today = datetime.date.today()

    for d in dreams:
        progress_pct = min(100.0, float((d.current_savings / d.target_amount) * 100))
        days_rem = max(0, (d.deadline - today).days)

        roadmap_dto = None
        if d.ai_roadmap_json:
            try:
                raw = json.loads(d.ai_roadmap_json)
                milestones_list = [
                    DreamMilestoneDto(
                        percent=m["percent"],
                        label=m["label"],
                        reached=(progress_pct >= m["percent"])
                    )
                    for m in raw.get("milestones", [])
                ]

                # Determine forecast prob
                prob = "High"
                color = "#4CAF7D"
                if progress_pct < 20 and days_rem < 30:
                    prob = "Low"
                    color = "#EF5350"
                elif progress_pct < 50 and days_rem < 90:
                    prob = "Medium"
                    color = "#F5A623"

                roadmap_dto = DreamRoadmapDto(
                    timeline_months=max(1, round(days_rem / 30.4)),
                    weekly_target=float(d.weekly_saving_target),
                    weekly_target_formatted=f"₹ {d.weekly_saving_target:,.2f}",
                    monthly_target=float(d.monthly_saving_target),
                    monthly_target_formatted=f"₹ {d.monthly_saving_target:,.2f}",
                    forecast_probability=prob,
                    forecast_color=color,
                    risk_analysis=raw.get("risk_analysis", ""),
                    investment_suggestions=raw.get("investment_suggestions", []),
                    motivational_timeline=milestones_list
                )
            except Exception as e:
                logger.warning("Failed to compile roadmap DTO: %s", e)

        dtos.append(
            DreamDto(
                id=d.id,
                name=d.name,
                target_amount=float(d.target_amount),
                target_amount_formatted=f"₹ {d.target_amount:,.2f}",
                current_savings=float(d.current_savings),
                current_savings_formatted=f"₹ {d.current_savings:,.2f}",
                progress_pct=round(progress_pct, 1),
                deadline=d.deadline,
                days_remaining=days_rem,
                status=d.status,
                created_at=d.created_at,
                roadmap=roadmap_dto
            )
        )

    return dtos
