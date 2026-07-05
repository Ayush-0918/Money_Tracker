package com.example.moneytracker.data.remote.dto

import java.util.UUID

data class CategoryResponse(
    val id: UUID,
    val slug: String,
    val display_name: String,
    val icon: String?,
    val color: String?,
    val sort_order: Int,
    val system: Boolean,
    val parent_category_id: UUID?
)

data class CategoryUpdateDto(
    val category_id: UUID
)
