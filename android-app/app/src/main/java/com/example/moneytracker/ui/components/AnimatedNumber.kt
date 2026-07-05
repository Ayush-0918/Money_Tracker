package com.example.moneytracker.ui.components

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import java.text.NumberFormat
import java.util.*

@Composable
fun AnimatedNumber(
    value: Float,
    modifier: Modifier = Modifier,
    style: TextStyle,
    color: Color = Color.Unspecified,
    prefix: String = "₹",
    suffix: String = ""
) {
    val animatedValue by animateFloatAsState(
        targetValue = value,
        animationSpec = tween(1000, easing = FastOutSlowInEasing),
        label = "NumberAnimation"
    )

    val formatter = remember { NumberFormat.getNumberInstance(Locale("en", "IN")) }

    Text(
        text = "$prefix${formatter.format(animatedValue.toInt())}$suffix",
        style = style,
        color = color,
        modifier = modifier
    )
}
