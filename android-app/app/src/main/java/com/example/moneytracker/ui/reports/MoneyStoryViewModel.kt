package com.example.moneytracker.ui.reports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.MoneyStoryResponseDto
import com.example.moneytracker.domain.repository.MoneyStoryRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class MoneyStoryUiState {
    object Loading : MoneyStoryUiState()
    data class Success(val story: MoneyStoryResponseDto) : MoneyStoryUiState()
    data class Error(val message: String) : MoneyStoryUiState()
}

class MoneyStoryViewModel(
    private val repository: MoneyStoryRepository,
    private val userId: String
) : ViewModel() {

    private val _uiState = MutableStateFlow<MoneyStoryUiState>(MoneyStoryUiState.Loading)
    val uiState: StateFlow<MoneyStoryUiState> = _uiState.asStateFlow()

    init {
        loadStory()
    }

    fun loadStory() {
        viewModelScope.launch {
            _uiState.value = MoneyStoryUiState.Loading
            repository.getMoneyStory(userId)
                .onSuccess { story ->
                    _uiState.value = MoneyStoryUiState.Success(story)
                }
                .onFailure { error ->
                    _uiState.value = MoneyStoryUiState.Error(
                        error.message ?: "Failed to load Sunday Money Story"
                    )
                }
        }
    }

    fun refreshStory() {
        viewModelScope.launch {
            _uiState.value = MoneyStoryUiState.Loading
            repository.refreshMoneyStory(userId)
                .onSuccess { story ->
                    _uiState.value = MoneyStoryUiState.Success(story)
                }
                .onFailure { error ->
                    _uiState.value = MoneyStoryUiState.Error(
                        error.message ?: "Failed to regenerate Sunday Money Story"
                    )
                }
        }
    }
}
