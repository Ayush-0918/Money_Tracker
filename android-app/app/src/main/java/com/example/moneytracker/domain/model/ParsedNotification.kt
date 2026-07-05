package com.example.moneytracker.domain.model

data class ParsedNotification(
    val amount: Double,
    val merchant: String,
    val rawText: String,
    val source: String
)
