package com.example.moneytracker.ui.analytics

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Lightbulb
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.BudgetSummaryResponse
import com.example.moneytracker.ui.analytics.AnalyticsReportData
import com.example.moneytracker.ui.components.CardEntrance
import com.example.moneytracker.ui.components.cards.PremiumCard
import com.example.moneytracker.ui.components.charts.CurvedLineChart
import com.example.moneytracker.ui.theme.*

@Composable
fun AnalyticsScreen(
    viewModel: AnalyticsViewModel
) {
    val uiState by viewModel.uiState.collectAsState()

    Box(modifier = Modifier.fillMaxSize().background(FintechSurface)) {
        when (val state = uiState) {
            is AnalyticsUiState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = FintechBlue)
                }
            }
            is AnalyticsUiState.Error -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(state.message, color = FintechRed)
                }
            }
            is AnalyticsUiState.Success -> {
                AnalyticsContent(data = state.data)
            }
        }
    }
}

@Composable
fun AnalyticsContent(data: AnalyticsReportData) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(top = 16.dp, start = 20.dp, end = 20.dp, bottom = 120.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        item {
            CardEntrance {
                TotalSavingsHero(data)
            }
        }

        item {
            CardEntrance(delay = 100) {
                AICoachSection(data.aiInsights)
            }
        }

        item {
            CardEntrance(delay = 200) {
                SpendingTrendsSection(data)
            }
        }

        item {
            CardEntrance(delay = 300) {
                BudgetCarouselSection(data.budgets)
            }
        }

        item {
            CardEntrance(delay = 400) {
                SavingTipsSection(data.savingTips)
            }
        }

        item {
            CardEntrance(delay = 500) {
                CategoryBreakdownDetailed(data)
            }
        }
    }
}

@Composable
fun TotalSavingsHero(data: AnalyticsReportData) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(32.dp))
            .background(
                Brush.verticalGradient(
                    colors = listOf(FintechBlue, FintechPurple)
                )
            )
            .padding(28.dp)
    ) {
        Column {
            Text("Savings Score", color = Color.White.copy(alpha = 0.7f), style = MaterialTheme.typography.labelMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Text("85", color = Color.White, style = MaterialTheme.typography.displayMedium.copy(fontWeight = FontWeight.Bold))
                Spacer(modifier = Modifier.width(8.dp))
                Text("/ 100", color = Color.White.copy(alpha = 0.7f), modifier = Modifier.padding(bottom = 12.dp))
            }
            Spacer(modifier = Modifier.height(24.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column {
                    Text("Total Assets", color = Color.White.copy(alpha = 0.7f), style = MaterialTheme.typography.labelSmall)
                    Text(data.totalBalance, color = Color.White, style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold))
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Monthly Savings", color = Color.White.copy(alpha = 0.7f), style = MaterialTheme.typography.labelSmall)
                    Text(data.monthlySavings, color = FintechGreen, style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold))
                }
            }
        }
    }
}

@Composable
fun AICoachSection(insights: String?) {
    PremiumCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(FintechBlue.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.AutoAwesome, 
                        contentDescription = null, 
                        modifier = Modifier.size(16.dp), 
                        tint = FintechBlue
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Text("AI Financial Coach", style = MaterialTheme.typography.titleMedium, color = Color.White)
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = insights ?: "Analyzing your spending patterns to provide personalized advice...",
                style = MaterialTheme.typography.bodyMedium,
                lineHeight = 22.sp,
                color = FintechSecondary
            )
        }
    }
}

@Composable
fun SpendingTrendsSection(data: AnalyticsReportData) {
    PremiumCard {
        Column {
            Text("Spending Trends", style = MaterialTheme.typography.titleMedium, color = Color.White)
            Spacer(modifier = Modifier.height(24.dp))
            CurvedLineChart(
                points = data.weeklyPoints,
                modifier = Modifier.height(180.dp).fillMaxWidth()
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TrendItem("Average", "₹${data.weeklyAverage.toInt()}")
                TrendItem("Forecast", "₹${(data.weeklyAverage * 30).toInt()}")
            }
        }
    }
}

