package com.example.moneytracker.ui.reports

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
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
import com.example.moneytracker.data.remote.dto.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.random.Random

// ── Aesthetics & Palette ──────────────────────────────────────────────────────
private val BG_DARK = Color(0xFF0B0F17)
private val SURFACE_DARK = Color(0xFF131924)
private val GLASS_WHITE = Color(0x12FFFFFF)
private val GLASS_BORDER = Color(0x1EFFFFFF)
private val ACCENT_GREEN = Color(0xFF4CAF7D)
private val ACCENT_BLUE = Color(0xFF90CAF9)
private val ACCENT_ORANGE = Color(0xFFF5A623)
private val ACCENT_RED = Color(0xFFEF5350)
private val ACCENT_PURPLE = Color(0xFFCE93D8)
private val TEXT_PRIMARY = Color(0xFFF1F5F9)
private val TEXT_SECONDARY = Color(0xFF94A3B8)

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun MoneyStoryScreen(
    viewModel: MoneyStoryViewModel,
    onBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(BG_DARK)
    ) {
        when (val state = uiState) {
            is MoneyStoryUiState.Loading -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        CircularProgressIndicator(color = ACCENT_GREEN, strokeWidth = 3.dp)
                        Text("Decoding your financial week...", color = TEXT_SECONDARY, fontSize = 14.sp)
                    }
                }
            }
            is MoneyStoryUiState.Error -> {
                Column(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(Icons.Default.Warning, contentDescription = null, tint = ACCENT_ORANGE, modifier = Modifier.size(56.dp))
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Oops! Try again", color = TEXT_PRIMARY, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(state.message, color = TEXT_SECONDARY, fontSize = 13.sp, textAlign = TextAlign.Center)
                    Spacer(modifier = Modifier.height(24.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        OutlinedButton(onClick = onBack, colors = ButtonDefaults.outlinedButtonColors(contentColor = TEXT_SECONDARY)) {
                            Text("Go Back")
                        }
                        Button(onClick = { viewModel.loadStory() }, colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)) {
                            Text("Retry", color = Color.White)
                        }
                    }
                }
            }
            is MoneyStoryUiState.Success -> {
                MoneyStoryContent(
                    story = state.story,
                    onBack = onBack,
                    onRefresh = { viewModel.refreshStory() }
                )
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun MoneyStoryContent(
    story: MoneyStoryResponseDto,
    onBack: () -> Unit,
    onRefresh: () -> Unit
) {
    val pagerState = rememberPagerState(pageCount = { 7 })
    val coroutineScope = rememberCoroutineScope()

    Box(modifier = Modifier.fillMaxSize()) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Story Progress Indicator Top Bar
            StoryIndicatorBar(
                pageCount = 7,
                currentPage = pagerState.currentPage,
                onProgressComplete = {
                    if (pagerState.currentPage < 6) {
                        coroutineScope.launch { pagerState.animateScrollToPage(pagerState.currentPage + 1) }
                    }
                }
            )

            // Header Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onBack) {
                    Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TEXT_PRIMARY)
                }
                Text(
                    text = "Weekly Money Story",
                    color = TEXT_PRIMARY,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, contentDescription = "Refresh", tint = ACCENT_GREEN)
                }
            }

            HorizontalPager(
                state = pagerState,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
            ) { pageIndex ->
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 20.dp, vertical = 8.dp)
                ) {
                    when (pageIndex) {
                        0 -> StoryPageScore(story.pageScore)
                        1 -> StoryPageSpending(story.pageSpending)
                        2 -> StoryPageSavings(story.pageSavings)
                        3 -> StoryPageAchievements(story.pageAchievements)
                        4 -> StoryPageMistakes(story.pageMistakes)
                        5 -> StoryPageForecast(story.pageForecast)
                        6 -> StoryPageAction(story.pageAction)
                    }
                }
            }

            // Bottom Navigation Arrows
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                TextButton(
                    onClick = {
                        if (pagerState.currentPage > 0) {
                            coroutineScope.launch { pagerState.animateScrollToPage(pagerState.currentPage - 1) }
                        }
                    },
                    enabled = pagerState.currentPage > 0
                ) {
                    Text(
                        text = "PREVIOUS",
                        color = if (pagerState.currentPage > 0) ACCENT_BLUE else Color.Transparent
                    )
                }

                Text(
                    text = "${pagerState.currentPage + 1} / 7",
                    color = TEXT_SECONDARY,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )

                TextButton(
                    onClick = {
                        if (pagerState.currentPage < 6) {
                            coroutineScope.launch { pagerState.animateScrollToPage(pagerState.currentPage + 1) }
                        } else {
                            onBack()
                        }
                    }
                ) {
                    Text(
                        text = if (pagerState.currentPage == 6) "CLOSE" else "NEXT",
                        color = ACCENT_GREEN
                    )
                }
            }
        }

        // Show Confetti if triggered by page state
        val currentPageConfetti = when (pagerState.currentPage) {
            0 -> story.pageScore.showConfetti
            3 -> story.pageAchievements.showConfetti
            else -> false
        }
        if (currentPageConfetti) {
            CustomConfettiEffect()
        }
    }
}

