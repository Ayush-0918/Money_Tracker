package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.PaginatedTransactionResponse

interface TransactionRepository {
    suspend fun syncTransaction(rawText: String)
    suspend fun getDashboardSummary(): Result<DashboardSummaryDto>
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
