package com.example.moneytracker.data.remote.dto

import java.util.UUID

data class BudgetSummaryResponse(
    val budget_id: UUID,
    val category_id: UUID,
    val monthly_limit: Double,
    val spent: Double,
    val remaining: Double,
    val percentage_used: Double?,
    val status: String,
    val stale: Boolean,
    val suggestion: String?
)

data class BudgetCreateRequest(
    val category_id: UUID,
    val monthly_limit: Double
)
