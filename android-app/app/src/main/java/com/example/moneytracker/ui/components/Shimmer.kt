package com.example.moneytracker.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun ShimmerEffect(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "shimmer_transition")
    
    val translateAnim by transition.animateFloat(
        initialValue = -1000f,
        targetValue = 1000f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = 1000,
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Restart
        ),
        label = "shimmer_translate"
    )

    val color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.05f)
    val highlightColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.15f)

    val brush = Brush.linearGradient(
        colors = listOf(color, highlightColor, color),
        start = Offset(translateAnim - 200f, translateAnim - 200f),
        end = Offset(translateAnim + 200f, translateAnim + 200f)
    )

    Box(
        modifier = modifier.background(brush, shape = MaterialTheme.shapes.small)
    )
}

@Composable
fun ShimmerCard() {
    ShimmerEffect(
        modifier = Modifier
            .fillMaxWidth()
            .height(80.dp)
    )
}
