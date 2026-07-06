package com.example.moneytracker.data.remote

import com.example.moneytracker.BuildConfig
import com.example.moneytracker.data.remote.api.ApiService
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    @Volatile
    private var INSTANCE: ApiService? = null

    fun getApi(authInterceptor: AuthInterceptor): ApiService {
        return INSTANCE ?: synchronized(this) {
            val instance = INSTANCE
            if (instance != null) {
                instance
            } else {
                val logging = HttpLoggingInterceptor { message ->
                    android.util.Log.d("OkHttp", message)
                }.apply {
                    level = HttpLoggingInterceptor.Level.BODY
                }

                val client = OkHttpClient.Builder()
                    .addInterceptor(authInterceptor)
                    .addInterceptor(RetryInterceptor())
                    .addInterceptor(logging)
                    .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .build()

                val api = Retrofit.Builder()
                    .baseUrl(BuildConfig.BASE_URL)
                    .client(client)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build()
                    .create(ApiService::class.java)
                
                INSTANCE = api
                api
            }
        }
    }
}
