package com.example.moneytracker.domain.repository

import com.example.moneytracker.data.remote.dto.CategoryResponse

interface CategoryRepository {
    suspend fun getCategories(): Result<List<CategoryResponse>>
}
