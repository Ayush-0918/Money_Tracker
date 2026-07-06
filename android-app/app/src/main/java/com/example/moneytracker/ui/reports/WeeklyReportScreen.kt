package com.example.moneytracker.ui.reports

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.TrendingDown
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.BudgetHealthItemDto
import com.example.moneytracker.data.remote.dto.MerchantSpendItemDto
import com.example.moneytracker.data.remote.dto.WeeklyReportResponseDto
import kotlin.math.max

// ── Color palette ─────────────────────────────────────────────────────────────
private val BackgroundDark = Color(0xFF0D1117)
private val SurfaceDark = Color(0xFF161B22)
private val CardDark = Color(0xFF1C2230)
private val AccentGreen = Color(0xFF4CAF7D)
private val AccentBlue = Color(0xFF90CAF9)
private val AccentOrange = Color(0xFFF5A623)
private val AccentRed = Color(0xFFEF5350)
private val AccentPurple = Color(0xFFCE93D8)
private val TextPrimary = Color(0xFFE6EDF3)
private val TextSecondary = Color(0xFF8B949E)
private val GlassWhite = Color(0x14FFFFFF)
private val GlassBorder = Color(0x1FFFFFFF)

@Composable
fun WeeklyReportScreen(
    viewModel: WeeklyReportViewModel,
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundDark)
    ) {
        when (val state = uiState) {
            is WeeklyReportUiState.Loading -> WeeklyReportLoadingState()
            is WeeklyReportUiState.Error -> WeeklyReportErrorState(
                message = state.message,
                onRetry = { viewModel.loadReport() },
                onBack = onBack
            )
            is WeeklyReportUiState.Success -> WeeklyReportContent(
                report = state.report,
                onBack = onBack,
                onRefresh = { viewModel.loadReport() }
            )
        }
    }
}

// ── Loading State ─────────────────────────────────────────────────────────────

@Composable
private fun WeeklyReportLoadingState() {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.4f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(900, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            CircularProgressIndicator(color = AccentGreen.copy(alpha = alpha), strokeWidth = 3.dp)
            Text("Generating AI Report…", color = TextSecondary, fontSize = 14.sp)
        }
    }
}

// ── Error State ───────────────────────────────────────────────────────────────

@Composable
private fun WeeklyReportErrorState(message: String, onRetry: () -> Unit, onBack: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(Icons.Default.Warning, contentDescription = null, tint = AccentOrange, modifier = Modifier.size(56.dp))
        Spacer(modifier = Modifier.height(16.dp))
        Text("Something went wrong", color = TextPrimary, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        Spacer(modifier = Modifier.height(8.dp))
        Text(message, color = TextSecondary, fontSize = 13.sp, textAlign = TextAlign.Center)
        Spacer(modifier = Modifier.height(24.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(
                onClick = onBack,
                colors = ButtonDefaults.outlinedButtonColors(contentColor = TextSecondary),
                border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorder)
            ) { Text("Go Back") }
            Button(onClick = onRetry, colors = ButtonDefaults.buttonColors(containerColor = AccentGreen)) {
                Text("Retry", color = Color.White)
            }
        }
    }
}

// ── Main Content ──────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun WeeklyReportContent(
    report: WeeklyReportResponseDto,
    onBack: () -> Unit,
    onRefresh: () -> Unit
) {
    var visible by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { visible = true }

    Scaffold(
        containerColor = BackgroundDark,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Weekly Report", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text(report.weekLabel, color = TextSecondary, fontSize = 12.sp)
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TextPrimary)
                    }
                },
                actions = {
                    IconButton(onClick = onRefresh) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh", tint = AccentGreen)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = SurfaceDark)
            )
        }
    ) { padding ->
        AnimatedVisibility(
            visible = visible,
            enter = fadeIn(tween(400)) + slideInVertically(tween(400)) { it / 4 }
        ) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(vertical = 16.dp)
            ) {
                // 1. Health Score Ring + Spend Summary
                item { HealthScoreCard(report) }

                // 2. AI Narrative
                item { AiNarrativeCard(report.aiNarrative, report.aiTips) }

                // 3. Spend vs Prior Week
                item { SpendComparisonCard(report) }

                // 4. Category Breakdown
                if (report.topCategories.isNotEmpty()) {
                    item { CategoryBreakdownCard(report) }
                }

                // 5. Daily Activity Chart
                item { DailyActivityCard(report) }

                // 6. Top Merchants
                if (report.topMerchants.isNotEmpty()) {
                    item { TopMerchantsCard(report.topMerchants) }
                }

                // 7. Budget Health
                if (report.budgetHealth.isNotEmpty()) {
                    item { BudgetHealthCard(report.budgetHealth, report.exceededBudgetCount) }
                }

                // 8. Upcoming Subscriptions
                if (report.upcomingSubscriptions.isNotEmpty()) {
                    item { UpcomingSubscriptionsCard(report) }
                }

                item { Spacer(modifier = Modifier.height(32.dp)) }
            }
        }
    }
}

