package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.NotificationDto

interface NotificationRepository {
    suspend fun registerDeviceToken(token: String): Result<Unit>
    suspend fun getNotifications(): Result<List<NotificationDto>>
    suspend fun markAsRead(ids: List<String>): Result<Unit>
}
