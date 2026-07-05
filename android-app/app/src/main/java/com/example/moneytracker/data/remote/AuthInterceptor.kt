package com.example.moneytracker.data.remote

import com.example.moneytracker.util.SecurePrefs
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(private val securePrefs: SecurePrefs) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        
        // Don't add API key for auth/register endpoint
        if (originalRequest.url.encodedPath.contains("/auth/register")) {
            return chain.proceed(originalRequest)
        }

        val token = securePrefs.getToken()
        
        val newRequest = if (token != null) {
            android.util.Log.d("AuthInterceptor", "Attaching Bearer Token: ${token.take(10)}...")
            originalRequest.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            android.util.Log.w("AuthInterceptor", "No Token found in SecurePrefs")
            originalRequest
        }
        
        return chain.proceed(newRequest)
    }
}
