package com.example.moneytracker.data.remote.dto

data class TransactionRequest(
    val user_id: String,
    val raw_text: String,
    val source: String,
    val idempotency_key: String? = null
)
