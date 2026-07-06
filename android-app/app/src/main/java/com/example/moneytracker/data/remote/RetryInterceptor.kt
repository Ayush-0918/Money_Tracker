package com.example.moneytracker.data.remote

import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException

class RetryInterceptor(
    private val maxRetries: Int = 3,
    private val initialDelayMs: Long = 1000,
    private val multiplier: Double = 2.0
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        var response: Response? = null
        var attempt = 0
        var delay = initialDelayMs

        while (attempt < maxRetries) {
            try {
                response = chain.proceed(request)
                if (response.isSuccessful) {
                    return response
                }
                // Don't retry client-side 4xx errors except 408 (timeout) and 429 (rate limit)
                if (response.code in 400..499 && response.code != 408 && response.code != 429) {
                    return response
                }
            } catch (e: Exception) {
                if (attempt == maxRetries - 1) {
                    throw e
                }
            }

            attempt++
            if (attempt < maxRetries) {
                android.util.Log.w("RetryInterceptor", "Request failed (code=${response?.code}). Retrying attempt $attempt after $delay ms...")
                try {
                    Thread.sleep(delay)
                } catch (ie: InterruptedException) {
                    Thread.currentThread().interrupt()
                    throw IOException("Retry interrupted", ie)
                }
                delay = (delay * multiplier).toLong()
            }
        }
        return response ?: throw IOException("Request failed after $maxRetries attempts")
    }
}
