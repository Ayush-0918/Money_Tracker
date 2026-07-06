package com.example.moneytracker.data.remote.dto

import com.google.gson.annotations.SerializedName

// ── Money Story DTOs ─────────────────────────────────────────────────────────

data class MoneyStoryResponseDto(
    @SerializedName("week_label") val weekLabel: String,
    @SerializedName("generated_at") val generatedAt: String,
    @SerializedName("page_score") val pageScore: MoneyScorePageDto,
    @SerializedName("page_spending") val pageSpending: SpendingPageDto,
    @SerializedName("page_savings") val pageSavings: SavingsPageDto,
    @SerializedName("page_achievements") val pageAchievements: AchievementsPageDto,
    @SerializedName("page_mistakes") val pageMistakes: MistakesPageDto,
    @SerializedName("page_forecast") val pageForecast: ForecastPageDto,
    @SerializedName("page_action") val pageAction: ActionPlanPageDto,
    @SerializedName("card_headline") val cardHeadline: String,
    @SerializedName("card_score") val cardScore: Int,
    @SerializedName("card_summary") val cardSummary: String,
    @SerializedName("card_score_color") val cardScoreColor: String,
    @SerializedName("card_badge_count") val cardBadgeCount: Int
)

data class MoneyScorePageDto(
    @SerializedName("money_score") val moneyScore: Int,
    @SerializedName("score_label") val scoreLabel: String,
    @SerializedName("score_color") val scoreColor: String,
    @SerializedName("score_headline") val scoreHeadline: String,
    @SerializedName("show_confetti") val showConfetti: Boolean,
    @SerializedName("financial_mood") val financialMood: String,
    @SerializedName("mood_color") val moodColor: String
)

data class SpendingPageDto(
    @SerializedName("total_spend") val totalSpend: Double,
    @SerializedName("total_spend_formatted") val totalSpendFormatted: String,
    @SerializedName("prior_week_spend") val priorWeekSpend: Double,
    @SerializedName("prior_week_spend_formatted") val priorWeekSpendFormatted: String,
    @SerializedName("spend_change_pct") val spendChangePct: Double,
    @SerializedName("spend_change_text") val spendChangeText: String,
    @SerializedName("spend_change_is_increase") val spendChangeIsIncrease: Boolean,
    @SerializedName("daily_points") val dailyPoints: List<Double>,
    @SerializedName("daily_labels") val dailyLabels: List<String>,
    @SerializedName("average_per_day_formatted") val averagePerDayFormatted: String,
    @SerializedName("top_categories") val topCategories: Map<String, Double>,
    @SerializedName("top_categories_formatted") val topCategoriesFormatted: Map<String, String>
)

data class SavingsPageDto(
    @SerializedName("savings_amount") val savingsAmount: Double,
    @SerializedName("savings_amount_formatted") val savingsAmountFormatted: String,
    @SerializedName("savings_vs_last_week") val savingsVsLastWeek: Double,
    @SerializedName("savings_vs_last_week_formatted") val savingsVsLastWeekFormatted: String,
    @SerializedName("savings_is_positive") val savingsIsPositive: Boolean,
    @SerializedName("savings_headline") val savingsHeadline: String,
    @SerializedName("savings_trend") val savingsTrend: List<Double>,
    @SerializedName("savings_rate_pct") val savingsRatePct: Double
)

data class AchievementBadgeDto(
    @SerializedName("id") val id: String,
    @SerializedName("label") val label: String,
    @SerializedName("description") val description: String,
    @SerializedName("icon") val icon: String,
    @SerializedName("color") val color: String,
    @SerializedName("earned") val earned: Boolean
)

data class AchievementsPageDto(
    @SerializedName("badges") val badges: List<AchievementBadgeDto>,
    @SerializedName("earned_count") val earnedCount: Int,
    @SerializedName("show_confetti") val showConfetti: Boolean,
    @SerializedName("headline") val headline: String
)

data class MistakesPageDto(
    @SerializedName("worst_decision") val worstDecision: String,
    @SerializedName("exceeded_budgets") val exceededBudgets: List<String>,
    @SerializedName("overspend_categories") val overspendCategories: List<String>,
    @SerializedName("improvement_tip") val improvementTip: String,
    @SerializedName("has_mistakes") val hasMistakes: Boolean
)

data class ForecastPageDto(
    @SerializedName("prediction_next_week") val predictionNextWeek: String,
    @SerializedName("predicted_spend_formatted") val predictedSpendFormatted: String,
    @SerializedName("spend_trend_direction") val spendTrendDirection: String,
    @SerializedName("upcoming_subscriptions_count") val upcomingSubscriptionsCount: Int,
    @SerializedName("upcoming_subscriptions_total_formatted") val upcomingSubscriptionsTotalFormatted: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("risk_color") val riskColor: String
)

data class ActionPlanPageDto(
    @SerializedName("ai_tips") val aiTips: List<String>,
    @SerializedName("best_decision") val bestDecision: String,
    @SerializedName("weekly_challenge") val weeklyChallenge: String,
    @SerializedName("share_card_text") val shareCardText: String
)
