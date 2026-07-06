package com.example.moneytracker.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_transactions")
data class CachedTransactionEntity(
    @PrimaryKey val id: String,
    val merchant: String,
    val amountFormatted: String,
    val date: String,
    val category: String?
)
