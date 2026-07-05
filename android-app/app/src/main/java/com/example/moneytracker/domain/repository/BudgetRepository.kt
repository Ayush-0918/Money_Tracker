package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse

interface BudgetRepository {
    suspend fun getBudgetSummary(): Result<List<BudgetSummaryResponse>>
    suspend fun createBudget(request: BudgetCreateRequest): Result<Unit>
}
