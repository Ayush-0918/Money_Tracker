package com.example.moneytracker.ui.activity

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import com.example.moneytracker.domain.repository.TransactionRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ActivityState(
    val transactions: List<TransactionItemDto> = emptyList(),
    val isLoading: Boolean = false,
    val isPaginating: Boolean = false,
    val error: String? = null,
    val hasMore: Boolean = true,
    val page: Int = 1,
    // Filters
    val searchQuery: String = "",
    val categoryFilter: String? = null,
    val sortOrder: String = "date_desc"
)

class ActivityViewModel(
    private val repository: TransactionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ActivityState())
    val uiState: StateFlow<ActivityState> = _uiState.asStateFlow()

    private var searchJob: Job? = null
    
    // Config
    private val pageSize = 20

    init {
        loadTransactions(reset = true)
    }

    fun onSearchQueryChanged(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(500) // Debounce
            loadTransactions(reset = true)
        }
    }

    fun onCategoryFilterChanged(category: String?) {
        _uiState.update { it.copy(categoryFilter = category) }
        loadTransactions(reset = true)
    }

    fun onSortOrderChanged(sortOrder: String) {
        _uiState.update { it.copy(sortOrder = sortOrder) }
        loadTransactions(reset = true)
    }

    fun loadNextPage() {
        if (_uiState.value.isPaginating || !_uiState.value.hasMore || _uiState.value.isLoading) return
        loadTransactions(reset = false)
    }

    fun refresh() {
        loadTransactions(reset = true)
    }

    private fun loadTransactions(reset: Boolean) {
        if (reset) {
            _uiState.update { it.copy(isLoading = true, error = null, page = 1, transactions = emptyList(), hasMore = true) }
        } else {
            _uiState.update { it.copy(isPaginating = true, error = null) }
        }

        viewModelScope.launch {
            val currentState = _uiState.value
            val result = repository.getTransactions(
                page = currentState.page,
                size = pageSize,
                search = currentState.searchQuery.takeIf { it.isNotBlank() },
                category = currentState.categoryFilter,
                sort = currentState.sortOrder
            )

            result.onSuccess { paginatedResponse ->
                _uiState.update { state ->
                    val newTransactions = if (reset) {
                        paginatedResponse.items
                    } else {
                        state.transactions + paginatedResponse.items
                    }
                    state.copy(
                        transactions = newTransactions,
                        hasMore = paginatedResponse.has_more,
                        page = state.page + 1,
                        isLoading = false,
                        isPaginating = false
                    )
                }
            }.onFailure { exception ->
                _uiState.update { state ->
                    state.copy(
                        error = exception.message ?: "An unknown error occurred",
                        isLoading = false,
                        isPaginating = false
                    )
                }
            }
        }
    }

    fun updateCategory(txId: String, categoryId: java.util.UUID) {
        viewModelScope.launch {
            val result = repository.updateCategory(txId, categoryId)
            if (result.isSuccess) {
                // To reflect the updated category immediately, we could modify local state,
                // but refreshing guarantees sync with the new AI LearningEvent logic
                loadTransactions(reset = true)
            } else {
                _uiState.update { it.copy(error = result.exceptionOrNull()?.message ?: "Failed to update category") }
            }
        }
    }
}

class ActivityViewModelFactory(
    private val repository: TransactionRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ActivityViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ActivityViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
