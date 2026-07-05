package com.example.moneytracker.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = FintechPrimary,
    onPrimary = FintechBlack,
    primaryContainer = FintechSurfaceVariant,
    onPrimaryContainer = FintechWhite,
    secondary = FintechSecondary,
    onSecondary = FintechWhite,
    background = FintechBlack,
    surface = FintechBlack,
    surfaceVariant = FintechSurfaceVariant,
    onSurface = FintechWhite,
    onSurfaceVariant = FintechSecondary,
    error = FintechRed,
    outline = FintechSecondary.copy(alpha = 0.5f)
)

private val LightColorScheme = lightColorScheme(
    primary = FintechBlack,
    onPrimary = FintechWhite,
    primaryContainer = Color(0xFFF2F2F7),
    onPrimaryContainer = FintechBlack,
    secondary = FintechSecondary,
    onSecondary = FintechBlack,
    background = FintechWhite,
    surface = FintechWhite,
    surfaceVariant = Color(0xFFF2F2F7),
    onSurface = FintechBlack,
    onSurfaceVariant = FintechSecondary,
    error = FintechRed,
    outline = FintechSecondary.copy(alpha = 0.5f)
)

@Composable
fun MoneyTrackerTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            window.navigationBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = !darkTheme
                isAppearanceLightNavigationBars = !darkTheme
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
