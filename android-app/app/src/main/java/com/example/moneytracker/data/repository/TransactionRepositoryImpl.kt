package com.example.moneytracker.data.repository

import android.content.Context
import androidx.work.Constraints
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.example.moneytracker.data.local.dao.TransactionDao
import com.example.moneytracker.data.local.entity.TransactionEntity
import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.PaginatedTransactionResponse
import com.example.moneytracker.data.remote.dto.TransactionRequest
import com.example.moneytracker.data.remote.dto.CategoryUpdateDto
import com.example.moneytracker.domain.repository.TransactionRepository
import com.example.moneytracker.service.sync.SyncWorker
import com.example.moneytracker.util.Constants
import com.example.moneytracker.util.SecurePrefs
class TransactionRepositoryImpl(
    private val api: ApiService,
    private val dao: TransactionDao,
    private val securePrefs: SecurePrefs,
    private val context: Context
) : TransactionRepository {

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
            if (response.isSuccessful) {
                response.body()?.let { Result.success(it) }
                    ?: Result.failure(Exception("Dashboard summary response body is null"))
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("Repository", "getDashboardSummary API Error: ${response.code()} - $errorBody")
                Result.failure(Exception("API Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            android.util.Log.e("Repository", "getDashboardSummary Network/Parse Exception", e)
            Result.failure(e)
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
