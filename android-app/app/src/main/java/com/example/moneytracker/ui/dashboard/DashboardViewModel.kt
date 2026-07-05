package com.example.moneytracker.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.domain.repository.TransactionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class DashboardUiState {
    object Loading : DashboardUiState()
    data class Success(
        val summary: DashboardSummaryDto
    ) : DashboardUiState()
    data class Error(val message: String) : DashboardUiState()
}

class DashboardViewModel(
    private val repository: TransactionRepository,
    private val userId: String // Passed via factory
) : ViewModel() {

    private val _uiState = MutableStateFlow<DashboardUiState>(DashboardUiState.Loading)
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    private val _selectedTransactionForCategorize = MutableStateFlow<String?>(null)
    val selectedTransactionForCategorize: StateFlow<String?> = _selectedTransactionForCategorize.asStateFlow()

    init {
        loadDashboardData()
    }

    fun loadDashboardData() {
        android.util.Log.d("DashboardVM", "Loading dashboard data for userId: $userId")
        viewModelScope.launch {
            _uiState.value = DashboardUiState.Loading
            
            val result = repository.getDashboardSummary()
            
            if (result.isSuccess) {
                _uiState.value = DashboardUiState.Success(
                    summary = result.getOrThrow()
                )
            } else {
                val errorMsg = result.exceptionOrNull()?.message ?: "Unknown Error"
                android.util.Log.e("DashboardVM", "Error loading data: $errorMsg")
                _uiState.value = DashboardUiState.Error("Data load nahi ho paaya, dobara try karein")
            }
        }
    }

    fun onCategorizeClicked(txId: String?) {
        _selectedTransactionForCategorize.value = txId
    }

    fun confirmCategorize(txId: String, categoryId: java.util.UUID, categoryDisplayName: String) {
        // Optimistic UI Update
        val currentState = _uiState.value
        if (currentState is DashboardUiState.Success) {
            val updatedList = currentState.summary.latest_transactions.map {
                if (it.id == txId) it.copy(category = categoryDisplayName) else it
            }
            
            _uiState.value = DashboardUiState.Success(
                summary = currentState.summary.copy(latest_transactions = updatedList)
            )
        }

        _selectedTransactionForCategorize.value = null // Dismiss sheet

        viewModelScope.launch {
            val result = repository.updateCategory(txId, categoryId)
            if (result.isFailure) {
                // Revert or show error in production
                android.util.Log.e("DashboardVM", "Failed to update category remotely")
            }
        }
    }
}
