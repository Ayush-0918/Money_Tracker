package com.example.moneytracker.util

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecurePrefs(context: Context) {
    private val appContext = context.applicationContext
    private val masterKey = MasterKey.Builder(appContext)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        appContext,
        "money_tracker_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveApiKey(key: String) {
        prefs.edit().putString("api_key", key).apply()
    }

    fun getApiKey(): String? {
        return prefs.getString("api_key", null)
    }

    fun saveUserId(id: String) {
        android.util.Log.d("SecurePrefs", "Saving userId: $id")
        prefs.edit().putString("user_id", id).apply()
    }

    fun getUserId(): String? {
        val id = prefs.getString("user_id", null)
        android.util.Log.d("SecurePrefs", "Retrieved userId: $id")
        return id
    }

    fun saveDbPassword(password: String) {
        prefs.edit().putString("db_password", password).apply()
    }

    fun getDbPassword(): String? {
        return prefs.getString("db_password", null)
    }

    fun saveToken(token: String) {
        prefs.edit().putString("auth_token", token).apply()
    }

    fun getToken(): String? {
        return prefs.getString("auth_token", null)
    }

    fun saveDashboardSummary(summary: com.example.moneytracker.data.remote.dto.DashboardSummaryDto) {
        val json = com.google.gson.Gson().toJson(summary)
        prefs.edit().putString("cache_dashboard_summary", json).apply()
    }

    fun getDashboardSummary(): com.example.moneytracker.data.remote.dto.DashboardSummaryDto? {
        val json = prefs.getString("cache_dashboard_summary", null) ?: return null
        return try {
            com.google.gson.Gson().fromJson(json, com.example.moneytracker.data.remote.dto.DashboardSummaryDto::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun saveMonthlyReport(report: com.example.moneytracker.data.remote.dto.MonthlyReportDto) {
        val json = com.google.gson.Gson().toJson(report)
        prefs.edit().putString("cache_monthly_report", json).apply()
    }

    fun getMonthlyReport(): com.example.moneytracker.data.remote.dto.MonthlyReportDto? {
        val json = prefs.getString("cache_monthly_report", null) ?: return null
        return try {
            com.google.gson.Gson().fromJson(json, com.example.moneytracker.data.remote.dto.MonthlyReportDto::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun saveWeeklyReport(report: com.example.moneytracker.data.remote.dto.WeeklyActivityDto) {
        val json = com.google.gson.Gson().toJson(report)
        prefs.edit().putString("cache_weekly_report", json).apply()
    }

    fun getWeeklyReport(): com.example.moneytracker.data.remote.dto.WeeklyActivityDto? {
        val json = prefs.getString("cache_weekly_report", null) ?: return null
        return try {
            com.google.gson.Gson().fromJson(json, com.example.moneytracker.data.remote.dto.WeeklyActivityDto::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun saveSubscriptionReport(subscriptions: List<com.example.moneytracker.data.remote.dto.SubscriptionDto>) {
        val json = com.google.gson.Gson().toJson(subscriptions)
        prefs.edit().putString("cache_subscriptions", json).apply()
    }

    fun getSubscriptionReport(): List<com.example.moneytracker.data.remote.dto.SubscriptionDto>? {
        val json = prefs.getString("cache_subscriptions", null) ?: return null
        return try {
            val type = object : com.google.gson.reflect.TypeToken<List<com.example.moneytracker.data.remote.dto.SubscriptionDto>>() {}.type
            com.google.gson.Gson().fromJson(json, type)
        } catch (e: Exception) {
            null
        }
    }
}
