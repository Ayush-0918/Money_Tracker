package com.example.moneytracker.ui.reports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.WeeklyReportResponseDto
import com.example.moneytracker.domain.repository.WeeklyReportRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class WeeklyReportUiState {
    object Loading : WeeklyReportUiState()
    data class Success(val report: WeeklyReportResponseDto) : WeeklyReportUiState()
    data class Error(val message: String) : WeeklyReportUiState()
}

class WeeklyReportViewModel(
    private val repository: WeeklyReportRepository,
    private val userId: String
) : ViewModel() {

    private val _uiState = MutableStateFlow<WeeklyReportUiState>(WeeklyReportUiState.Loading)
    val uiState: StateFlow<WeeklyReportUiState> = _uiState.asStateFlow()

    init {
        loadReport()
    }

    fun loadReport() {
        viewModelScope.launch {
            _uiState.value = WeeklyReportUiState.Loading
            repository.getWeeklyReport(userId)
                .onSuccess { report ->
                    _uiState.value = WeeklyReportUiState.Success(report)
                }
                .onFailure { error ->
                    _uiState.value = WeeklyReportUiState.Error(
                        error.message ?: "Failed to load weekly report"
                    )
                }
        }
    }
}
