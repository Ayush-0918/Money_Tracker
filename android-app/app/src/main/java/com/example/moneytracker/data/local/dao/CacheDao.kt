package com.example.moneytracker.data.local.dao

import androidx.room.*
import com.example.moneytracker.data.local.entity.CachedBudgetEntity
import com.example.moneytracker.data.local.entity.CachedTransactionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CacheDao {
    
    // Transactions Cache
    @Query("SELECT * FROM cached_transactions ORDER BY date DESC")
    fun getAllTransactions(): Flow<List<CachedTransactionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTransactions(transactions: List<CachedTransactionEntity>)

    @Query("DELETE FROM cached_transactions")
    suspend fun clearTransactions()

    // Budgets Cache
    @Query("SELECT * FROM cached_budgets")
    fun getAllBudgets(): Flow<List<CachedBudgetEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertBudgets(budgets: List<CachedBudgetEntity>)

    @Query("DELETE FROM cached_budgets")
    suspend fun clearBudgets()
}
