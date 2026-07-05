package com.example.moneytracker.ui.dashboard

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import com.example.moneytracker.R
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.moneytracker.data.remote.dto.DashboardSummaryDto
import com.example.moneytracker.data.remote.dto.SubscriptionDto
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import com.example.moneytracker.ui.activity.ActivityScreen
import com.example.moneytracker.ui.activity.ActivityViewModel
import com.example.moneytracker.ui.budget.BudgetScreen
import com.example.moneytracker.ui.budget.BudgetViewModel
import com.example.moneytracker.ui.components.*
import com.example.moneytracker.ui.components.cards.PremiumCard
import com.example.moneytracker.ui.components.charts.CurvedLineChart
import com.example.moneytracker.ui.components.charts.PremiumDonutChart
import com.example.moneytracker.ui.theme.*
import kotlinx.coroutines.delay
import kotlin.time.Duration.Companion.milliseconds

@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel,
    activityViewModel: ActivityViewModel,
    budgetViewModel: BudgetViewModel? = null
) {
    val uiState by viewModel.uiState.collectAsState()
    val selectedTxId by viewModel.selectedTransactionForCategorize.collectAsState()

    DashboardScreenContent(
        uiState = uiState,
        selectedTxId = selectedTxId,
        onDismissBottomSheet = { viewModel.onCategorizeClicked(null) },
        onCategorySelect = { txId, category -> viewModel.confirmCategorize(txId, category) },
        onRetry = { viewModel.loadDashboardData() },
        onCategorizeClicked = { txId -> viewModel.onCategorizeClicked(txId) },
        activityViewModel = activityViewModel,
        budgetViewModel = budgetViewModel
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreenContent(
    uiState: DashboardUiState,
    selectedTxId: String?,
    onDismissBottomSheet: () -> Unit,
    onCategorySelect: (String, String) -> Unit,
    onRetry: () -> Unit,
    onCategorizeClicked: (String) -> Unit,
    activityViewModel: ActivityViewModel? = null,
    budgetViewModel: BudgetViewModel? = null
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    if (selectedTxId != null) {
        CategoryBottomSheet(
            onDismiss = onDismissBottomSheet,
            onCategorySelect = { category ->
                onCategorySelect(selectedTxId, category)
            }
        )
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = FintechSurface,
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = { PremiumTopBar(
            onMenuClick = { scope.launch { snackbarHostState.showSnackbar("Menu opened") } },
            onNotificationClick = { scope.launch { snackbarHostState.showSnackbar("No new notifications") } }
        ) },
        bottomBar = {
            PremiumBottomNavigation(
                selectedTab = selectedTab,
                onTabSelected = { selectedTab = it }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { scope.launch { snackbarHostState.showSnackbar("Add Transaction flow coming soon") } },
                containerColor = FintechBlue,
                contentColor = Color.White,
                shape = CircleShape,
                modifier = Modifier
                    .size(64.dp)
                    .offset(y = 32.dp)
                    .shadow(12.dp, CircleShape, spotColor = FintechBlue, ambientColor = FintechBlue)
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add Transaction", modifier = Modifier.size(32.dp))
            }
        },
        floatingActionButtonPosition = FabPosition.Center
    ) { padding ->
        Box(modifier = Modifier.padding(padding)) {
            when (uiState) {
                is DashboardUiState.Loading -> DashboardLoadingState()
                is DashboardUiState.Error -> DashboardErrorState(
                    message = uiState.message,
                    onRetry = onRetry
                )
                is DashboardUiState.Success -> {
                    Crossfade(targetState = selectedTab, label = "Tab Transition") { tab ->
                        when (tab) {
                            0 -> DashboardContent(
                                summary = uiState.summary,
                                onCategorize = onCategorizeClicked,
                                onAddClick = { scope.launch { snackbarHostState.showSnackbar("Add Balance flow coming soon") } },
                                onSeeAllClick = { scope.launch { snackbarHostState.showSnackbar("Navigating to all transactions...") } }
                            )
                            1 -> Box(modifier = Modifier.fillMaxSize()) { 
                                if (activityViewModel != null) {
                                    ActivityScreen(viewModel = activityViewModel, onNavigateBack = {})
                                } else {
                                    ActivitySection(uiState.summary.weekly_activity)
                                }
                            }
                            2 -> Box(modifier = Modifier.fillMaxSize()) { 
                                if (budgetViewModel != null) {
                                    BudgetScreen(viewModel = budgetViewModel)
                                } else {
                                    Box(modifier = Modifier.padding(16.dp)) { CategorySection(uiState.summary) }
                                }
                            }
                            3 -> Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Profile settings", color = Color.White) }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PremiumTopBar(
    onMenuClick: () -> Unit,
    onNotificationClick: () -> Unit
) {
    CenterAlignedTopAppBar(
        title = {
            Text(
                "Money Tracker",
                style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
            )
        },
        colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
            containerColor = Color.Transparent,
            titleContentColor = Color.White
        ),
        navigationIcon = {
            IconButton(onClick = onMenuClick) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(FintechSurfaceBright),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.Menu, contentDescription = null, modifier = Modifier.size(20.dp), tint = Color.White)
                }
            }
        },
        actions = {
            IconButton(onClick = onNotificationClick) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(FintechSurfaceBright),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.Notifications, contentDescription = null, modifier = Modifier.size(20.dp), tint = Color.White)
                }
            }
        }
    )
}

@Composable
fun DashboardContent(
    summary: DashboardSummaryDto,
    onCategorize: (String) -> Unit,
    onAddClick: () -> Unit,
    onSeeAllClick: () -> Unit
) {
    val spendValue = parseCurrency(summary.monthly_expense)
    val balanceValue = parseCurrency(summary.total_balance)
    val incomeValue = parseCurrency(summary.monthly_income)
    val savingsValue = parseCurrency(summary.monthly_savings)

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(top = 16.dp, start = 20.dp, end = 20.dp, bottom = 140.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        item {
            CardEntrance {
                BalanceCard(
                    totalBalance = balanceValue,
                    monthlySpending = spendValue,
                    onAddClick = onAddClick
                )
            }
        }

        item {
            CardEntrance(delay = 100) {
                StatsGrid(
                    income = incomeValue,
                    expenses = spendValue,
                    savings = savingsValue
                )
            }
        }

        item {
            CardEntrance(delay = 200) {
                AICoachCard(
                    insight = "You've spent 15% less on Food than last month. Keep it up!"
                )
            }
        }

        item {
            CardEntrance(delay = 300) {
                SpendingScoreCard(score = 85)
            }
        }
        
        item {
            CardEntrance(delay = 400) {
                BudgetCard(
                    spent = spendValue,
                    total = 40000f,
                    progress = (spendValue / 40000f).coerceIn(0f, 1f)
                )
            }
        }

        item {
            CardEntrance(delay = 500) {
                ActivitySection(summary.weekly_activity)
            }
        }

        item {
            CardEntrance(delay = 600) {
                CategorySection(report)
            }
        }

        item {
            CardEntrance(delay = 700) {
                SubscriptionsSection(summary.upcoming_subscriptions)
            }
        }

        item {
            CardEntrance(delay = 800) {
                RecentTransactionsSection(summary.latest_transactions, onCategorize, onSeeAllClick)
            }
        }
    }
}

@Composable
fun CardEntrance(
    delay: Int = 0,
    content: @Composable () -> Unit
) {
    val isPreview = androidx.compose.ui.platform.LocalInspectionMode.current
    var visible by remember { mutableStateOf(isPreview) }
    
    if (!isPreview) {
        LaunchedEffect(Unit) {
            delay(delay.milliseconds)
            visible = true
        }
    }
    
    AnimatedVisibility(
        visible = visible,
        enter = slideInVertically(initialOffsetY = { it / 2 }) + fadeIn(animationSpec = tween(600)),
        exit = fadeOut()
    ) {
        content()
    }
}

private fun parseCurrency(formatted: String): Float {
    return formatted.replace("₹", "").replace(",", "").toFloatOrNull() ?: 0f
}

@Composable
fun ActivitySection(weeklyActivity: com.example.moneytracker.data.remote.dto.WeeklyActivityDto) {
    PremiumCard {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("Weekly Activity", style = MaterialTheme.typography.titleMedium, color = Color.White)
                    val formattedAvg = java.text.NumberFormat.getCurrencyInstance(java.util.Locale("en", "IN")).apply {
                        maximumFractionDigits = 0
                    }.format(weeklyActivity.average_per_day)
                    Text("Average $formattedAvg/day", style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
                }
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(FintechBlue.copy(alpha = 0.1f))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text("Last 7 Days", style = MaterialTheme.typography.labelSmall, color = FintechBlue)
                }
            }
            Spacer(modifier = Modifier.height(24.dp))
            CurvedLineChart(
                points = if (weeklyActivity.points.isEmpty()) listOf(0f, 0f, 0f, 0f, 0f, 0f, 0f) else weeklyActivity.points,
                modifier = Modifier.height(150.dp).fillMaxWidth()
            )
        }
    }
}

