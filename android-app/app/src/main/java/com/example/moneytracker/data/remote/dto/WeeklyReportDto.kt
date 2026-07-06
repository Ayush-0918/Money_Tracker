package com.example.moneytracker.data.remote.dto

import com.google.gson.annotations.SerializedName

// ── Weekly Financial Report DTOs ─────────────────────────────────────────────

data class WeeklyReportResponseDto(
    @SerializedName("week_label") val weekLabel: String,
    @SerializedName("generated_at") val generatedAt: String,

    // Spend summary
    @SerializedName("total_spend") val totalSpend: Double,
    @SerializedName("total_spend_formatted") val totalSpendFormatted: String,
    @SerializedName("prior_week_spend") val priorWeekSpend: Double,
    @SerializedName("prior_week_spend_formatted") val priorWeekSpendFormatted: String,
    @SerializedName("spend_change_pct") val spendChangePct: Double,
    @SerializedName("spend_change_text") val spendChangeText: String,
    @SerializedName("spend_change_is_increase") val spendChangeIsIncrease: Boolean,

    // Categories
    @SerializedName("top_categories") val topCategories: Map<String, Double>,
    @SerializedName("top_categories_formatted") val topCategoriesFormatted: Map<String, String>,

    // Merchants
    @SerializedName("top_merchants") val topMerchants: List<MerchantSpendItemDto>,

    // Daily activity
    @SerializedName("daily_points") val dailyPoints: List<Double>,
    @SerializedName("daily_labels") val dailyLabels: List<String>,
    @SerializedName("average_per_day") val averagePerDay: Double,
    @SerializedName("average_per_day_formatted") val averagePerDayFormatted: String,

    // Budget health
    @SerializedName("budget_health") val budgetHealth: List<BudgetHealthItemDto>,
    @SerializedName("exceeded_budget_count") val exceededBudgetCount: Int,

    // Subscriptions
    @SerializedName("upcoming_subscriptions") val upcomingSubscriptions: List<UpcomingSubscriptionDto>,

    // AI content
    @SerializedName("ai_narrative") val aiNarrative: String,
    @SerializedName("ai_tips") val aiTips: List<String>,

    // Health score
    @SerializedName("financial_health_score") val financialHealthScore: Int,
    @SerializedName("health_score_label") val healthScoreLabel: String,
    @SerializedName("health_score_color") val healthScoreColor: String
)

data class MerchantSpendItemDto(
    @SerializedName("rank") val rank: Int,
    @SerializedName("merchant") val merchant: String,
    @SerializedName("amount") val amount: Double,
    @SerializedName("amount_formatted") val amountFormatted: String
)

data class BudgetHealthItemDto(
    @SerializedName("category") val category: String,
    @SerializedName("limit") val limit: Double,
    @SerializedName("spent") val spent: Double,
    @SerializedName("percent_used") val percentUsed: Double,
    @SerializedName("is_exceeded") val isExceeded: Boolean,
    @SerializedName("limit_formatted") val limitFormatted: String,
    @SerializedName("spent_formatted") val spentFormatted: String
)

data class UpcomingSubscriptionDto(
    @SerializedName("id") val id: String,
    @SerializedName("merchant") val merchant: String,
    @SerializedName("amount_formatted") val amountFormatted: String,
    @SerializedName("next_billing_date") val nextBillingDate: String,
    @SerializedName("countdown_days") val countdownDays: Int
)
