package com.example.moneytracker.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Delete
import com.example.moneytracker.data.local.entity.TransactionEntity

@Dao
interface TransactionDao {
    @Insert
    suspend fun insert(transaction: TransactionEntity)

    @Query("SELECT * FROM pending_transactions ORDER BY timestamp ASC")
    suspend fun getAllPending(): List<TransactionEntity>

    @Delete
    suspend fun delete(transaction: TransactionEntity)
}
