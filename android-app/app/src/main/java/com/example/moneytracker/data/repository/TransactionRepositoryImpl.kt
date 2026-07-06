package com.example.moneytracker.data.repository

import android.content.Context
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.example.moneytracker.data.local.dao.TransactionDao
import com.example.moneytracker.data.local.dao.CacheDao
import com.example.moneytracker.data.local.entity.TransactionEntity
import com.example.moneytracker.data.local.entity.CachedTransactionEntity
import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.PaginatedTransactionResponse
import com.example.moneytracker.data.remote.dto.TransactionRequest
import com.example.moneytracker.data.remote.dto.CategoryUpdateDto
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import com.example.moneytracker.domain.repository.TransactionRepository
import com.example.moneytracker.service.sync.SyncWorker
import com.example.moneytracker.util.Constants
import com.example.moneytracker.util.SecurePrefs
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class TransactionRepositoryImpl(
    private val api: ApiService,
    private val dao: TransactionDao,
    private val cacheDao: CacheDao,
    private val securePrefs: SecurePrefs,
    private val context: Context
) : TransactionRepository {

    override fun getCachedTransactions(): Flow<List<TransactionItemDto>> {
        return cacheDao.getAllTransactions().map { entities ->
            entities.map { entity ->
                TransactionItemDto(
                    id = entity.id,
                    merchant = entity.merchant,
                    amount_formatted = entity.amountFormatted,
                    date = entity.date,
                    category = entity.category
                )
            }
        }
    }

    override suspend fun refreshTransactions(): Result<Unit> {
        return try {
            val response = api.getTransactions(page = 1, size = 50)
            if (response.isSuccessful) {
                val transactions = response.body()?.items ?: emptyList()
                val entities = transactions.map { dto ->
                    CachedTransactionEntity(
                        id = dto.id,
                        merchant = dto.merchant,
                        amountFormatted = dto.amount_formatted,
                        date = dto.date,
                        category = dto.category
                    )
                }
                cacheDao.clearTransactions()
                cacheDao.insertTransactions(entities)
                Result.success(Unit)
            } else {
                Result.failure(Exception("Refresh failed: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun syncTransaction(rawText: String) {
        val token = securePrefs.getToken() ?: return
        val userId = securePrefs.getUserId() ?: return
        
        try {
            // Attempt network call (AuthInterceptor attaches token)
            val response = api.postTransaction(
                TransactionRequest(userId, rawText, "notification")
            )
            if (!response.isSuccessful) {
                queueForRetry(userId, rawText)
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "Transaction sync failed", e)
        }
    }


    override suspend fun getDashboardSummary(): Result<DashboardSummaryDto> {
        return try {
            val response = api.getDashboardSummary()
            if (response.isSuccessful && response.body() != null) {
                val summary = response.body()!!
                // Cache latest transactions as a side effect
                val entities = summary.latest_transactions.map { dto ->
                    CachedTransactionEntity(
                        id = dto.id,
                        merchant = dto.merchant,
                        amountFormatted = dto.amount_formatted,
                        date = dto.date,
                        category = dto.category
                    )
                }
                cacheDao.clearTransactions()
                cacheDao.insertTransactions(entities)
                
                // Cache full summary for offline fallback
                securePrefs.saveDashboardSummary(summary)
                
                Result.success(summary)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getDashboardSummary API Error: ${response.code()} - $errorBody")
                
                // Fallback to local cache
                val cached = securePrefs.getDashboardSummary()
                if (cached != null) {
                    android.util.Log.i("Repository", "getDashboardSummary: falling back to cache")
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getDashboardSummary Network/Parse Exception", e)
            
            // Fallback to local cache
            val cached = securePrefs.getDashboardSummary()
            if (cached != null) {
                android.util.Log.i("Repository", "getDashboardSummary: falling back to cache on exception")
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun getMonthlyReport(userId: String): Result<com.example.moneytracker.data.remote.dto.MonthlyReportDto> {
        return try {
            val response = api.getMonthlyReport(userId)
            if (response.isSuccessful && response.body() != null) {
                val report = response.body()!!
                securePrefs.saveMonthlyReport(report)
                Result.success(report)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getMonthlyReport API Error: ${response.code()} - $errorBody")
                
                val cached = securePrefs.getMonthlyReport()
                if (cached != null) {
                    android.util.Log.i("Repository", "getMonthlyReport: falling back to cache")
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getMonthlyReport Network/Parse Exception", e)
            
            val cached = securePrefs.getMonthlyReport()
            if (cached != null) {
                android.util.Log.i("Repository", "getMonthlyReport: falling back to cache on exception")
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun getWeeklyReport(userId: String): Result<com.example.moneytracker.data.remote.dto.WeeklyActivityDto> {
        return try {
            val response = api.getWeeklyReport(userId)
            if (response.isSuccessful && response.body() != null) {
                val report = response.body()!!
                securePrefs.saveWeeklyReport(report)
                Result.success(report)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getWeeklyReport API Error: ${response.code()} - $errorBody")
                
                val cached = securePrefs.getWeeklyReport()
                if (cached != null) {
                    android.util.Log.i("Repository", "getWeeklyReport: falling back to cache")
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getWeeklyReport Network/Parse Exception", e)
            
            val cached = securePrefs.getWeeklyReport()
            if (cached != null) {
                android.util.Log.i("Repository", "getWeeklyReport: falling back to cache on exception")
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun getSubscriptionReport(userId: String): Result<List<com.example.moneytracker.data.remote.dto.SubscriptionDto>> {
        return try {
            val response = api.getSubscriptionReport(userId)
            if (response.isSuccessful && response.body() != null) {
                val subs = response.body()!!
                securePrefs.saveSubscriptionReport(subs)
                Result.success(subs)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getSubscriptionReport API Error: ${response.code()} - $errorBody")
                
                val cached = securePrefs.getSubscriptionReport()
                if (cached != null) {
                    android.util.Log.i("Repository", "getSubscriptionReport: falling back to cache")
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getSubscriptionReport Network/Parse Exception", e)
            
            val cached = securePrefs.getSubscriptionReport()
            if (cached != null) {
                android.util.Log.i("Repository", "getSubscriptionReport: falling back to cache on exception")
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun updateCategory(txId: String, categoryId: java.util.UUID): Result<Unit> {
        return try {
            val response = api.updateCategory(txId, CategoryUpdateDto(categoryId))
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "Update Category Error: $errorBody")
                Result.failure(Exception("HTTP ${response.code()}: $errorBody"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getTransactions(
        page: Int,
        size: Int,
        search: String?,
        category: String?,
        merchant: String?,
        minAmount: Float?,
        maxAmount: Float?,
        sort: String
    ): Result<PaginatedTransactionResponse> {
        return try {
            val response = api.getTransactions(
                page = page,
                size = size,
                search = search,
                category = category,
                merchant = merchant,
                minAmount = minAmount,
                maxAmount = maxAmount,
                sort = sort
            )
            if (response.isSuccessful) {
                response.body()?.let { Result.success(it) }
                    ?: Result.failure(Exception("Paginated transaction response body is null"))
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getTransactions API Error: ${response.code()} - $errorBody")
                Result.failure(Exception("API Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getTransactions Network/Parse Exception", e)
            Result.failure(e)
        }
    }

    private suspend fun queueForRetry(userId: String, rawText: String) {
        // Network failed. Save to local Room DB queue
        dao.insert(TransactionEntity(userId = userId, rawText = rawText))
        
        // Trigger WorkManager to retry later
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
            
        val workRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .build()
            
        WorkManager.getInstance(context).enqueue(workRequest)
    }
}
