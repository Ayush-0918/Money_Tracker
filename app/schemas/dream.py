"""
app/schemas/dream.py
─────────────────────────────────────────────────────────────────────────────
Pydantic schemas for the AI Dream Planner.
"""

from __future__ import annotations

from typing import List, Optional
from decimal import Decimal
from datetime import date, datetime
import uuid

from pydantic import BaseModel


class DreamCreateDto(BaseModel):
    name: str
    target_amount: Decimal
    deadline: date


class DreamUpdateProgressDto(BaseModel):
    amount: Decimal


class DreamMilestoneDto(BaseModel):
    percent: int
    label: str          # e.g. "25%: Good start!"
    reached: bool


class DreamRoadmapDto(BaseModel):
    timeline_months: int
    weekly_target: float
    weekly_target_formatted: str
    monthly_target: float
    monthly_target_formatted: str
    forecast_probability: str      # "High" / "Medium" / "Low"
    forecast_color: str            # hex color
    risk_analysis: str             # AI explanation of budget or speed risks
    investment_suggestions: List[str]
    motivational_timeline: List[DreamMilestoneDto]


class DreamDto(BaseModel):
    id: uuid.UUID
    name: str
    target_amount: float
    target_amount_formatted: str
    current_savings: float
    current_savings_formatted: str
    progress_pct: float            # 0.0 - 100.0
    deadline: date
    days_remaining: int
    status: str                    # "active", "completed"
    created_at: datetime
    roadmap: Optional[DreamRoadmapDto] = None
