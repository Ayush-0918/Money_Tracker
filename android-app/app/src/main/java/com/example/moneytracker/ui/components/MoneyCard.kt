package com.example.moneytracker.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import com.example.moneytracker.ui.theme.AppTheme


@Composable
fun MoneyCard(
    title: String,
    amount: String,
    modifier: Modifier = Modifier,
    isPositive: Boolean? = null
) {

    
    val amountColor = when (isPositive) {
        true -> MaterialTheme.colorScheme.tertiary // Assuming tertiary maps to Success in Theme setup if configured, or fallback
        false -> MaterialTheme.colorScheme.onBackground
        null -> MaterialTheme.colorScheme.onBackground
    }

    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = AppTheme.elevation.small),
        shape = MaterialTheme.shapes.medium
    ) {
        Column(modifier = Modifier.padding(AppTheme.spacing.large)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
            )
            Spacer(modifier = Modifier.height(AppTheme.spacing.small))
            Text(
                text = amount,
                style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Bold),
                color = amountColor
            )
        }
    }
}
