package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.DeviceTokenRegisterDto
import com.example.moneytracker.data.remote.dto.NotificationDto
import com.example.moneytracker.domain.repository.NotificationRepository

class NotificationRepositoryImpl(
    private val api: ApiService
) : NotificationRepository {

    override suspend fun registerDeviceToken(token: String): Result<Unit> {
        return try {
            val response = api.registerDevice(DeviceTokenRegisterDto(token))
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("Token register failed: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getNotifications(): Result<List<NotificationDto>> {
        return try {
            val response = api.getNotifications()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Get notifications failed: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun markAsRead(ids: List<String>): Result<Unit> {
        return try {
            val response = api.readNotifications(ids)
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("Read updates failed: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
