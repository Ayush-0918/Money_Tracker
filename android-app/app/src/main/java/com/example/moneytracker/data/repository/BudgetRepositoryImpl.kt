package com.example.moneytracker.data.repository

import com.example.moneytracker.data.local.dao.CacheDao
import com.example.moneytracker.data.local.entity.CachedBudgetEntity
import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import com.example.moneytracker.domain.repository.BudgetRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.util.UUID

class BudgetRepositoryImpl(
    private val api: ApiService,
    private val cacheDao: CacheDao
) : BudgetRepository {

    override fun getCachedBudgets(): Flow<List<BudgetSummaryResponse>> {
        return cacheDao.getAllBudgets().map { entities ->
            entities.map { entity ->
                BudgetSummaryResponse(
                    budget_id = UUID.fromString(entity.id),
                    category_id = UUID.fromString(entity.categoryId),
                    monthly_limit = entity.monthlyLimit,
                    spent = entity.spent,
                    remaining = entity.remaining,
                    percentage_used = entity.percentageUsed?.toDouble(),
                    status = entity.status,
                    stale = false,
                    suggestion = null
                )
            }
        }
    }

    override suspend fun refreshBudgets(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val response = api.getBudgetSummary()
            if (response.isSuccessful && response.body() != null) {
                val budgets = response.body()!!
                val entities = budgets.map { dto ->
                    CachedBudgetEntity(
                        id = dto.budget_id.toString(),
                        categoryId = dto.category_id.toString(),
                        monthlyLimit = dto.monthly_limit,
                        spent = dto.spent,
                        remaining = dto.remaining,
                        percentageUsed = dto.percentage_used?.toFloat(),
                        status = dto.status,
                        categoryName = "Unknown"
                    )
                }
                cacheDao.clearBudgets()
                cacheDao.insertBudgets(entities)
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to fetch budgets: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getBudgetSummary(): Result<List<BudgetSummaryResponse>> = withContext(Dispatchers.IO) {
        try {
            val response = api.getBudgetSummary()
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
            val response = api.createBudget(request)
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
