package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.AIPredictionResponseDto

interface PredictionRepository {
    suspend fun getPredictions(): Result<AIPredictionResponseDto>
    suspend fun refreshPredictions(): Result<AIPredictionResponseDto>
}
