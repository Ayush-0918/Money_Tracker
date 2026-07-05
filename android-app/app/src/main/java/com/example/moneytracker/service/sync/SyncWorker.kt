package com.example.moneytracker.service.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.example.moneytracker.di.ServiceLocator
import com.example.moneytracker.data.remote.dto.TransactionRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class SyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    private val dependencies = ServiceLocator.provideSyncWorkerDependencies(context)
    private val dao = dependencies.dao
    private val api = dependencies.api
    private val securePrefs = dependencies.securePrefs

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val pending = dao.getAllPending()
        if (pending.isEmpty()) return@withContext Result.success()

        val token = securePrefs.getToken() ?: return@withContext Result.failure()

        for (transaction in pending) {
            try {
                val response = api.postTransaction(
                    TransactionRequest(transaction.userId, transaction.rawText, "notification")
                )
                if (response.isSuccessful) {
                    dao.delete(transaction)
                } else {
                    // In a real app, you might want to stop here to avoid multiple retries in one go
                    return@withContext Result.retry()
                }
            } catch (e: Exception) {
                return@withContext Result.retry()
            }
        }
        
        Result.success()
    }
}
