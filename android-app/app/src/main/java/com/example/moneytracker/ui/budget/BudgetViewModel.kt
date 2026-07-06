package com.example.moneytracker.ui.budget

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.BudgetCreateRequest
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import com.example.moneytracker.data.remote.dto.CategoryResponse
import com.example.moneytracker.domain.repository.BudgetRepository
import com.example.moneytracker.domain.repository.CategoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class BudgetUiState(
    val isLoading: Boolean = true,
    val budgets: List<BudgetSummaryResponse> = emptyList(),
    val categories: List<CategoryResponse> = emptyList(),
    val error: String? = null
)

class BudgetViewModel(
    private val budgetRepository: BudgetRepository,
    private val categoryRepository: CategoryRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(BudgetUiState())
    val uiState: StateFlow<BudgetUiState> = _uiState.asStateFlow()

    init {
        // SSOT: Observe local cache
        viewModelScope.launch {
            budgetRepository.getCachedBudgets().collectLatest { cached ->
                if (cached.isNotEmpty()) {
                    _uiState.update { it.copy(budgets = cached, isLoading = false) }
                }
            }
        }
        loadData() // Initial sync
    }

    fun loadData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            val categoriesResult = categoryRepository.getCategories()
            val budgetsResult = budgetRepository.refreshBudgets()

            if (categoriesResult.isSuccess && budgetsResult.isSuccess) {
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        categories = categoriesResult.getOrNull() ?: emptyList()
                    ) 
                }
            } else {
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        error = "Failed to load budget data from server."
                    )
                }
            }
        }
    }

    fun createBudget(categoryId: java.util.UUID, limit: Double) {
        viewModelScope.launch {
            val result = budgetRepository.createBudget(BudgetCreateRequest(categoryId, limit))
            if (result.isSuccess) {
                loadData() // Refresh list after creation
            } else {
                _uiState.update { it.copy(error = "Failed to create budget") }
            }
        }
    }
}

class BudgetViewModelFactory(
    private val budgetRepository: BudgetRepository,
    private val categoryRepository: CategoryRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(BudgetViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return BudgetViewModel(budgetRepository, categoryRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
