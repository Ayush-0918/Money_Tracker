package com.example.moneytracker.util

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecurePrefs(context: Context) {
    private val appContext = context.applicationContext
    private val masterKey = MasterKey.Builder(appContext)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        appContext,
        "money_tracker_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveApiKey(key: String) {
        prefs.edit().putString("api_key", key).apply()
    }

    fun getApiKey(): String? {
        return prefs.getString("api_key", null)
    }

    fun saveUserId(id: String) {
        android.util.Log.d("SecurePrefs", "Saving userId: $id")
        prefs.edit().putString("user_id", id).apply()
    }

    fun getUserId(): String? {
        val id = prefs.getString("user_id", null)
        android.util.Log.d("SecurePrefs", "Retrieved userId: $id")
        return id
    }

    fun saveDbPassword(password: String) {
        prefs.edit().putString("db_password", password).apply()
    }

    fun getDbPassword(): String? {
        return prefs.getString("db_password", null)
    }

    fun saveToken(token: String) {
        prefs.edit().putString("auth_token", token).apply()
    }

    fun getToken(): String? {
        return prefs.getString("auth_token", null)
    }
}
