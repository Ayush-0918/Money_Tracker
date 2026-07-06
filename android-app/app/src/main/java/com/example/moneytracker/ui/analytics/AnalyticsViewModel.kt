package com.example.moneytracker.ui.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.domain.repository.TransactionRepository
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class AnalyticsReportData(
    val totalSpend: String,
    val totalBalance: String,
    val monthlyIncome: String,
    val monthlySavings: String,
    val spendDiffText: String,
    val spendDiffIsPositive: Boolean,
    val categories: Map<String, Float>,
    val recentTransactions: List<com.example.moneytracker.data.remote.dto.TransactionItemDto>,
    val weeklyPoints: List<Float>,
    val weeklyAverage: Float,
    val upcomingSubscriptions: List<com.example.moneytracker.data.remote.dto.SubscriptionDto>,
    val budgets: List<com.example.moneytracker.data.remote.dto.BudgetSummaryResponse>,
    val aiInsights: String?,
    val savingTips: String?
)

sealed class AnalyticsUiState {
    object Loading : AnalyticsUiState()
    data class Success(val data: AnalyticsReportData) : AnalyticsUiState()
    data class Error(val message: String) : AnalyticsUiState()
}

class AnalyticsViewModel(
    private val repository: TransactionRepository,
    private val userId: String
) : ViewModel() {

    private val _uiState = MutableStateFlow<AnalyticsUiState>(AnalyticsUiState.Loading)
    val uiState: StateFlow<AnalyticsUiState> = _uiState.asStateFlow()

    init {
        loadAnalytics()
    }

    fun loadAnalytics() {
        _uiState.value = AnalyticsUiState.Loading
        viewModelScope.launch {
            try {
                val monthlyDeferred = async { repository.getMonthlyReport(userId) }
                val weeklyDeferred = async { repository.getWeeklyReport(userId) }
                val subsDeferred = async { repository.getSubscriptionReport(userId) }
                val dashboardDeferred = async { repository.getDashboardSummary() }

                val monthlyResult = monthlyDeferred.await()
                val weeklyResult = weeklyDeferred.await()
                val subsResult = subsDeferred.await()
                val dashboardResult = dashboardDeferred.await()

                if (monthlyResult.isSuccess && weeklyResult.isSuccess && subsResult.isSuccess && dashboardResult.isSuccess) {
                    val monthly = monthlyResult.getOrThrow()
                    val weekly = weeklyResult.getOrThrow()
                    val subs = subsResult.getOrThrow()
                    val dashboard = dashboardResult.getOrThrow()

                    _uiState.value = AnalyticsUiState.Success(
                        AnalyticsReportData(
                            totalSpend = monthly.total_spend_formatted,
                            totalBalance = monthly.total_balance_formatted,
                            monthlyIncome = monthly.income_formatted,
                            monthlySavings = monthly.savings_formatted,
                            spendDiffText = monthly.spend_diff_text,
                            spendDiffIsPositive = monthly.spend_diff_is_positive,
                            categories = monthly.categories,
                            recentTransactions = monthly.recent_transactions,
                            weeklyPoints = weekly.points,
                            weeklyAverage = weekly.average_per_day,
                            upcomingSubscriptions = subs,
                            budgets = dashboard.budgets,
                            aiInsights = dashboard.ai_insights,
                            savingTips = dashboard.saving_tips
                        )
                    )
                } else {
                    val errors = listOf(
                        monthlyResult.exceptionOrNull()?.message,
                        weeklyResult.exceptionOrNull()?.message,
                        subsResult.exceptionOrNull()?.message,
                        dashboardResult.exceptionOrNull()?.message
                    ).filterNotNull().joinToString(", ")
                    _uiState.value = AnalyticsUiState.Error(errors.ifEmpty { "Failed to load analytics" })
                }
            } catch (e: Exception) {
                _uiState.value = AnalyticsUiState.Error(e.message ?: "Failed to load analytics")
            }
        }
    }
}

class AnalyticsViewModelFactory(
    private val repository: TransactionRepository,
    private val userId: String
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(AnalyticsViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return AnalyticsViewModel(repository, userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
