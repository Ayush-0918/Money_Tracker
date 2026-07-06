package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.WeeklyReportResponseDto

interface WeeklyReportRepository {
    suspend fun getWeeklyReport(userId: String): Result<WeeklyReportResponseDto>
}
