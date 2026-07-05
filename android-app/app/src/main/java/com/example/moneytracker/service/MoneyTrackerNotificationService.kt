package com.example.moneytracker.service

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.security.MessageDigest
import android.content.ComponentName
import android.content.pm.PackageManager
import com.example.moneytracker.di.ServiceLocator
import com.example.moneytracker.domain.repository.TransactionRepository
import java.util.ArrayDeque

class MoneyTrackerNotificationService : NotificationListenerService() {

    private lateinit var repository: TransactionRepository
    private val serviceScope = CoroutineScope(Dispatchers.IO)
    private val processedHashes = ArrayDeque<String>(50)

    override fun onCreate() {
        super.onCreate()
        repository = ServiceLocator.provideTransactionRepository(applicationContext)
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        
        val packageName = sbn.packageName
        
        // 1. Package Filter
        if (!NotificationFilter.isAllowedPackage(packageName)) return

        val extras = sbn.notification.extras
        val title = extras.getString("android.title")
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        val fullText = "$title $text"
        
        // 2. SHA256 Duplicate Check (rawText + timestamp rounded to minute)
        val currentMinute = System.currentTimeMillis() / 60000
        val hashInput = "$fullText-$currentMinute"
        val hash = sha256(hashInput)

        if (processedHashes.contains(hash)) return
        
        // Bounded queue logic: Add to end, remove from front if size > 50
        if (processedHashes.size >= 50) {
            processedHashes.removeFirst()
        }
        processedHashes.addLast(hash)

        // 3. Security Filter
        if (!NotificationFilter.isSafeToProcess(fullText)) {
            Log.d("MoneyTrackerNLS", "Blocked sensitive notification")
            return
        }

        // 4. Parse & Sync (On Background Thread)
        serviceScope.launch {
            val parsed = NotificationParser.parse(packageName, title, text)
            if (parsed != null) {
                repository.syncTransaction(parsed.rawText)
            }
        }
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }

    // Call this from MainActivity onResume to force a reconnect if OEM kills the service
    fun requestRebind() {
        val cn = ComponentName(this, MoneyTrackerNotificationService::class.java)
        requestRebind(cn)
    }
}
