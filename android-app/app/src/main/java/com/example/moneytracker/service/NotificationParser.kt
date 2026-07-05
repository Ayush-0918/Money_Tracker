package com.example.moneytracker.service

import com.example.moneytracker.domain.model.ParsedNotification

object NotificationParser {
    // Basic regex to find amount (₹ or Rs or INR)
    private val AMOUNT_REGEX = Regex("(?:Rs\\.?|₹|INR)\\s*([\\d,]+(?:\\.\\d{1,2})?)", RegexOption.IGNORE_CASE)
    
    // Fallback basic merchant extraction
    private val MERCHANT_REGEX = Regex("(?:paid to|debited to|sent to)\\s+([A-Za-z][A-Za-z0-9\\s&.-]{1,39})", RegexOption.IGNORE_CASE)

    fun parse(packageName: String, title: String?, text: String?): ParsedNotification? {
        val fullText = "${title ?: ""} ${text ?: ""}"
        
        val amountMatch = AMOUNT_REGEX.find(fullText) ?: return null
        val merchantMatch = MERCHANT_REGEX.find(fullText)

        val amountStr = amountMatch.groupValues[1].replace(",", "")
        val amount = amountStr.toDoubleOrNull() ?: return null
        
        val merchant = merchantMatch?.groupValues?.get(1)?.trim() ?: "Unknown Merchant"

        return ParsedNotification(
            amount = amount,
            merchant = merchant,
            rawText = fullText,
            source = "notification"
        )
    }
}
