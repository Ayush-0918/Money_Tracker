package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.MoneyStoryResponseDto
import com.example.moneytracker.domain.repository.MoneyStoryRepository
import com.example.moneytracker.util.SecurePrefs

class MoneyStoryRepositoryImpl(
    private val api: ApiService,
    private val securePrefs: SecurePrefs
) : MoneyStoryRepository {

    override suspend fun getMoneyStory(userId: String): Result<MoneyStoryResponseDto> {
        return try {
            val response = api.getMoneyStory(userId)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                securePrefs.saveMoneyStory(body)
                Result.success(body)
            } else {
                val cached = securePrefs.getMoneyStory()
                if (cached != null) {
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API error ${response.code()}: ${response.message()}"))
                }
            }
        } catch (e: Exception) {
            val cached = securePrefs.getMoneyStory()
            if (cached != null) {
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun refreshMoneyStory(userId: String): Result<MoneyStoryResponseDto> {
        return try {
            val response = api.refreshMoneyStory(userId)
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                securePrefs.saveMoneyStory(body)
                Result.success(body)
            } else {
                Result.failure(Exception("Refresh API error ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
