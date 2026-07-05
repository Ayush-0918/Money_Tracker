package com.example.moneytracker.ui.theme

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearOutSlowInEasing
import androidx.compose.animation.core.tween

object AppAnimation {
    val durationShort = 200
    val durationMedium = 300
    val durationLong = 500

    val standardEasing = FastOutSlowInEasing
    val enterEasing = LinearOutSlowInEasing

    fun <T> standardTween() = tween<T>(durationMillis = durationMedium, easing = standardEasing)
    fun <T> enterTween() = tween<T>(durationMillis = durationMedium, easing = enterEasing)
}