// ── Story Pager Top Progress Bar ──────────────────────────────────────────────

@Composable
private fun StoryIndicatorBar(
    pageCount: Int,
    currentPage: Int,
    onProgressComplete: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 16.dp, start = 16.dp, end = 16.dp, bottom = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        for (i in 0 until pageCount) {
            val progress = when {
                i < currentPage -> 1f
                i > currentPage -> 0f
                else -> {
                    var progressState by remember { mutableStateOf(0f) }
                    LaunchedEffect(currentPage) {
                        progressState = 0f
                        val duration = 7000f // 7 seconds per story screen
                        val intervals = 70
                        for (step in 1..intervals) {
                            delay((duration / intervals).toLong())
                            progressState = step / intervals.toFloat()
                        }
                        onProgressComplete()
                    }
                    progressState
                }
            }
            LinearProgressIndicator(
                progress = progress,
                modifier = Modifier
                    .weight(1f)
                    .height(3.dp)
                    .clip(RoundedCornerShape(2.dp)),
                color = ACCENT_GREEN,
                trackColor = GLASS_WHITE
            )
        }
    }
}

// ── Page 1: Score ─────────────────────────────────────────────────────────────

@Composable
private fun StoryPageScore(data: MoneyScorePageDto) {
    val animatedScore by animateIntAsState(
        targetValue = data.moneyScore,
        animationSpec = tween(1200, easing = FastOutSlowInEasing),
        label = "score"
    )

    Column(
        modifier = Modifier
            .fillMaxSize(),
        verticalArrangement = Arrangement.SpaceEvenly,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "YOUR MONEY SCORE",
                color = TEXT_SECONDARY,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.5.sp
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = data.scoreHeadline,
                color = TEXT_PRIMARY,
                fontSize = 18.sp,
                fontWeight = FontWeight.SemiBold,
                textAlign = TextAlign.Center
            )
        }

        Box(contentAlignment = Alignment.Center, modifier = Modifier.size(200.dp)) {
            Canvas(modifier = Modifier.size(190.dp)) {
                val strokeWidth = 14.dp.toPx()
                drawArc(
                    color = GLASS_WHITE,
                    startAngle = -90f,
                    sweepAngle = 360f,
                    useCenter = false,
                    style = Stroke(strokeWidth, cap = StrokeCap.Round),
                    topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
                    size = Size(size.width - strokeWidth, size.height - strokeWidth)
                )
                drawArc(
                    color = Color(android.graphics.Color.parseColor(data.scoreColor)),
                    startAngle = -90f,
                    sweepAngle = (animatedScore / 100f) * 360f,
                    useCenter = false,
                    style = Stroke(strokeWidth, cap = StrokeCap.Round),
                    topLeft = Offset(strokeWidth / 2, strokeWidth / 2),
                    size = Size(size.width - strokeWidth, size.height - strokeWidth)
                )
            }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "$animatedScore",
                    color = Color(android.graphics.Color.parseColor(data.scoreColor)),
                    fontSize = 48.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = data.scoreLabel.uppercase(),
                    color = TEXT_SECONDARY,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
            }
        }

        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(12.dp))
                .background(Color(android.graphics.Color.parseColor(data.moodColor)).copy(alpha = 0.15f))
                .border(1.dp, Color(android.graphics.Color.parseColor(data.moodColor)).copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            Text(
                text = "Mood: ${data.financialMood}",
                color = Color(android.graphics.Color.parseColor(data.moodColor)),
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp
            )
        }
    }
}

// ── Page 2: Spending ─────────────────────────────────────────────────────────

