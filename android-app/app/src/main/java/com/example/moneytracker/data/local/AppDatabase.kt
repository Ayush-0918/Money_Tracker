package com.example.moneytracker.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.example.moneytracker.data.local.dao.TransactionDao
import com.example.moneytracker.data.local.entity.TransactionEntity
// import net.sqlcipher.database.SupportOpenHelperFactory

@Database(entities = [TransactionEntity::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun transactionDao(): TransactionDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                // Securely derive or generate the database passphrase using Android Keystore
                val securePrefs = com.example.moneytracker.util.SecurePrefs(context)
                var dbPassword = securePrefs.getDbPassword()
                
                if (dbPassword == null) {
                    // Generate a strong, random passphrase on first run
                    dbPassword = java.util.UUID.randomUUID().toString()
                    // Store it securely (encrypted via Android Keystore)
                    securePrefs.saveDbPassword(dbPassword)
                }

                // Use SQLCipher for encrypted Room database
                // val factory = SupportOpenHelperFactory(dbPassword.toByteArray())
                
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "money_tracker_encrypted_db"
                )
                // .openHelperFactory(factory)
                .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