// ── Card: Health Score + Summary ──────────────────────────────────────────────

@Composable
private fun HealthScoreCard(report: WeeklyReportResponseDto) {
    val scoreColor = try {
        Color(android.graphics.Color.parseColor(report.healthScoreColor))
    } catch (e: Exception) {
        AccentGreen
    }

    val animatedScore by animateIntAsState(
        targetValue = report.financialHealthScore,
        animationSpec = tween(1200, easing = FastOutSlowInEasing),
        label = "healthScore"
    )

    GlassCard {
        Row(
            modifier = Modifier.fillMaxWidth().padding(20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Left: spend info
            Column(modifier = Modifier.weight(1f)) {
                Text("This Week", color = TextSecondary, fontSize = 12.sp)
                Text(report.totalSpendFormatted, color = TextPrimary, fontSize = 26.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))

                val changeColor = if (report.spendChangeIsIncrease) AccentRed else AccentGreen
                val changeIcon = if (report.spendChangeIsIncrease) Icons.Default.TrendingUp else Icons.Default.TrendingDown
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Icon(changeIcon, contentDescription = null, tint = changeColor, modifier = Modifier.size(16.dp))
                    Text(report.spendChangeText, color = changeColor, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text("Avg/day: ${report.averagePerDayFormatted}", color = TextSecondary, fontSize = 12.sp)
            }

            // Right: animated ring
            Box(contentAlignment = Alignment.Center, modifier = Modifier.size(90.dp)) {
                Canvas(modifier = Modifier.size(90.dp)) {
                    val strokeWidth = 8.dp.toPx()
                    val radius = (size.minDimension - strokeWidth) / 2
                    // Background track
                    drawArc(
                        color = GlassWhite,
                        startAngle = -90f,
                        sweepAngle = 360f,
                        useCenter = false,
                        style = Stroke(strokeWidth, cap = StrokeCap.Round),
                        topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
                        size = Size(size.width - strokeWidth, size.height - strokeWidth)
                    )
                    // Score arc
                    drawArc(
                        color = scoreColor,
                        startAngle = -90f,
                        sweepAngle = (animatedScore / 100f) * 360f,
                        useCenter = false,
                        style = Stroke(strokeWidth, cap = StrokeCap.Round),
                        topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
                        size = Size(size.width - strokeWidth, size.height - strokeWidth)
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("$animatedScore", color = scoreColor, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                    Text(report.healthScoreLabel, color = TextSecondary, fontSize = 9.sp)
                }
            }
        }
    }
}

// ── Card: AI Narrative ────────────────────────────────────────────────────────

@Composable
private fun AiNarrativeCard(narrative: String, tips: List<String>) {
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(AccentPurple.copy(alpha = 0.2f)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("✨", fontSize = 16.sp)
                }
                Text("AI Insight", color = AccentPurple, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            }
            Text(narrative, color = TextPrimary, fontSize = 14.sp, lineHeight = 22.sp)
            if (tips.isNotEmpty()) {
                Divider(color = GlassBorder, thickness = 1.dp)
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    tips.forEach { tip ->
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Text("→", color = AccentGreen, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                            Text(tip, color = TextSecondary, fontSize = 13.sp, lineHeight = 19.sp)
                        }
                    }
                }
            }
        }
    }
}

// ── Card: Spend Comparison ────────────────────────────────────────────────────

@Composable
private fun SpendComparisonCard(report: WeeklyReportResponseDto) {
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Spend Comparison", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                SpendPill(label = "This Week", value = report.totalSpendFormatted, color = AccentBlue)
                SpendPill(label = "Last Week", value = report.priorWeekSpendFormatted, color = TextSecondary)
            }
        }
    }
}

@Composable
private fun SpendPill(label: String, value: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, color = TextSecondary, fontSize = 11.sp)
        Text(value, color = color, fontSize = 16.sp, fontWeight = FontWeight.Bold)
    }
}

// ── Card: Category Breakdown ──────────────────────────────────────────────────

private val categoryColors = listOf(AccentGreen, AccentBlue, AccentOrange, AccentPurple, AccentRed, Color(0xFF80DEEA))

@Composable
private fun CategoryBreakdownCard(report: WeeklyReportResponseDto) {
    val total = report.topCategories.values.sum().takeIf { it > 0 } ?: 1.0
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Top Categories", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            report.topCategories.entries.forEachIndexed { idx, (name, amount) ->
                val pct = (amount / total).toFloat().coerceIn(0f, 1f)
                val color = categoryColors.getOrElse(idx) { AccentBlue }
                val formatted = report.topCategoriesFormatted[name] ?: "₹ ${amount.toLong()}"
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(name, color = TextPrimary, fontSize = 13.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.weight(1f))
                        Text(formatted, color = color, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    }
                    val animPct by animateFloatAsState(
                        targetValue = pct, animationSpec = tween(800, easing = FastOutSlowInEasing), label = "pct_$idx"
                    )
                    LinearProgressIndicator(
                        progress = animPct,
                        modifier = Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(3.dp)),
                        color = color,
                        trackColor = GlassWhite
                    )
                }
            }
        }
    }
}

