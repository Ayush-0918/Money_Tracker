package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.MoneyStoryResponseDto

interface MoneyStoryRepository {
    suspend fun getMoneyStory(userId: String): Result<MoneyStoryResponseDto>
    suspend fun refreshMoneyStory(userId: String): Result<MoneyStoryResponseDto>
}
