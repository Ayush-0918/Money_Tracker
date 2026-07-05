package com.example.moneytracker.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.*
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.ui.components.cards.GlassCard
import com.example.moneytracker.ui.components.cards.GradientCard
import com.example.moneytracker.ui.components.cards.PremiumCard
import com.example.moneytracker.ui.theme.*

@Composable
fun BalanceCard(
    totalBalance: Float,
    monthlySpending: Float,
    onAddClick: () -> Unit,
) {
    GradientCard(gradient = PremiumGradient) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        "Total Balance",
                        style = MaterialTheme.typography.labelLarge,
                        color = Color.White.copy(alpha = 0.7f)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    AnimatedNumber(
                        value = totalBalance,
                        style = MaterialTheme.typography.displayLarge.copy(fontSize = 38.sp),
                        color = Color.White
                    )
                }
                IconButton(
                    onClick = onAddClick,
                    modifier = Modifier
                        .clip(CircleShape)
                        .background(Color.White.copy(alpha = 0.2f))
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, tint = Color.White)
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            GlassCard(
                cornerRadius = 20.dp,
                padding = 16.dp
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(Color.White.copy(alpha = 0.1f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.AutoMirrored.Filled.TrendingDown, contentDescription = null, tint = FintechRed)
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                "Monthly Spent",
                                style = MaterialTheme.typography.labelSmall,
                                color = Color.White.copy(alpha = 0.6f)
                            )
                            AnimatedNumber(
                                value = monthlySpending,
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White
                            )
                        }
                    }
                    Icon(Icons.Default.ChevronRight, contentDescription = null, tint = Color.White.copy(alpha = 0.4f))
                }
            }
        }
    }
}

@Composable
fun StatsGrid(
    income: Float,
    expenses: Float,
    savings: Float
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        StatItem(
            label = "Income",
            value = income,
            icon = Icons.Default.ArrowDownward,
            color = FintechGreen,
            modifier = Modifier.weight(1f)
        )
        StatItem(
            label = "Expenses",
            value = expenses,
            icon = Icons.Default.ArrowUpward,
            color = FintechRed,
            modifier = Modifier.weight(1f)
        )
        StatItem(
            label = "Savings",
            value = savings,
            icon = Icons.Default.Savings,
            color = FintechBlue,
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
fun StatItem(
    label: String,
    value: Float,
    icon: ImageVector,
    color: Color,
    modifier: Modifier = Modifier
) {
    PremiumCard(
        modifier = modifier,
        padding = 16.dp,
        cornerRadius = 24.dp
    ) {
        Column {
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .clip(CircleShape)
                    .background(color.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(16.dp))
            }
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                label,
                style = MaterialTheme.typography.labelSmall,
                color = FintechSecondary
            )
            AnimatedNumber(
                value = value,
                style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                color = Color.White
            )
        }
    }
}

@Composable
fun BudgetCard(
    spent: Float,
    total: Float,
    progress: Float
) {
    PremiumCard {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Monthly Budget", style = MaterialTheme.typography.titleMedium, color = Color.White)
                Text(
                    "${(progress * 100).toInt()}%",
                    style = MaterialTheme.typography.labelLarge,
                    color = if (progress > 0.9f) FintechRed else FintechGreen
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(CircleShape),
                color = if (progress > 0.9f) FintechRed else FintechBlue,
                trackColor = FintechSurfaceBright
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Spent", style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
                    AnimatedNumber(value = spent, style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Bold), color = Color.White)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Total Budget", style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
                    AnimatedNumber(value = total, style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.Bold), color = Color.White)
                }
            }
        }
    }
}

@Composable
fun AICoachCard(insight: String) {
    GradientCard(gradient = PurpleGradient) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(Color.White.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = Color.White)
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    "AI Finance Coach",
                    style = MaterialTheme.typography.labelLarge,
                    color = Color.White.copy(alpha = 0.8f)
                )
                Text(
                    insight,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color.White
                )
            }
        }
    }
}

@Composable
fun SpendingScoreCard(score: Int) {
    PremiumCard {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text("Spending Score", style = MaterialTheme.typography.titleMedium, color = Color.White)
                Text(
                    "Excellent",
                    style = MaterialTheme.typography.labelLarge,
                    color = FintechGreen
                )
            }
            Box(contentAlignment = Alignment.Center) {
                CircularProgressIndicator(
                    progress = { score / 100f },
                    modifier = Modifier.size(60.dp),
                    color = FintechGreen,
                    trackColor = FintechSurfaceBright,
                    strokeWidth = 6.dp,
                    strokeCap = StrokeCap.Round
                )
                Text(
                    score.toString(),
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                    color = Color.White
                )
            }
        }
    }
}