@Composable
fun CategorySection(summary: DashboardSummaryDto) {
    PremiumCard {
        Column {
            Text("Spending Breakdown", style = MaterialTheme.typography.titleMedium, color = Color.White)
            Spacer(modifier = Modifier.height(32.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                PremiumDonutChart(
                    data = summary.top_categories,
                    modifier = Modifier.size(160.dp),
                    centerLabel = summary.monthly_expense
                )
                Spacer(modifier = Modifier.width(24.dp))
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    summary.top_categories.entries.take(4).forEachIndexed { index, entry ->
                        CategoryIndicator(
                            name = entry.key,
                            color = listOf(FintechBlue, FintechPurple, FintechGreen, FintechOrange)[index % 4],
                            percentage = (entry.value / summary.top_categories.values.sum() * 100).toInt()
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun CategoryIndicator(name: String, color: Color, percentage: Int) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(color))
            Spacer(modifier = Modifier.width(12.dp))
            Text(name, style = MaterialTheme.typography.bodyMedium, color = FintechSecondary)
        }
        Text("$percentage%", style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold, color = Color.White))
    }
}

@Composable
fun SubscriptionsSection(subscriptions: List<SubscriptionDto>) {
    Column {
        Text("Upcoming Bills", style = MaterialTheme.typography.titleMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        if (subscriptions.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(100.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .background(FintechSurfaceVariant),
                contentAlignment = Alignment.Center
            ) {
                Text("No upcoming bills", color = FintechSecondary)
            }
        } else {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                items(subscriptions) { sub ->
                    SubscriptionCard(sub)
                }
            }
        }
    }
}

@Composable
fun SubscriptionCard(sub: SubscriptionDto) {
    Box(
        modifier = Modifier
            .width(160.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(FintechSurfaceVariant)
            .padding(16.dp)
    ) {
        Column {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(FintechSurfaceBright),
                contentAlignment = Alignment.Center
            ) {
                Text(sub.merchant.take(1), fontWeight = FontWeight.Bold, color = FintechBlue)
            }
            Spacer(modifier = Modifier.height(16.dp))
            Text(sub.merchant, fontWeight = FontWeight.SemiBold, maxLines = 1, color = Color.White)
            Text(sub.amount_formatted, style = MaterialTheme.typography.titleSmall, color = Color.White)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "${sub.countdown_days}d left",
                style = MaterialTheme.typography.labelSmall,
                color = FintechOrange
            )
        }
    }
}

@Composable
fun RecentTransactionsSection(
    transactions: List<TransactionItemDto>,
    onCategorize: (String) -> Unit,
    onSeeAllClick: () -> Unit
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Recent Activity", style = MaterialTheme.typography.titleMedium, color = Color.White)
            TextButton(onClick = onSeeAllClick) {
                Text("See All", color = FintechBlue)
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            transactions.forEach { tx ->
                TransactionRowItem(tx, onCategorize)
            }
        }
    }
}