// ── Card: Daily Activity Bar Chart ────────────────────────────────────────────

@Composable
private fun DailyActivityCard(report: WeeklyReportResponseDto) {
    val maxVal = report.dailyPoints.maxOrNull()?.takeIf { it > 0 } ?: 1.0

    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Daily Activity", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            Row(
                modifier = Modifier.fillMaxWidth().height(80.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.Bottom
            ) {
                report.dailyPoints.forEachIndexed { i, value ->
                    val fraction = (value / maxVal).toFloat().coerceIn(0f, 1f)
                    val animFraction by animateFloatAsState(
                        targetValue = fraction,
                        animationSpec = tween(700, delayMillis = i * 60, easing = FastOutSlowInEasing),
                        label = "bar_$i"
                    )
                    val barColor = if (value == report.dailyPoints.maxOrNull()) AccentGreen else AccentBlue.copy(alpha = 0.6f)
                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Bottom) {
                        Box(
                            modifier = Modifier
                                .width(24.dp)
                                .fillMaxHeight(animFraction.coerceAtLeast(0.04f))
                                .clip(RoundedCornerShape(topStart = 4.dp, topEnd = 4.dp))
                                .background(barColor)
                        )
                    }
                }
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                report.dailyLabels.forEach { label ->
                    Text(label, color = TextSecondary, fontSize = 10.sp, textAlign = TextAlign.Center,
                        modifier = Modifier.width(24.dp))
                }
            }
        }
    }
}

// ── Card: Top Merchants ───────────────────────────────────────────────────────

@Composable
private fun TopMerchantsCard(merchants: List<MerchantSpendItemDto>) {
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Top Merchants", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            merchants.forEach { m ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier.size(28.dp).clip(CircleShape)
                                .background(categoryColors.getOrElse(m.rank - 1) { AccentBlue }.copy(alpha = 0.2f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Text("#${m.rank}", color = categoryColors.getOrElse(m.rank - 1) { AccentBlue },
                                fontSize = 10.sp, fontWeight = FontWeight.Bold)
                        }
                        Text(m.merchant, color = TextPrimary, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.weight(1f))
                    }
                    Text(m.amountFormatted, color = AccentOrange, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

// ── Card: Budget Health ───────────────────────────────────────────────────────

@Composable
private fun BudgetHealthCard(items: List<BudgetHealthItemDto>, exceededCount: Int) {
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically) {
                Text("Budget Health", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                if (exceededCount > 0) {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = AccentRed.copy(alpha = 0.15f)
                    ) {
                        Text("$exceededCount Exceeded", color = AccentRed, fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp))
                    }
                }
            }
            items.forEach { b ->
                val pct = (b.percentUsed / 100f).toFloat().coerceIn(0f, 1f)
                val barColor = when {
                    b.isExceeded -> AccentRed
                    pct > 0.75f -> AccentOrange
                    else -> AccentGreen
                }
                val animPct by animateFloatAsState(
                    targetValue = pct, animationSpec = tween(800, easing = FastOutSlowInEasing), label = "budget_${b.category}"
                )
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(b.category, color = TextPrimary, fontSize = 13.sp, modifier = Modifier.weight(1f),
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("${b.spentFormatted} / ${b.limitFormatted}", color = barColor, fontSize = 12.sp)
                    }
                    LinearProgressIndicator(
                        progress = animPct,
                        modifier = Modifier.fillMaxWidth().height(6.dp).clip(RoundedCornerShape(3.dp)),
                        color = barColor,
                        trackColor = GlassWhite
                    )
                    Text("${b.percentUsed.toInt()}% used this week", color = TextSecondary, fontSize = 11.sp)
                }
            }
        }
    }
}

// ── Card: Upcoming Subscriptions ──────────────────────────────────────────────

@Composable
private fun UpcomingSubscriptionsCard(report: WeeklyReportResponseDto) {
    GlassCard {
        Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Due This Week", color = TextSecondary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
            report.upcomingSubscriptions.forEach { sub ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(sub.merchant, color = TextPrimary, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text(sub.nextBillingDate, color = TextSecondary, fontSize = 12.sp)
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text(sub.amountFormatted, color = AccentOrange, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                        val daysColor = if (sub.countdownDays <= 2) AccentRed else TextSecondary
                        Text("in ${sub.countdownDays}d", color = daysColor, fontSize = 11.sp)
                    }
                }
            }
        }
    }
}

// ── Glassmorphism Card Container ──────────────────────────────────────────────

@Composable
private fun GlassCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, GlassBorder, RoundedCornerShape(16.dp)),
        shape = RoundedCornerShape(16.dp),
        color = GlassWhite,
        tonalElevation = 0.dp,
        shadowElevation = 0.dp
    ) {
        content()
    }
}
