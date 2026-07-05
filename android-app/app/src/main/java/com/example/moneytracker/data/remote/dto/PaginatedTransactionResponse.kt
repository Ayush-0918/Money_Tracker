package com.example.moneytracker.data.remote.dto

data class PaginatedTransactionResponse(
    val items: List<TransactionItemDto>,
    val total: Int,
    val page: Int,
    val size: Int,
    val has_more: Boolean
)
