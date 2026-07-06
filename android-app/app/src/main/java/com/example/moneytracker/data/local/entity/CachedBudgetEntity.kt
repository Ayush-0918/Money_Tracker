package com.example.moneytracker.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_budgets")
data class CachedBudgetEntity(
    @PrimaryKey val id: String,
    val categoryId: String,
    val monthlyLimit: Double,
    val spent: Double,
    val remaining: Double,
    val percentageUsed: Float?,
    val status: String,
    val categoryName: String
)
