package com.example.moneytracker.data.remote.dto

import com.google.gson.annotations.SerializedName

// ── AI Dream Planner DTOs ───────────────────────────────────────────────────

data class DreamCreateDto(
    @SerializedName("name") val name: String,
    @SerializedName("target_amount") val targetAmount: Double,
    @SerializedName("deadline") val deadline: String
)

data class DreamUpdateProgressDto(
    @SerializedName("amount") val amount: Double
)

data class DreamMilestoneDto(
    @SerializedName("percent") val percent: Int,
    @SerializedName("label") val label: String,
    @SerializedName("reached") val reached: Boolean
)

data class DreamRoadmapDto(
    @SerializedName("timeline_months") val timelineMonths: Int,
    @SerializedName("weekly_target") val weeklyTarget: Double,
    @SerializedName("weekly_target_formatted") val weeklyTargetFormatted: String,
    @SerializedName("monthly_target") val monthlyTarget: Double,
    @SerializedName("monthly_target_formatted") val monthlyTargetFormatted: String,
    @SerializedName("forecast_probability") val forecastProbability: String,
    @SerializedName("forecast_color") val forecastColor: String,
    @SerializedName("risk_analysis") val riskAnalysis: String,
    @SerializedName("investment_suggestions") val investmentSuggestions: List<String>,
    @SerializedName("motivational_timeline") val motivationalTimeline: List<DreamMilestoneDto>
)

data class DreamResponseDto(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("target_amount") val targetAmount: Double,
    @SerializedName("target_amount_formatted") val targetAmountFormatted: String,
    @SerializedName("current_savings") val currentSavings: Double,
    @SerializedName("current_savings_formatted") val currentSavingsFormatted: String,
    @SerializedName("progress_pct") val progressPct: Double,
    @SerializedName("deadline") val deadline: String,
    @SerializedName("days_remaining") val daysRemaining: Int,
    @SerializedName("status") val status: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("roadmap") val roadmap: DreamRoadmapDto?
)
