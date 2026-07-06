package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.PaginatedTransactionResponse
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import kotlinx.coroutines.flow.Flow

interface TransactionRepository {
    fun getCachedTransactions(): Flow<List<TransactionItemDto>>
    suspend fun refreshTransactions(): Result<Unit>

    suspend fun syncTransaction(rawText: String)
    suspend fun getDashboardSummary(): Result<DashboardSummaryDto>
    suspend fun getMonthlyReport(userId: String): Result<com.example.moneytracker.data.remote.dto.MonthlyReportDto>
    suspend fun getWeeklyReport(userId: String): Result<com.example.moneytracker.data.remote.dto.WeeklyActivityDto>
    suspend fun getSubscriptionReport(userId: String): Result<List<com.example.moneytracker.data.remote.dto.SubscriptionDto>>
    suspend fun updateCategory(txId: String, categoryId: java.util.UUID): Result<Unit>
    suspend fun getTransactions(
        page: Int,
        size: Int,
        search: String? = null,
        category: String? = null,
        merchant: String? = null,
        minAmount: Float? = null,
        maxAmount: Float? = null,
        sort: String = "date_desc"
    ): Result<PaginatedTransactionResponse>
}