@Composable
private fun StoryPageSpending(data: SpendingPageDto) {
    val totalAmount = data.topCategories.values.sum().takeIf { it > 0 } ?: 1.0
    val maxBarValue = data.dailyPoints.maxOrNull()?.takeIf { it > 0 } ?: 1.0

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(20.dp)
    ) {
        item {
            Column {
                Text(
                    text = "WEEKLY SPENDING",
                    color = TEXT_SECONDARY,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.2.sp
                )
                Text(
                    text = data.totalSpendFormatted,
                    color = TEXT_PRIMARY,
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = data.spendChangeText,
                    color = if (data.spendChangeIsIncrease) ACCENT_RED else ACCENT_GREEN,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }

        // Daily Activity Piller Chart
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(110.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(GLASS_WHITE)
                    .padding(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxSize(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom
                ) {
                    data.dailyPoints.forEachIndexed { idx, valPoint ->
                        val fraction = (valPoint / maxBarValue).toFloat().coerceIn(0f, 1f)
                        val heightFraction by animateFloatAsState(
                            targetValue = fraction,
                            animationSpec = tween(700, delayMillis = idx * 50),
                            label = "bar_$idx"
                        )
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .width(18.dp)
                                    .weight(1f, fill = false)
                                    .fillMaxHeight(heightFraction.coerceAtLeast(0.05f))
                                    .clip(RoundedCornerShape(topStart = 4.dp, topEnd = 4.dp))
                                    .background(if (valPoint == data.dailyPoints.maxOrNull()) ACCENT_GREEN else ACCENT_BLUE.copy(alpha = 0.6f))
                            )
                            Text(
                                text = data.dailyLabels.getOrNull(idx) ?: "",
                                color = TEXT_SECONDARY,
                                fontSize = 9.sp
                            )
                        }
                    }
                }
            }
        }

        // Top Categories list
        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "TOP CATEGORIES",
                    color = TEXT_SECONDARY,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
                data.topCategories.entries.forEachIndexed { idx, (cat, amt) ->
                    val progress = (amt / totalAmount).toFloat().coerceIn(0f, 1f)
                    val barColor = when (idx) {
                        0 -> ACCENT_GREEN
                        1 -> ACCENT_BLUE
                        2 -> ACCENT_ORANGE
                        else -> ACCENT_PURPLE
                    }
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(cat, color = TEXT_PRIMARY, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text(data.topCategoriesFormatted[cat] ?: "", color = barColor, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                        val animProgress by animateFloatAsState(
                            targetValue = progress,
                            animationSpec = tween(800, delayMillis = idx * 100),
                            label = "cat_bar"
                        )
                        LinearProgressIndicator(
                            progress = animProgress,
                            modifier = Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp)),
                            color = barColor,
                            trackColor = GLASS_WHITE
                        )
                    }
                }
            }
        }
    }
}

// ── Page 3: Savings ──────────────────────────────────────────────────────────

