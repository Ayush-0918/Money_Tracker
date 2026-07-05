package com.example.moneytracker.data.repository

import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.remote.dto.CategoryResponse
import com.example.moneytracker.domain.repository.CategoryRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class CategoryRepositoryImpl(
    private val apiService: ApiService
) : CategoryRepository {
    
    // In-memory cache to avoid repeated network calls for static categories
    private var cachedCategories: List<CategoryResponse>? = null

    override suspend fun getCategories(): Result<List<CategoryResponse>> = withContext(Dispatchers.IO) {
        cachedCategories?.let { return@withContext Result.success(it) }

        try {
            val response = apiService.getCategories()
            if (response.isSuccessful && response.body() != null) {
                cachedCategories = response.body()
                Result.success(cachedCategories!!)
            } else {
                Result.failure(Exception("Failed to fetch categories: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
