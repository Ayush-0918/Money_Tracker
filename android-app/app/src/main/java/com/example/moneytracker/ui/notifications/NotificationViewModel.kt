package com.example.moneytracker.ui.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.NotificationDto
import com.example.moneytracker.domain.repository.NotificationRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class NotificationUiState {
    object Loading : NotificationUiState()
    data class Success(val notifications: List<NotificationDto>) : NotificationUiState()
    data class Error(val message: String) : NotificationUiState()
}

class NotificationViewModel(
    private val repository: NotificationRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<NotificationUiState>(NotificationUiState.Loading)
    val uiState: StateFlow<NotificationUiState> = _uiState.asStateFlow()

    init {
        loadNotifications()
    }

    fun loadNotifications() {
        viewModelScope.launch {
            _uiState.value = NotificationUiState.Loading
            repository.getNotifications()
                .onSuccess { list ->
                    _uiState.value = NotificationUiState.Success(list)
                }
                .onFailure { error ->
                    _uiState.value = NotificationUiState.Error(
                        error.message ?: "Failed to load notifications"
                    )
                }
        }
    }

    fun markAsRead(ids: List<String>) {
        if (ids.isEmpty()) return
        viewModelScope.launch {
            repository.markAsRead(ids)
                .onSuccess {
                    loadNotifications()
                }
                .onFailure {
                    // Fail silently or fallback load
                    loadNotifications()
                }
        }
    }

    fun registerPushToken(token: String) {
        viewModelScope.launch {
            repository.registerDeviceToken(token)
        }
    }
}
