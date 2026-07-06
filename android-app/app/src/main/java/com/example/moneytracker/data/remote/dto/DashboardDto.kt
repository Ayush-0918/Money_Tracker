package com.example.moneytracker.data.remote.dto

data class WeeklyActivityDto(
    val average_per_day: Float,
    val points: List<Float>
)

data class DashboardSummaryDto(
    val total_balance: String,
    val monthly_income: String,
    val monthly_expense: String,
    val monthly_savings: String,
    val total_transactions: Int,
    val latest_transactions: List<TransactionItemDto>,
    val top_categories: Map<String, Float>,
    val upcoming_subscriptions: List<SubscriptionDto>,
    val weekly_activity: WeeklyActivityDto,
    val budgets: List<BudgetSummaryResponse> = emptyList(),
    val ai_insights: String? = null,
    val saving_tips: String? = null
)

data class TransactionItemDto(
    val id: String,
    val merchant: String,
    val amount_formatted: String,
    val date: String,
    val category: String?
)

data class SubscriptionDto(
    val id: String,
    val merchant: String,
    val amount_formatted: String,
    val next_billing_date: String,
    val countdown_days: Int
)
