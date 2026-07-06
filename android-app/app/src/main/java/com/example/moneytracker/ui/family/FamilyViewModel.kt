package com.example.moneytracker.ui.family

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.moneytracker.data.remote.dto.FamilyWalletResponseDto
import com.example.moneytracker.data.remote.dto.FamilySummaryResponseDto
import com.example.moneytracker.data.remote.dto.SharedExpenseDto
import com.example.moneytracker.domain.repository.FamilyRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class FamilyUiState {
    object Loading : FamilyUiState()
    data class WalletsLoaded(val wallets: List<FamilyWalletResponseDto>) : FamilyUiState()
    data class WalletDetails(
        val wallet: FamilyWalletResponseDto,
        val summary: FamilySummaryResponseDto
    ) : FamilyUiState()
    data class Error(val message: String) : FamilyUiState()
}

class FamilyViewModel(
    private val repository: FamilyRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<FamilyUiState>(FamilyUiState.Loading)
    val uiState: StateFlow<FamilyUiState> = _uiState.asStateFlow()

    init {
        loadWallets()
    }

    fun loadWallets() {
        viewModelScope.launch {
            _uiState.value = FamilyUiState.Loading
            repository.getFamilyWallets()
                .onSuccess { list ->
                    _uiState.value = FamilyUiState.WalletsLoaded(list)
                }
                .onFailure { error ->
                    _uiState.value = FamilyUiState.Error(error.message ?: "Failed to load Family Wallets")
                }
        }
    }

    fun selectWallet(walletId: String) {
        viewModelScope.launch {
            _uiState.value = FamilyUiState.Loading
            
            val detailsResult = repository.getFamilyWalletDetails(walletId)
            val summaryResult = repository.getFamilySummary(walletId)

            if (detailsResult.isSuccess && summaryResult.isSuccess) {
                _uiState.value = FamilyUiState.WalletDetails(
                    wallet = detailsResult.getOrNull()!!,
                    summary = summaryResult.getOrNull()!!
                )
            } else {
                val errorMsg = detailsResult.exceptionOrNull()?.message 
                    ?: summaryResult.exceptionOrNull()?.message 
                    ?: "Failed to load wallet details"
                _uiState.value = FamilyUiState.Error(errorMsg)
            }
        }
    }

    fun createWallet(name: String) {
        viewModelScope.launch {
            _uiState.value = FamilyUiState.Loading
            repository.createFamilyWallet(name)
                .onSuccess {
                    loadWallets()
                }
                .onFailure { error ->
                    _uiState.value = FamilyUiState.Error(error.message ?: "Failed to create Family Wallet")
                }
        }
    }

    fun joinWallet(inviteCode: String) {
        viewModelScope.launch {
            _uiState.value = FamilyUiState.Loading
            repository.joinFamilyWallet(inviteCode)
                .onSuccess {
                    loadWallets()
                }
                .onFailure { error ->
                    _uiState.value = FamilyUiState.Error(error.message ?: "Failed to join Family Wallet")
                }
        }
    }

    fun addExpense(walletId: String, amount: Double, description: String, categoryId: String? = null) {
        viewModelScope.launch {
            repository.addFamilyExpense(walletId, amount, description, categoryId)
                .onSuccess {
                    selectWallet(walletId)
                }
                .onFailure { error ->
                    _uiState.value = FamilyUiState.Error(error.message ?: "Failed to add shared expense")
                }
        }
    }
}
