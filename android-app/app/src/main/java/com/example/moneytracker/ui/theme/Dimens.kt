package com.example.moneytracker.ui.theme

import androidx.compose.runtime.Composable
import androidx.compose.runtime.ReadOnlyComposable

object AppTheme {
    val spacing: AppSpacing
        @Composable
        @ReadOnlyComposable
        get() = LocalSpacing.current

    val elevation: AppElevation
        @Composable
        @ReadOnlyComposable
        get() = LocalElevation.current
}
