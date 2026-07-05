package com.example.moneytracker.service

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NotificationFilterTest {

    @Test
    fun testOtpKeyword_Lowercase() {
        val text = "your otp is 123456"
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testOtpKeyword_Uppercase() {
        val text = "Your OTP is 123456"
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testOtpKeyword_MixedCase() {
        val text = "Your oTp is 123456"
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testOneTimePassword() {
        val text = "Your One Time Password is 123456"
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testVerificationCode() {
        val text = "Use verification code 5555"
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testDoNotShare() {
        val text = "Rs.500 paid. Do not share this PIN."
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testValidFor() {
        val text = "Your login code is 1234. Valid for 5 minutes."
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testOtpMixedWithLegitInfo() {
        // Even if it looks like a legit transaction, if OTP keyword is there, drop it!
        val text = "Rs.500 debited from HDFC. Enter OTP 1234 to confirm."
        assertFalse(NotificationFilter.isSafeToProcess(text))
    }

    @Test
    fun testSafePaymentMessage() {
        val text = "Rs.500 debited to Netflix via UPI."
        assertTrue(NotificationFilter.isSafeToProcess(text))
    }
}