@Composable
fun PremiumBottomNavigation(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit
) {
    BottomAppBar(
        containerColor = FintechSurface.copy(alpha = 0.95f),
        contentColor = Color.White,
        tonalElevation = 0.dp,
        modifier = Modifier
            .height(90.dp)
            .clip(RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp))
            .border(1.dp, Color.White.copy(alpha = 0.05f), RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp))
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            NavigationBarItem(
                selected = selectedTab == 0,
                onClick = { onTabSelected(0) },
                icon = { Icon(if (selectedTab == 0) Icons.Default.Dashboard else Icons.Outlined.Dashboard, null) },
                label = { Text(stringResource(R.string.dashboard_tab_home)) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = FintechBlue,
                    unselectedIconColor = FintechSecondary,
                    indicatorColor = Color.Transparent
                )
            )
            NavigationBarItem(
                selected = selectedTab == 1,
                onClick = { onTabSelected(1) },
                icon = { Icon(if (selectedTab == 1) Icons.Default.Receipt else Icons.Outlined.Receipt, null) },
                label = { Text(stringResource(R.string.dashboard_tab_activity)) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = FintechBlue,
                    unselectedIconColor = FintechSecondary,
                    indicatorColor = Color.Transparent
                )
            )
            
            // Spacer for FAB
            Box(modifier = Modifier.size(64.dp))
            
            NavigationBarItem(
                selected = selectedTab == 2,
                onClick = { onTabSelected(2) },
                icon = { Icon(if (selectedTab == 2) Icons.Default.BarChart else Icons.Outlined.BarChart, null) },
                label = { Text(stringResource(R.string.dashboard_tab_analytics)) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = FintechBlue,
                    unselectedIconColor = FintechSecondary,
                    indicatorColor = Color.Transparent
                )
            )
            NavigationBarItem(
                selected = selectedTab == 3,
                onClick = { onTabSelected(3) },
                icon = { Icon(if (selectedTab == 3) Icons.Default.Person else Icons.Outlined.Person, null) },
                label = { Text(stringResource(R.string.dashboard_tab_profile)) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = FintechBlue,
                    unselectedIconColor = FintechSecondary,
                    indicatorColor = Color.Transparent
                )
            )
        }
    }
}

