package com.example.moneytracker.ui.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.AIPredictionResponseDto
import com.example.moneytracker.domain.repository.PredictionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class PredictionUiState {
    object Loading : PredictionUiState()
    data class Success(val predictions: AIPredictionResponseDto) : PredictionUiState()
    data class Error(val message: String) : PredictionUiState()
}

class PredictionViewModel(
    private val repository: PredictionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<PredictionUiState>(PredictionUiState.Loading)
    val uiState: StateFlow<PredictionUiState> = _uiState.asStateFlow()

    init {
        loadPredictions()
    }

    fun loadPredictions() {
        _uiState.value = PredictionUiState.Loading
        viewModelScope.launch {
            val result = repository.getPredictions()
            if (result.isSuccess) {
                _uiState.value = PredictionUiState.Success(result.getOrThrow())
            } else {
                val error = result.exceptionOrNull()?.message ?: "Failed to load financial predictions"
                _uiState.value = PredictionUiState.Error(error)
            }
        }
    }

    fun refreshPredictions() {
        _uiState.value = PredictionUiState.Loading
        viewModelScope.launch {
            val result = repository.refreshPredictions()
            if (result.isSuccess) {
                _uiState.value = PredictionUiState.Success(result.getOrThrow())
            } else {
                val error = result.exceptionOrNull()?.message ?: "Failed to refresh predictions"
                _uiState.value = PredictionUiState.Error(error)
            }
        }
    }
}

class PredictionViewModelFactory(
    private val repository: PredictionRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(PredictionViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return PredictionViewModel(repository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
