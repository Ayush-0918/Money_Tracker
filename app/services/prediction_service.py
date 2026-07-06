"""
app/services/prediction_service.py
─────────────────────────────────────────────────────────────────────────────
Business logic for AI-powered financial predictions.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.user import PredictionCache
from app.schemas.prediction import (
    AIPredictionResponse,
    ExpenseForecast,
    CashFlowForecast,
    BudgetPrediction,
    SalaryPrediction,
)
from app.services.ai_service import get_ai_service

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 24


class PredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = get_ai_service()

    async def get_predictions(self, user_id: uuid.UUID) -> AIPredictionResponse:
        """
        Retrieves financial predictions for a user, using cache if available.
        """
        # 1. Check Cache
        cached = await self._get_cached_predictions(user_id)
        if cached:
            return AIPredictionResponse(**cached)

        # 2. Fetch Context Data
        transactions_data = await self._fetch_user_financial_context(user_id)
        budget_data = await self._fetch_user_budget_context(user_id)

        # 3. Call AI for Predictions
        predictions_json = await self._generate_ai_predictions(user_id, transactions_data, budget_data)

        if not predictions_json:
            # Fallback to statistical predictions if AI fails
            predictions = self._generate_statistical_fallback(user_id, transactions_data, budget_data)
        else:
            try:
                predictions_dict = json.loads(predictions_json)
                # Add user_id and timestamp if not present
                predictions_dict["user_id"] = str(user_id)
                predictions_dict["generated_at"] = datetime.utcnow().isoformat()
                predictions = AIPredictionResponse(**predictions_dict)
            except Exception as e:
                logger.error(f"Failed to parse AI predictions for user {user_id}: {e}")
                predictions = self._generate_statistical_fallback(user_id, transactions_data, budget_data)

        # 4. Update Cache
        await self._cache_predictions(user_id, predictions.model_dump())

        return predictions

    async def _get_cached_predictions(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(PredictionCache).where(PredictionCache.user_id == user_id)
        result = await self.db.execute(stmt)
        cache = result.scalar_one_or_none()

        if cache:
            age = datetime.now(timezone.utc) - cache.updated_at
            if age < timedelta(hours=CACHE_TTL_HOURS):
                return cache.predictions
        return None

    async def _cache_predictions(self, user_id: uuid.UUID, predictions: Dict[str, Any]):
        try:
            # predictions contains datetime objects which need to be stringified for JSON
            # But model_dump() with mode='json' is better if available,
            # here we just rely on Pydantic's default serialization if possible or manual fix.
            cache = PredictionCache(user_id=user_id, predictions=json.loads(json.dumps(predictions, default=str)))
            await self.db.merge(cache)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to cache predictions for user {user_id}: {e}")
            await self.db.rollback()

    async def _fetch_user_financial_context(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        # Fetch last 3 months of transactions
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        stmt = (
            select(Transaction)
            .where(and_(Transaction.user_id == user_id, Transaction.transaction_date >= three_months_ago))
            .order_by(Transaction.transaction_date.desc())
        )

        result = await self.db.execute(stmt)
        transactions = result.scalars().all()

        return [
            {
                "amount": float(t.amount),
                "merchant": t.merchant,
                "category": t.category,
                "date": t.transaction_date.isoformat(),
                "is_recurring": t.is_recurring,
            }
            for t in transactions
        ]

    async def _fetch_user_budget_context(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        stmt = select(Budget).options(selectinload(Budget.category)).where(Budget.user_id == user_id)
        result = await self.db.execute(stmt)
        budgets = result.scalars().all()

        return [
            {
                "category": b.category.name if b.category else "Others",
                "limit": float(b.monthly_limit),
                "spent": float(b.cached_spent or 0),
            }
            for b in budgets
        ]

    async def _generate_ai_predictions(
        self, user_id: uuid.UUID, transactions: List[Dict[str, Any]], budgets: List[Dict[str, Any]]
    ) -> Optional[str]:
        system_msg = (
            "You are a sophisticated AI Financial Prediction Engine. Analyze historical transactions and budgets "
            "to forecast future behavior. Detect recurring patterns (like salary, subscriptions, EMIs). "
            "Estimate future expenses and cash flow risks. Return your response in STRICTURE JSON format."
        )

        prompt = f"""
        User ID: {user_id}
        Historical Transactions (Last 90 days): {json.dumps(transactions[:50])}
        Current Budgets: {json.dumps(budgets)}

        Based on this data, predict:
        1. Expense Forecast (next_day, next_week, next_month amount, category breakdown, confidence).
        2. Cash Flow Forecast (predicted_balance series for next 30 days, inflow/outflow, negative risk dates).
        3. Budget Forecast (will user exceed limit, estimated days remaining, projected spend).
        4. Salary Prediction (is_detected, expected_date, expected_amount).
        5. AI Insights (at least 3 punchy financial advice/warnings).

        Output JSON Template:
        {{
            "expense_forecast": {{
                "next_day": 0.0, "next_week": 0.0, "next_month": 0.0,
                "category_forecast": {{"Category": 0.0}},
                "confidence_percentage": 0.0
            }},
            "cash_flow_forecast": {{
                "predicted_balance": [{{"date": "YYYY-MM-DD", "balance": 0.0}}],
                "estimated_inflow": 0.0, "estimated_outflow": 0.0,
                "negative_balance_risk_dates": ["YYYY-MM-DD"]
            }},
            "budget_forecast": [
                {{
                    "category_id": "uuid", "category_name": "string",
                    "predicted_spend": 0.0, "will_exceed": false,
                    "estimated_days_remaining": 0, "projected_trend": [0.0]
                }}
            ],
            "salary_prediction": {{
                "is_detected": false, "expected_date": "YYYY-MM-DD", "expected_amount": 0.0, "confidence": 0.0
            }},
            "ai_insights": ["string"]
        }}
        """

        # Use provider directly to get full completion
        return await self.ai_service.provider.get_completion(prompt, system_msg)

    def _generate_statistical_fallback(
        self, user_id: uuid.UUID, transactions: List[Dict[str, Any]], budgets: List[Dict[str, Any]]
    ) -> AIPredictionResponse:
        """
        Provides a basic mathematical fallback if AI fails.
        """
        total_spent = sum(t["amount"] for t in transactions)
        avg_daily = total_spent / 90 if transactions else 0.0

        expense_forecast = ExpenseForecast(
            next_day=avg_daily,
            next_week=avg_daily * 7,
            next_month=avg_daily * 30,
            category_forecast={},
            confidence_percentage=50.0,
        )

        cash_flow = CashFlowForecast(
            predicted_balance=[],
            estimated_inflow=0.0,
            estimated_outflow=total_spent / 3,
            negative_balance_risk_dates=[],
        )

        budget_forecast = []
        for b in budgets:
            days_passed = datetime.now().day
            days_in_month = 30
            predicted = (b["spent"] / days_passed) * days_in_month if days_passed > 0 else 0
            budget_forecast.append(
                BudgetPrediction(
                    category_id=uuid.uuid4(),  # Dummy for fallback
                    category_name=b["category"],
                    predicted_spend=predicted,
                    will_exceed=predicted > b["limit"],
                    estimated_days_remaining=(
                        int((b["limit"] - b["spent"]) / (b["spent"] / days_passed)) if b["spent"] > 0 else 30
                    ),
                    projected_trend=[],
                )
            )

        salary = SalaryPrediction(is_detected=False, expected_date=None, expected_amount=None, confidence=0.0)

        return AIPredictionResponse(
            user_id=user_id,
            generated_at=datetime.utcnow(),
            expense_forecast=expense_forecast,
            cash_flow_forecast=cash_flow,
            budget_forecast=budget_forecast,
            salary_prediction=salary,
            ai_insights=["Statistical fallback used. AI predictions are currently unavailable."],
        )
