package com.example.moneytracker.data.remote.dto

data class AIPredictionResponseDto(
    val user_id: String,
    val generated_at: String,
    val expense_forecast: ExpenseForecastDto,
    val cash_flow_forecast: CashFlowForecastDto,
    val budget_forecast: List<BudgetPredictionDto>,
    val salary_prediction: SalaryPredictionDto,
    val ai_insights: List<String>
)

data class ExpenseForecastDto(
    val next_day: Float,
    val next_week: Float,
    val next_month: Float,
    val category_forecast: Map<String, Float>,
    val confidence_percentage: Float
)

data class CashFlowForecastDto(
    val predicted_balance: List<Map<String, Float>>,
    val estimated_inflow: Float,
    val estimated_outflow: Float,
    val negative_balance_risk_dates: List<String>
)

data class BudgetPredictionDto(
    val category_id: String,
    val category_name: String,
    val predicted_spend: Float,
    val will_exceed: Boolean,
    val estimated_days_remaining: Int,
    val projected_trend: List<Float>
)

data class SalaryPredictionDto(
    val is_detected: Boolean,
    val expected_date: String?,
    val expected_amount: Float?,
    val confidence: Float
)
