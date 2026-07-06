package com.example.moneytracker.data.remote.dto

import com.google.gson.annotations.SerializedName

// ── Family Wallet DTOs ────────────────────────────────────────────────────────

data class FamilyWalletCreateDto(
    @SerializedName("name") val name: String
)

data class FamilyMemberDto(
    @SerializedName("id") val id: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("email") val email: String,
    @SerializedName("role") val role: String,
    @SerializedName("joined_at") val joinedAt: String
)

data class SharedExpenseCreateDto(
    @SerializedName("amount") val amount: Double,
    @SerializedName("description") val description: String,
    @SerializedName("category_id") val categoryId: String? = null
)

data class SharedExpenseDto(
    @SerializedName("id") val id: String,
    @SerializedName("amount") val amount: Double,
    @SerializedName("amount_formatted") val amountFormatted: String,
    @SerializedName("description") val description: String,
    @SerializedName("paid_by_id") val paidById: String,
    @SerializedName("paid_by_name") val paidByName: String,
    @SerializedName("category_id") val categoryId: String?,
    @SerializedName("category_name") val categoryName: String?,
    @SerializedName("transaction_date") val transactionDate: String
)

data class FamilyWalletResponseDto(
    @SerializedName("id") val id: String,
    @SerializedName("name") val name: String,
    @SerializedName("invite_code") val inviteCode: String,
    @SerializedName("owner_id") val ownerId: String,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("members") val members: List<FamilyMemberDto>,
    @SerializedName("expenses") val expenses: List<SharedExpenseDto>,
    @SerializedName("total_spent") val totalSpent: Double,
    @SerializedName("total_spent_formatted") val totalSpentFormatted: String
)

data class FamilyLeaderboardItemDto(
    @SerializedName("name") val name: String,
    @SerializedName("rank") val rank: Int,
    @SerializedName("saved_amount") val savedAmount: Double,
    @SerializedName("saved_amount_formatted") val savedAmountFormatted: String,
    @SerializedName("avatar_emoji") val avatarEmoji: String
)

data class FamilySummaryResponseDto(
    @SerializedName("wallet_id") val walletId: String,
    @SerializedName("name") val name: String,
    @SerializedName("money_score") val moneyScore: Int,
    @SerializedName("leaderboard") val leaderboard: List<FamilyLeaderboardItemDto>,
    @SerializedName("ai_insights") val aiInsights: String
)
