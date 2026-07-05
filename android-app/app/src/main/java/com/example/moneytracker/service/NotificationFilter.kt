package com.example.moneytracker.service

object NotificationFilter {
    private val SENSITIVE_KEYWORDS = listOf(
        "otp", 
        "one time password", 
        "verification code", 
        "do not share", 
        "valid for",
        "passcode"
    )

    fun isAllowedPackage(packageName: String): Boolean {
        return com.example.moneytracker.util.Constants.ALLOWED_PACKAGES.contains(packageName)
    }

    fun isSafeToProcess(text: String): Boolean {
        val lowerText = text.lowercase()
        for (keyword in SENSITIVE_KEYWORDS) {
            if (lowerText.contains(keyword)) {
                return false // Discard immediately
            }
        }
        return true
    }
}
