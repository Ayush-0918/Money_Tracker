package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import kotlinx.coroutines.flow.Flow

interface BudgetRepository {
    fun getCachedBudgets(): Flow<List<BudgetSummaryResponse>>
    suspend fun refreshBudgets(): Result<Unit>

    suspend fun getBudgetSummary(): Result<List<BudgetSummaryResponse>>
    suspend fun createBudget(request: BudgetCreateRequest): Result<Unit>
}
