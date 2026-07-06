package com.example.moneytracker.ui.dreams

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.DreamResponseDto
import com.example.moneytracker.domain.repository.DreamRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class DreamUiState {
    object Loading : DreamUiState()
    data class Success(val dreams: List<DreamResponseDto>) : DreamUiState()
    data class Error(val message: String) : DreamUiState()
}

class DreamViewModel(
    private val repository: DreamRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<DreamUiState>(DreamUiState.Loading)
    val uiState: StateFlow<DreamUiState> = _uiState.asStateFlow()

    init {
        loadDreams()
    }

    fun loadDreams() {
        viewModelScope.launch {
            _uiState.value = DreamUiState.Loading
            repository.getDreams()
                .onSuccess { list ->
                    _uiState.value = DreamUiState.Success(list)
                }
                .onFailure { error ->
                    _uiState.value = DreamUiState.Error(
                        error.message ?: "Failed to fetch dreams"
                    )
                }
        }
    }

    fun createDream(name: String, targetAmount: Double, deadline: String) {
        viewModelScope.launch {
            _uiState.value = DreamUiState.Loading
            repository.createDream(name, targetAmount, deadline)
                .onSuccess {
                    loadDreams()
                }
                .onFailure { error ->
                    _uiState.value = DreamUiState.Error(
                        error.message ?: "Failed to add dream goal"
                    )
                }
        }
    }

    fun logProgress(dreamId: String, amount: Double) {
        viewModelScope.launch {
            _uiState.value = DreamUiState.Loading
            repository.addDreamProgress(dreamId, amount)
                .onSuccess {
                    loadDreams()
                }
                .onFailure { error ->
                    _uiState.value = DreamUiState.Error(
                        error.message ?: "Failed to update savings progress"
                    )
                }
        }
    }
}
