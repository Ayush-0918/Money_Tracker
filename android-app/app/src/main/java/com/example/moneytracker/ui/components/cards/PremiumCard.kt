package com.example.moneytracker.ui.components.cards

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.example.moneytracker.ui.theme.*

@Composable
fun PremiumCard(
    modifier: Modifier = Modifier,
    containerColor: Color = FintechSurfaceVariant,
    cornerRadius: Dp = 28.dp,
    elevation: Dp = 0.dp,
    borderWidth: Dp = 1.dp,
    borderColor: Color = CardOutline,
    padding: Dp = 24.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .shadow(elevation, RoundedCornerShape(cornerRadius), clip = false)
            .border(borderWidth, borderColor, RoundedCornerShape(cornerRadius)),
        color = containerColor,
        shape = RoundedCornerShape(cornerRadius)
    ) {
        Column(
            modifier = Modifier.padding(padding),
            content = content
        )
    }
}

@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 28.dp,
    padding: Dp = 24.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(cornerRadius))
            .background(GlassWhite)
            .border(1.dp, GlassBorder, RoundedCornerShape(cornerRadius))
            .background(
                Brush.verticalGradient(
                    listOf(Color.White.copy(alpha = 0.05f), Color.Transparent)
                )
            )
    ) {
        Column(
            modifier = Modifier.padding(padding),
            content = content
        )
    }
}

@Composable
fun GradientCard(
    gradient: List<Color>,
    modifier: Modifier = Modifier,
    cornerRadius: Dp = 28.dp,
    padding: Dp = 24.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(cornerRadius))
            .background(Brush.linearGradient(gradient))
            .border(1.dp, Color.White.copy(alpha = 0.2f), RoundedCornerShape(cornerRadius))
    ) {
        Column(
            modifier = Modifier.padding(padding),
            content = content
        )
    }
}
