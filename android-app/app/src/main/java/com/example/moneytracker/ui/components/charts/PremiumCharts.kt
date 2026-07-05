package com.example.moneytracker.ui.components.charts

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.ui.theme.*

@Composable
fun PremiumDonutChart(
    data: Map<String, Float>,
    modifier: Modifier = Modifier,
    centerLabel: String = "",
) {
    val total = data.values.sum().coerceAtLeast(1f)
    val sweepAnim = remember { Animatable(0f) }

    LaunchedEffect(data) {
        sweepAnim.animateTo(1f, animationSpec = tween(1500, easing = CubicBezierEasing(0.2f, 0.8f, 0.2f, 1f)))
    }

    val colors = listOf(FintechBlue, FintechPurple, FintechGreen, FintechOrange, FintechRed, FintechIndigo, FintechPink, FintechTeal)

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val strokeWidth = 16.dp.toPx()
            val diameter = size.minDimension - strokeWidth
            val topLeft = Offset((size.width - diameter) / 2, (size.height - diameter) / 2)
            val arcSize = Size(diameter, diameter)
            
            var startAngle = -90f

            data.entries.forEachIndexed { index, entry ->
                val sweepAngle = (entry.value / total) * 360f * sweepAnim.value
                val color = colors[index % colors.size]

                drawArc(
                    color = color,
                    startAngle = startAngle,
                    sweepAngle = sweepAngle,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
                startAngle += sweepAngle
            }
        }
        if (centerLabel.isNotEmpty()) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = centerLabel,
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp
                    ),
                    color = Color.White
                )
                Text(
                    text = "Total",
                    style = MaterialTheme.typography.labelSmall,
                    color = FintechSecondary
                )
            }
        }
    }
}

@Composable
fun CurvedLineChart(
    points: List<Float>,
    modifier: Modifier = Modifier,
    lineColor: Color = FintechBlue,
    fillColor: Color = FintechBlue.copy(alpha = 0.1f)
) {
    val animationProgress = remember { Animatable(0f) }
    LaunchedEffect(points) {
        animationProgress.animateTo(1f, animationSpec = tween(2000, easing = CubicBezierEasing(0.2f, 0.8f, 0.2f, 1f)))
    }

    Canvas(modifier = modifier) {
        if (points.size < 2) return@Canvas
        
        val maxPoint = points.maxOrNull()?.coerceAtLeast(1f) ?: 1f
        val minPoint = points.minOrNull() ?: 0f
        val range = (maxPoint - minPoint).coerceAtLeast(1f)
        
        val stepX = size.width / (points.size - 1)
        
        val path = Path()
        val fillPath = Path()
        
        points.forEachIndexed { index, point ->
            val x = index * stepX
            val y = size.height - ((point - minPoint) / range) * size.height * animationProgress.value
            
            if (index == 0) {
                path.moveTo(x, y)
                fillPath.moveTo(x, size.height)
                fillPath.lineTo(x, y)
            } else {
                val prevX = (index - 1) * stepX
                val prevY = size.height - ((points[index - 1] - minPoint) / range) * size.height * animationProgress.value
                
                // Bézier curve
                val controlX1 = prevX + (x - prevX) / 2
                val controlX2 = prevX + (x - prevX) / 2
                
                path.cubicTo(controlX1, prevY, controlX2, y, x, y)
                fillPath.cubicTo(controlX1, prevY, controlX2, y, x, y)
            }
            
            if (index == points.size - 1) {
                fillPath.lineTo(x, size.height)
                fillPath.close()
            }
        }

        drawPath(
            path = fillPath,
            brush = Brush.verticalGradient(
                colors = listOf(fillColor, Color.Transparent)
            )
        )
        
        drawPath(
            path = path,
            color = lineColor,
            style = Stroke(width = 4.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round)
        )
    }
}

@Composable
fun WeeklyMiniGraph(
    points: List<Float>,
    modifier: Modifier = Modifier,
    color: Color = FintechBlue
) {
    CurvedLineChart(points = points, modifier = modifier, lineColor = color)
}
