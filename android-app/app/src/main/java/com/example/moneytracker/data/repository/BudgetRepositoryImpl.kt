package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import com.example.moneytracker.domain.repository.BudgetRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class BudgetRepositoryImpl(
    private val apiService: ApiService
) : BudgetRepository {

    override suspend fun getBudgetSummary(): Result<List<BudgetSummaryResponse>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getBudgetSummary()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch budgets: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun createBudget(request: BudgetCreateRequest): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.createBudget(request)
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to create budget: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
