package com.example.moneytracker.data.remote.dto

import com.google.gson.annotations.SerializedName

// ── Notification DTOs ────────────────────────────────────────────────────────

data class DeviceTokenRegisterDto(
    @SerializedName("token") val token: String,
    @SerializedName("device_type") val deviceType: String = "android"
)

data class NotificationDto(
    @SerializedName("id") val id: String,
    @SerializedName("title") val title: String,
    @SerializedName("body") val body: String,
    @SerializedName("notification_type") val notificationType: String, // "alert", "insight", "subscription"
    @SerializedName("is_read") val isRead: Boolean,
    @SerializedName("created_at") val createdAt: String
)