@Composable
private fun StoryPageSavings(data: SavingsPageDto) {
    val maxVal = data.savingsTrend.maxOrNull()?.takeIf { it > 0 } ?: 1.0

    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Text(
                text = "WEEKLY SAVINGS RATE",
                color = TEXT_SECONDARY,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            Text(
                text = data.savingsAmountFormatted,
                color = ACCENT_GREEN,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = data.savingsHeadline,
                color = TEXT_PRIMARY,
                fontSize = 14.sp
            )
        }

        // Animated Area Chart / Sparkline replacement for Savings trend
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(150.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(GLASS_WHITE)
                .border(1.dp, GLASS_BORDER, RoundedCornerShape(16.dp))
                .padding(16.dp)
        ) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val stepX = size.width / 6f
                val points = data.savingsTrend.map { (it / maxVal).toFloat() }

                val path = Path().apply {
                    points.forEachIndexed { index, yFrac ->
                        val x = index * stepX
                        val y = size.height - (yFrac * size.height)
                        if (index == 0) moveTo(x, y) else lineTo(x, y)
                    }
                }

                // Fill under curve
                val filledPath = Path().apply {
                    addPath(path)
                    lineTo(size.width, size.height)
                    lineTo(0f, size.height)
                    close()
                }

                drawPath(
                    path = filledPath,
                    brush = Brush.verticalGradient(
                        colors = listOf(ACCENT_GREEN.copy(alpha = 0.3f), Color.Transparent)
                    )
                )
                drawPath(
                    path = path,
                    color = ACCENT_GREEN,
                    style = Stroke(width = 3.dp.toPx(), cap = StrokeCap.Round)
                )
            }
        }

        // Summary banner
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(GLASS_WHITE)
                .padding(16.dp)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(ACCENT_GREEN.copy(alpha = 0.15f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = if (data.savingsIsPositive) Icons.Default.TrendingUp else Icons.Default.TrendingDown,
                        contentDescription = null,
                        tint = ACCENT_GREEN
                    )
                }
                Column {
                    Text("Prior week expenses: ${data.savingsVsLastWeekFormatted}", color = TEXT_SECONDARY, fontSize = 11.sp)
                    Text("Disciplined lifestyle pays off.", color = TEXT_PRIMARY, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

// ── Page 4: Achievements ─────────────────────────────────────────────────────

@Composable
private fun StoryPageAchievements(data: AchievementsPageDto) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Column {
            Text(
                text = "WEEKLY ACHIEVEMENTS",
                color = TEXT_SECONDARY,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            Text(
                text = data.headline,
                color = TEXT_PRIMARY,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }

        // Grid of 6 badges
        Column(verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.weight(1f)) {
            val chunked = data.badges.chunked(2)
            chunked.forEach { rowList ->
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                    rowList.forEach { badge ->
                        val badgeColor = try {
                            Color(android.graphics.Color.parseColor(badge.color))
                        } catch (e: Exception) {
                            ACCENT_BLUE
                        }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(90.dp)
                                .clip(RoundedCornerShape(16.dp))
                                .background(if (badge.earned) GLASS_WHITE else GLASS_WHITE.copy(alpha = 0.03f))
                                .border(
                                    1.dp,
                                    if (badge.earned) badgeColor.copy(alpha = 0.4f) else Color.Transparent,
                                    RoundedCornerShape(16.dp)
                                )
                                .padding(12.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxSize(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = badge.icon,
                                    fontSize = 26.sp,
                                    modifier = Modifier.alpha(if (badge.earned) 1f else 0.2f)
                                )
                                Column {
                                    Text(
                                        text = badge.label,
                                        color = if (badge.earned) TEXT_PRIMARY else TEXT_SECONDARY.copy(alpha = 0.4f),
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                    Text(
                                        text = badge.description,
                                        color = TEXT_SECONDARY.copy(alpha = if (badge.earned) 0.8f else 0.3f),
                                        fontSize = 10.sp,
                                        lineHeight = 13.sp,
                                        maxLines = 2,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

// ── Page 5: Mistakes ─────────────────────────────────────────────────────────

@Composable
private fun StoryPageMistakes(data: MistakesPageDto) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Text(
                text = "FINANCIAL LEAKS",
                color = TEXT_SECONDARY,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            Text(
                text = if (data.has_mistakes) "Areas of concern" else "Zero Budget Spills! 🎉",
                color = if (data.has_mistakes) ACCENT_RED else ACCENT_GREEN,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }

        if (data.has_mistakes) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.weight(1f).padding(vertical = 16.dp)) {
                // Card 1: Worst Decision
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = SURFACE_DARK),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Icon(Icons.Default.PriorityHigh, contentDescription = null, tint = ACCENT_RED, modifier = Modifier.size(16.dp))
                            Text("AI Analysis", color = ACCENT_RED, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(data.worstDecision, color = TEXT_PRIMARY, fontSize = 13.sp, lineHeight = 18.sp)
                    }
                }

                // Card 2: Exceeded budgets list
                if (data.exceededBudgets.isNotEmpty() || data.overspendCategories.isNotEmpty()) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = SURFACE_DARK),
                        shape = RoundedCornerShape(16.dp)
                    ) {
                        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text("Busted budgets or heavy trends:", color = TEXT_SECONDARY, fontSize = 11.sp)
                            val lists = (data.exceededBudgets + data.overspendCategories).distinct()
                            lists.forEach { budget ->
                                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Box(modifier = Modifier.size(6.dp).clip(CircleShape).background(ACCENT_RED))
                                    Text(budget, color = TEXT_PRIMARY, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                                }
                            }
                        }
                    }
                }
            }

            // Improvement TIP banner
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(ACCENT_BLUE.copy(alpha = 0.15f))
                    .padding(16.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("SUGGESTED CORRECTION", color = ACCENT_BLUE, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(data.improvementTip, color = TEXT_PRIMARY, fontSize = 13.sp, lineHeight = 17.sp)
                }
            }
        } else {
            // Congratulatory screen if no mistakes
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("🏅", fontSize = 56.sp)
                    Text(
                        text = "Perfect Budget Execution!",
                        color = TEXT_PRIMARY,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "You didn't exceed a single weekly budget limit and avoided major spend spikes. Keep this streak alive!",
                        color = TEXT_SECONDARY,
                        fontSize = 13.sp,
                        textAlign = TextAlign.Center,
                        lineHeight = 19.sp
                    )
                }
            }
        }
    }
}

