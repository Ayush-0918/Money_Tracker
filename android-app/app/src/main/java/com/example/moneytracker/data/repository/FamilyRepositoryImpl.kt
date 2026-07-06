package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.*
import com.example.moneytracker.domain.repository.FamilyRepository

class FamilyRepositoryImpl(
    private val api: ApiService
) : FamilyRepository {

    override suspend fun createFamilyWallet(name: String): Result<FamilyWalletResponseDto> {
        return try {
            val response = api.createFamilyWallet(FamilyWalletCreateDto(name))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to create wallet: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun joinFamilyWallet(inviteCode: String): Result<FamilyWalletResponseDto> {
        return try {
            val response = api.joinFamilyWallet(inviteCode)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to join wallet: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getFamilyWallets(): Result<List<FamilyWalletResponseDto>> {
        return try {
            val response = api.getFamilyWallets()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch wallets: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getFamilyWalletDetails(walletId: String): Result<FamilyWalletResponseDto> {
        return try {
            val response = api.getFamilyWalletDetails(walletId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch details: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun addFamilyExpense(
        walletId: String,
        amount: Double,
        description: String,
        categoryId: String?
    ): Result<SharedExpenseDto> {
        return try {
            val response = api.addFamilyExpense(walletId, SharedExpenseCreateDto(amount, description, categoryId))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to add expense: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getFamilySummary(walletId: String): Result<FamilySummaryResponseDto> {
        return try {
            val response = api.getFamilySummary(walletId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch summary: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
