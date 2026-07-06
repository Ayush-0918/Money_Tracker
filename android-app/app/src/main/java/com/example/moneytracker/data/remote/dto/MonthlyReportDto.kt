package com.example.moneytracker.data.remote.dto

data class MonthlyReportDto(
    val total_spend_formatted: String,
    val total_balance_formatted: String,
    val income_formatted: String,
    val savings_formatted: String,
    val spend_diff_text: String,
    val spend_diff_is_positive: Boolean,
    val categories: Map<String, Float>,
    val recent_transactions: List<TransactionItemDto>
)