@Composable
fun DashboardLoadingState() {
    Column(
        modifier = Modifier.padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(180.dp).clip(RoundedCornerShape(28.dp)))
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            repeat(3) {
                ShimmerEffect(modifier = Modifier.weight(1f).height(100.dp).clip(RoundedCornerShape(24.dp)))
            }
        }
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(80.dp).clip(RoundedCornerShape(28.dp)))
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(250.dp).clip(RoundedCornerShape(28.dp)))
    }
}

@Composable
fun DashboardErrorState(message: String, onRetry: () -> Unit) {
    Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.ErrorOutline, contentDescription = null, modifier = Modifier.size(64.dp), tint = FintechRed)
            Spacer(modifier = Modifier.height(16.dp))
            Text(message, textAlign = androidx.compose.ui.text.style.TextAlign.Center, color = Color.White)
            Spacer(modifier = Modifier.height(24.dp))
            Button(
                onClick = onRetry,
                colors = ButtonDefaults.buttonColors(containerColor = FintechBlue)
            ) {
                Text("Retry")
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CategoryBottomSheet(
    onDismiss: () -> Unit,
    onCategorySelect: (String) -> Unit
) {
    val categories = listOf("Food", "Shopping", "Bills", "Travel", "Entertainment", "Other")
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = FintechSurfaceVariant,
        dragHandle = { BottomSheetDefaults.DragHandle(color = FintechSecondary) }
    ) {
        Column(modifier = Modifier.padding(24.dp).padding(bottom = 32.dp)) {
            Text("Categorize Transaction", style = MaterialTheme.typography.headlineSmall, color = Color.White)
            Spacer(modifier = Modifier.height(24.dp))
            categories.chunked(3).forEach { row ->
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    row.forEach { cat ->
                        AssistChip(
                            onClick = { onCategorySelect(cat) },
                            label = { Text(cat) },
                            modifier = Modifier.weight(1f),
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = FintechSurfaceBright,
                                labelColor = Color.White
                            ),
                            border = null
                        )
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun DashboardPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        DashboardContent(
            summary = DashboardSummaryDto(
                total_balance = "₹84,250",
                monthly_income = "₹1,20,000",
                monthly_expense = "₹12,450",
                monthly_savings = "₹35,750",
                total_transactions = 15,
                latest_transactions = listOf(
                    TransactionItemDto("1", "Apple Store", "₹1,49,900", "2 min ago", "Shopping"),
                    TransactionItemDto("2", "Starbucks", "₹450", "1 hour ago", "Food"),
                    TransactionItemDto("3", "Netflix", "₹649", "Yesterday", "Entertainment"),
                    TransactionItemDto("4", "Uber", "₹280", "Yesterday", "Travel")
                ),
                top_categories = mapOf("Food" to 4000f, "Transport" to 2000f, "Shopping" to 6450f),
                upcoming_subscriptions = listOf(
                    SubscriptionDto("1", "Netflix", "₹649", "2024-07-10", 5),
                    SubscriptionDto("2", "Spotify", "₹119", "2024-07-15", 12)
                ),
                weekly_activity = com.example.moneytracker.data.remote.dto.WeeklyActivityDto(
                    average_per_day = 4200f,
                    points = listOf(200f, 450f, 150f, 800f, 300f, 600f, 420f)
                )
            ),
            onCategorize = {},
            onAddClick = {},
            onSeeAllClick = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
fun DashboardScreenPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        DashboardScreenContent(
            uiState = DashboardUiState.Success(
                summary = DashboardSummaryDto(
                    total_balance = "₹84,250",
                    monthly_income = "₹1,20,000",
                    monthly_expense = "₹12,450",
                    monthly_savings = "₹35,750",
                    total_transactions = 15,
                    latest_transactions = listOf(
                        TransactionItemDto("1", "Apple Store", "₹1,49,900", "2 min ago", "Shopping"),
                        TransactionItemDto("2", "Starbucks", "₹450", "1 hour ago", "Food"),
                        TransactionItemDto("3", "Netflix", "₹649", "Yesterday", "Entertainment"),
                        TransactionItemDto("4", "Uber", "₹280", "Yesterday", "Travel")
                    ),
                    top_categories = mapOf("Food" to 4000f, "Transport" to 2000f, "Shopping" to 6450f),
                    upcoming_subscriptions = listOf(
                        SubscriptionDto("1", "Netflix", "₹649", "2024-07-10", 5),
                        SubscriptionDto("2", "Spotify", "₹119", "2024-07-15", 12)
                    ),
                    weekly_activity = com.example.moneytracker.data.remote.dto.WeeklyActivityDto(
                        average_per_day = 4200f,
                        points = listOf(200f, 450f, 150f, 800f, 300f, 600f, 420f)
                    )
                )
            ),
            selectedTxId = null,
            onDismissBottomSheet = {},
            onCategorySelect = { _, _ -> },
            onRetry = {},
            onCategorizeClicked = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun RecentTransactionsSectionPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        RecentTransactionsSection(
            transactions = listOf(
                TransactionItemDto("1", "Apple Store", "₹1,49,900", "2 min ago", "Shopping"),
                TransactionItemDto("2", "Starbucks", "₹450", "1 hour ago", "Food"),
                TransactionItemDto("3", "Netflix", "₹649", "Yesterday", "Entertainment"),
                TransactionItemDto("4", "Uber", "₹280", "Yesterday", "Travel")
            ),
            onCategorize = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun PremiumTopBarPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        PremiumTopBar()
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun CardEntrancePreview() {
    MoneyTrackerTheme(darkTheme = true) {
        CardEntrance {
            BalanceCard(
                totalBalance = 84250f,
                monthlySpending = 12450f,
                onAddClick = {}
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun SubscriptionsSectionPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        Box(modifier = Modifier.padding(20.dp)) {
            SubscriptionsSection(
                subscriptions = listOf(
                    SubscriptionDto("1", "Netflix", "₹649", "2024-07-10", 5),
                    SubscriptionDto("2", "Spotify", "₹119", "2024-07-15", 12),
                    SubscriptionDto("3", "YouTube", "₹129", "2024-07-20", 15)
                )
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun SubscriptionsSectionEmptyPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        Box(modifier = Modifier.padding(20.dp)) {
            SubscriptionsSection(subscriptions = emptyList())
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun DashboardErrorStatePreview() {
    MoneyTrackerTheme(darkTheme = true) {
        DashboardErrorState(
            message = "Unable to load dashboard data. Please check your internet connection.",
            onRetry = {}
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun CategoryIndicatorPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        Column(modifier = Modifier.padding(16.dp)) {
            CategoryIndicator(name = "Food & Drinks", color = Color(0xFF4CAF50), percentage = 45)
            Spacer(modifier = Modifier.height(8.dp))
            CategoryIndicator(name = "Shopping", color = Color(0xFFFFC107), percentage = 30)
            Spacer(modifier = Modifier.height(8.dp))
            CategoryIndicator(name = "Transport", color = Color(0xFF2196F3), percentage = 25)
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun ActivitySectionPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        Box(modifier = Modifier.padding(20.dp)) {
            ActivitySection(
                com.example.moneytracker.data.remote.dto.WeeklyActivityDto(
                    average_per_day = 4200f,
                    points = listOf(200f, 450f, 150f, 800f, 300f, 600f, 420f)
                )
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF080808)
@Composable
fun CardEntranceStatsPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        Box(modifier = Modifier.padding(20.dp)) {
            CardEntrance {
                StatsGrid(
                    income = 50000f,
                    expenses = 32000f,
                    savings = 18000f
                )
            }
        }
    }
}