// ── Page 6: Forecast ─────────────────────────────────────────────────────────

@Composable
private fun StoryPageForecast(data: ForecastPageDto) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            Text(
                text = "NEXT WEEK FORECAST",
                color = TEXT_SECONDARY,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp
            )
            Text(
                text = data.predicted_spend_formatted,
                color = ACCENT_BLUE,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "Predicted Spending Trend",
                color = TEXT_PRIMARY,
                fontSize = 14.sp
            )
        }

        // Forecast Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SURFACE_DARK),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Default.OnlinePrediction, contentDescription = null, tint = ACCENT_BLUE)
                    Text("AI Prediction", color = ACCENT_BLUE, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
                Text(
                    text = data.prediction_next_week,
                    color = TEXT_PRIMARY,
                    fontSize = 13.sp,
                    lineHeight = 18.sp
                )
            }
        }

        // Bills Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SURFACE_DARK),
            shape = RoundedCornerShape(16.dp)
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("Bills due next week", color = TEXT_SECONDARY, fontSize = 11.sp)
                    Text(data.upcoming_subscriptions_total_formatted, color = TEXT_PRIMARY, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(android.graphics.Color.parseColor(data.riskColor)).copy(alpha = 0.15f))
                        .padding(horizontal = 10.dp, vertical = 5.dp)
                ) {
                    Text(
                        text = "RISK: ${data.riskLevel.uppercase()}",
                        color = Color(android.graphics.Color.parseColor(data.riskColor)),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

// ── Page 7: Action Plan ──────────────────────────────────────────────────────

@Composable
private fun StoryPageAction(data: ActionPlanPageDto) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column {
                Text(
                    text = "ACTION PLAN",
                    color = TEXT_SECONDARY,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.2.sp
                )
                Text(
                    text = "Recommended for you",
                    color = TEXT_PRIMARY,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        // Smart tip list
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                data.aiTips.forEach { tip ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(GLASS_WHITE)
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text("🎯", fontSize = 18.sp)
                        Text(tip, color = TEXT_PRIMARY, fontSize = 12.sp, lineHeight = 16.sp)
                    }
                }
            }
        }

        // Challenge card
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = ACCENT_PURPLE.copy(alpha = 0.1f)),
                shape = RoundedCornerShape(16.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, ACCENT_PURPLE.copy(alpha = 0.3f))
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("🏆 WEEKLY CHALLENGE", color = ACCENT_PURPLE, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text(data.weeklyChallenge, color = TEXT_PRIMARY, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, lineHeight = 18.sp)
                }
            }
        }

        // Share Card Text Preview
        item {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("SHARE YOUR STORY", color = TEXT_SECONDARY, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                OutlinedButton(
                    onClick = { /* Share functionality triggers system intent */ },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = ACCENT_GREEN),
                    border = androidx.compose.foundation.BorderStroke(1.dp, ACCENT_GREEN.copy(alpha = 0.4f))
                ) {
                    Icon(Icons.Default.Share, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Share with Friends")
                }
            }
        }
    }
}

// ── Particle Confetti Emitter ───────────────────────────────────────────────

@Composable
private fun CustomConfettiEffect() {
    val particles = remember {
        List(40) {
            ConfettiParticle(
                x = Random.nextFloat(),
                y = -0.2f - Random.nextFloat() * 0.4f,
                speed = 2f + Random.nextFloat() * 4f,
                color = listOf(ACCENT_GREEN, ACCENT_BLUE, ACCENT_ORANGE, ACCENT_PURPLE, ACCENT_RED).random(),
                size = 10f + Random.nextFloat() * 15f
            )
        }
    }

    val transition = rememberInfiniteTransition(label = "confetti")
    val ticker by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2500, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "ticker"
    )

    Canvas(modifier = Modifier.fillMaxSize()) {
        particles.forEach { particle ->
            val progressY = ticker * particle.speed
            val currentY = (particle.y + progressY) % 1.2f
            if (currentY > 0 && currentY < 1f) {
                drawCircle(
                    color = particle.color,
                    radius = particle.size / 2,
                    center = Offset(particle.x * size.width, currentY * size.height)
                )
            }
        }
    }
}

private data class ConfettiParticle(
    val x: Float,
    val y: Float,
    val speed: Float,
    val color: Color,
    val size: Float
)
