package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.WeeklyReportResponseDto
import com.example.moneytracker.domain.repository.WeeklyReportRepository
import com.example.moneytracker.util.SecurePrefs

class WeeklyReportRepositoryImpl(
    private val api: ApiService,
    private val securePrefs: SecurePrefs
) : WeeklyReportRepository {

    override suspend fun getWeeklyReport(userId: String): Result<WeeklyReportResponseDto> {
        return try {
            val response = api.getWeeklyFinancialReport(userId)
            if (response.isSuccessful) {
                val body = response.body()!!
                // Cache for offline-first support
                securePrefs.saveWeeklyFinancialReport(body)
                Result.success(body)
            } else {
                // Attempt to return cached data if API fails
                val cached = securePrefs.getWeeklyFinancialReport()
                if (cached != null) {
                    Result.success(cached)
                } else {
                    Result.failure(Exception("API error ${response.code()}: ${response.message()}"))
                }
            }
        } catch (e: Exception) {
            // Network failure — fall back to cache
            val cached = securePrefs.getWeeklyFinancialReport()
            if (cached != null) {
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }
}
