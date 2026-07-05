package com.example.moneytracker.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

@Composable
fun CategoryDonutChart(
    categories: Map<String, Float>,
    modifier: Modifier = Modifier
) {
    val total = categories.values.sum().coerceAtLeast(1f)
    val sweepAnim = remember { Animatable(0f) }

    LaunchedEffect(categories) {
        sweepAnim.animateTo(1f, animationSpec = tween(1000))
    }

    // Pastel palette for categories
    val colors = listOf(
        Color(0xFF90CAF9), // Pastel Blue
        Color(0xFFA5D6A7), // Pastel Green
        Color(0xFFFFCC80), // Pastel Orange
        Color(0xFFF48FB1), // Pastel Pink
        Color(0xFFCE93D8)  // Pastel Purple
    )

    Canvas(modifier = modifier.size(200.dp)) {
        val strokeWidth = 32.dp.toPx()
        val diameter = size.minDimension - strokeWidth
        val topLeft = Offset(strokeWidth / 2, strokeWidth / 2)
        val arcSize = Size(diameter, diameter)

        var startAngle = -90f

        categories.entries.forEachIndexed { index, entry ->
            val sweepAngle = (entry.value / total) * 360f * sweepAnim.value
            val color = colors[index % colors.size]

            drawArc(
                color = color,
                startAngle = startAngle,
                sweepAngle = sweepAngle,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Butt)
            )
            startAngle += sweepAngle
        }
    }
}
