package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.AIPredictionResponseDto
import com.example.moneytracker.domain.repository.PredictionRepository
import com.example.moneytracker.util.SecurePrefs

class PredictionRepositoryImpl(
    private val api: ApiService,
    private val securePrefs: SecurePrefs
) : PredictionRepository {

    override suspend fun getPredictions(): Result<AIPredictionResponseDto> {
        return try {
            val response = api.getPredictions()
            if (response.isSuccessful && response.body() != null) {
                val predictions = response.body()!!
                securePrefs.savePredictions(predictions)
                Result.success(predictions)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("PredictionRepo", "getPredictions API Error: ${response.code()} - $errorBody")
                val cached = securePrefs.getPredictions()
                if (cached != null) {
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API Error: ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("PredictionRepo", "getPredictions Exception", e)
            val cached = securePrefs.getPredictions()
            if (cached != null) {
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    override suspend fun refreshPredictions(): Result<AIPredictionResponseDto> {
        return try {
            val response = api.refreshPredictions()
            if (response.isSuccessful && response.body() != null) {
                val predictions = response.body()!!
                securePrefs.savePredictions(predictions)
                Result.success(predictions)
            } else {
                val errorBody = response.errorBody()?.string()
                android.util.Log.e("PredictionRepo", "refreshPredictions API Error: ${response.code()} - $errorBody")
                Result.failure(Exception("API Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            android.util.Log.e("PredictionRepo", "refreshPredictions Exception", e)
            Result.failure(e)
        }
    }
}
