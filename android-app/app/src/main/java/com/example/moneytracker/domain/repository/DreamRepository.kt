package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.DreamResponseDto

interface DreamRepository {
    suspend fun createDream(name: String, targetAmount: Double, deadline: String): Result<DreamResponseDto>
    suspend fun getDreams(): Result<List<DreamResponseDto>>
    suspend fun addDreamProgress(dreamId: String, amount: Double): Result<DreamResponseDto>
}