@Composable
fun TrendItem(label: String, value: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
        Text(value, style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold), color = Color.White)
    }
}

@Composable
fun SavingTipsSection(tips: String?) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Lightbulb, contentDescription = null, tint = FintechOrange, modifier = Modifier.size(20.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Smart Saving Tips", style = MaterialTheme.typography.titleMedium, color = Color.White)
        }
        Spacer(modifier = Modifier.height(16.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(24.dp))
                .background(FintechSurfaceVariant)
                .padding(20.dp)
        ) {
            Text(
                text = tips ?: "You could save ₹2,400 by switching your mobile plan to a yearly subscription.",
                style = MaterialTheme.typography.bodyMedium,
                color = FintechSecondary
            )
        }
    }
}

@Composable
fun CategoryBreakdownDetailed(data: AnalyticsReportData) {
    Column {
        Text("Category Breakdown", style = MaterialTheme.typography.titleMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        PremiumCard {
            Column(verticalArrangement = Arrangement.spacedBy(20.dp)) {
                data.categories.entries.sortedByDescending { it.value }.forEach { entry ->
                    CategoryProgressRow(
                        name = entry.key,
                        amount = "${String.format("%.1f", entry.value)}%",
                        percentage = entry.value / 100f
                    )
                }
            }
        }
    }
}

@Composable
fun BudgetCarouselSection(budgets: List<BudgetSummaryResponse>) {
    Column {
        Text("Active Budgets", style = MaterialTheme.typography.titleMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        if (budgets.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(FintechSurfaceVariant),
                contentAlignment = Alignment.Center
            ) {
                Text("No budgets set yet", color = FintechSecondary)
            }
        } else {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(end = 20.dp)
            ) {
                items(budgets) { budget ->
                    AnalyticsBudgetCard(budget)
                }
            }
        }
    }
}

@Composable
fun AnalyticsBudgetCard(budget: BudgetSummaryResponse) {
    Box(
        modifier = Modifier
            .width(220.dp)
            .clip(RoundedCornerShape(28.dp))
            .background(FintechSurfaceVariant)
            .padding(20.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = budget.status.replaceFirstChar { it.uppercase() },
                    style = MaterialTheme.typography.labelSmall,
                    color = when (budget.status) {
                        "safe" -> FintechGreen
                        "warning" -> FintechOrange
                        else -> FintechRed
                    }
                )
                Text(
                    "${(budget.percentage_used ?: 0.0).toInt()}%",
                    style = MaterialTheme.typography.labelLarge.copy(fontWeight = FontWeight.Bold),
                    color = Color.White
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                "Monthly Budget",
                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                color = Color.White
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "₹${budget.remaining.toInt()} left",
                style = MaterialTheme.typography.labelSmall,
                color = FintechSecondary
            )
            Spacer(modifier = Modifier.height(16.dp))
            LinearProgressIndicator(
                progress = { ((budget.percentage_used ?: 0.0) / 100.0).coerceIn(0.0, 1.0).toFloat() },
                modifier = Modifier.fillMaxWidth().height(4.dp).clip(CircleShape),
                color = when (budget.status) {
                    "safe" -> FintechBlue
                    "warning" -> FintechOrange
                    else -> FintechRed
                },
                trackColor = FintechSurfaceBright
            )
        }
    }
}

@Composable
fun CategoryProgressRow(name: String, amount: String, percentage: Float) {
    Column {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(name, style = MaterialTheme.typography.bodyMedium, color = Color.White)
            Text(amount, style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold), color = Color.White)
        }
        Spacer(modifier = Modifier.height(8.dp))
        LinearProgressIndicator(
            progress = { percentage },
            modifier = Modifier.fillMaxWidth().height(6.dp).clip(CircleShape),
            color = FintechBlue,
            trackColor = FintechSurfaceBright
        )
    }
}
