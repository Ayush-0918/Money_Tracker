package com.example.moneytracker.data.remote.api

import com.example.moneytracker.data.remote.dto.MonthlyReportDto
import com.example.moneytracker.data.remote.dto.SubscriptionDto
import com.example.moneytracker.data.remote.dto.TransactionRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import com.example.moneytracker.data.remote.dto.PaginatedTransactionResponse
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.CategoryResponse
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.CategoryUpdateDto

interface ApiService {
    @POST("auth/register")
    suspend fun register(
        @Body request: Map<String, String>
    ): Response<Map<String, String>>

    @POST("transactions")
    suspend fun postTransaction(
        @Body request: TransactionRequest
    ): Response<Unit>

    @GET("dashboard/summary")
    suspend fun getDashboardSummary(): Response<DashboardSummaryDto>

    @GET("reports/monthly/{userId}")
    suspend fun getMonthlyReport(
        @Path("userId") userId: String
    ): Response<MonthlyReportDto>

    @GET("reports/weekly/{userId}")
    suspend fun getWeeklyReport(
        @Path("userId") userId: String
    ): Response<com.example.moneytracker.data.remote.dto.WeeklyActivityDto>

    @GET("reports/subscriptions/{userId}")
    suspend fun getSubscriptionReport(
        @Path("userId") userId: String
    ): Response<List<com.example.moneytracker.data.remote.dto.SubscriptionDto>>

    @PATCH("transactions/{id}/category")
    suspend fun updateCategory(
        @Path("id") txId: String,
        @Body request: CategoryUpdateDto
    ): Response<Unit>

    @GET("categories")
    suspend fun getCategories(): Response<List<CategoryResponse>>

    @GET("budgets/summary")
    suspend fun getBudgetSummary(): Response<List<BudgetSummaryResponse>>

    @POST("budgets")
    suspend fun createBudget(
        @Body request: BudgetCreateRequest
    ): Response<Unit>

    @GET("transactions")
    suspend fun getTransactions(
        @Query("page") page: Int = 1,
        @Query("size") size: Int = 20,
        @Query("search") search: String? = null,
        @Query("category") category: String? = null,
        @Query("merchant") merchant: String? = null,
        @Query("min_amount") minAmount: Float? = null,
        @Query("max_amount") maxAmount: Float? = null,
        @Query("sort") sort: String = "date_desc"
    ): Response<PaginatedTransactionResponse>
}
