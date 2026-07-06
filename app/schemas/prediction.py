from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ExpenseForecast(BaseModel):
    next_day: float
    next_week: float
    next_month: float
    category_forecast: Dict[str, float]
    confidence_percentage: float


class CashFlowForecast(BaseModel):
    predicted_balance: List[Dict[str, float]]  # Date as string -> balance
    estimated_inflow: float
    estimated_outflow: float
    negative_balance_risk_dates: List[date]


class BudgetPrediction(BaseModel):
    category_id: uuid.UUID
    category_name: str
    predicted_spend: float
    will_exceed: bool
    estimated_days_remaining: int
    projected_trend: List[float]


class SalaryPrediction(BaseModel):
    is_detected: bool
    expected_date: Optional[date]
    expected_amount: Optional[float]
    confidence: float


class AIPredictionResponse(BaseModel):
    user_id: uuid.UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expense_forecast: ExpenseForecast
    cash_flow_forecast: CashFlowForecast
    budget_forecast: List[BudgetPrediction]
    salary_prediction: SalaryPrediction
    ai_insights: List[str]
