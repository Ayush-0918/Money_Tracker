package com.example.moneytracker.ui.components

import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import kotlinx.coroutines.delay
import kotlin.time.Duration.Companion.milliseconds

@Composable
fun CardEntrance(
    delay: Int = 0,
    content: @Composable () -> Unit
) {
    val isPreview = androidx.compose.ui.platform.LocalInspectionMode.current
    var visible by remember { mutableStateOf(isPreview) }
    
    if (!isPreview) {
        LaunchedEffect(Unit) {
            delay(delay.milliseconds)
            visible = true
        }
    }
    
    AnimatedVisibility(
        visible = visible,
        enter = slideInVertically(initialOffsetY = { it / 2 }) + fadeIn(animationSpec = tween(600)),
        exit = fadeOut()
    ) {
        content()
    }
}
