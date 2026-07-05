package com.example.moneytracker.util

object Constants {
    // Packages allowed for processing
    val ALLOWED_PACKAGES = setOf(
        "com.phonepe.app",
        "net.one97.paytm",
        "com.google.android.apps.nbu.paisa.user", // Google Pay
        // SMS Packages (Fallback for bank SMS since we are using NLS exclusively for Play Store safety)
        "com.google.android.apps.messaging",
        "com.samsung.android.messaging",
        "com.android.mms"
    )
}
