package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.DreamCreateDto
import com.example.moneytracker.data.remote.dto.DreamResponseDto
import com.example.moneytracker.data.remote.dto.DreamUpdateProgressDto
import com.example.moneytracker.domain.repository.DreamRepository

class DreamRepositoryImpl(
    private val api: ApiService
) : DreamRepository {

    override suspend fun createDream(
        name: String,
        targetAmount: Double,
        deadline: String
    ): Result<DreamResponseDto> {
        return try {
            val response = api.createDream(DreamCreateDto(name, targetAmount, deadline))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to register dream: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getDreams(): Result<List<DreamResponseDto>> {
        return try {
            val response = api.getDreams()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to load dreams: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun addDreamProgress(
        dreamId: String,
        amount: Double
    ): Result<DreamResponseDto> {
        return try {
            val response = api.addDreamProgress(dreamId, DreamUpdateProgressDto(amount))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to update progress: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
