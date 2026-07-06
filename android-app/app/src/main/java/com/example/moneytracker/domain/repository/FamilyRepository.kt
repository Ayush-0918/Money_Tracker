package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.*

interface FamilyRepository {
    suspend fun createFamilyWallet(name: String): Result<FamilyWalletResponseDto>
    suspend fun joinFamilyWallet(inviteCode: String): Result<FamilyWalletResponseDto>
    suspend fun getFamilyWallets(): Result<List<FamilyWalletResponseDto>>
    suspend fun getFamilyWalletDetails(walletId: String): Result<FamilyWalletResponseDto>
    suspend fun addFamilyExpense(walletId: String, amount: Double, description: String, categoryId: String?): Result<SharedExpenseDto>
    suspend fun getFamilySummary(walletId: String): Result<FamilySummaryResponseDto>
}
