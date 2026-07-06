package com.example.moneytracker.ui.family

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.*

// ── HSL tailored Fintech colors ──────────────────────────────────────────────
private val BG_DARK = Color(0xFF0B0F17)
private val SURFACE_DARK = Color(0xFF131924)
private val SURFACE_LIGHT = Color(0xFF1E293B)
private val GLASS_WHITE = Color(0x12FFFFFF)
private val GLASS_BORDER = Color(0x1EFFFFFF)
private val ACCENT_GREEN = Color(0xFF4CAF7D)
private val ACCENT_BLUE = Color(0xFF90CAF9)
private val ACCENT_ORANGE = Color(0xFFF5A623)
private val TEXT_PRIMARY = Color(0xFFF1F5F9)
private val TEXT_SECONDARY = Color(0xFF94A3B8)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FamilyScreen(
    viewModel: FamilyViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var showCreateDialog by remember { mutableStateOf(false) }
    var showJoinDialog by remember { mutableStateOf(false) }
    var showAddExpenseDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Family Wallet", color = TEXT_PRIMARY, fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TEXT_PRIMARY)
                    }
                },
                actions = {
                    if (uiState is FamilyUiState.WalletsLoaded) {
                        IconButton(onClick = { showCreateDialog = true }) {
                            Icon(Icons.Default.Add, contentDescription = "Create", tint = ACCENT_GREEN)
                        }
                        IconButton(onClick = { showJoinDialog = true }) {
                            Icon(Icons.Default.GroupAdd, contentDescription = "Join", tint = ACCENT_BLUE)
                        }
                    } else if (uiState is FamilyUiState.WalletDetails) {
                        IconButton(onClick = { viewModel.loadWallets() }) {
                            Icon(Icons.Default.Home, contentDescription = "Wallets List", tint = TEXT_PRIMARY)
                        }
                        IconButton(onClick = { showAddExpenseDialog = true }) {
                            Icon(Icons.Default.PostAdd, contentDescription = "Log Expense", tint = ACCENT_GREEN)
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BG_DARK)
            )
        },
        containerColor = BG_DARK
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (val state = uiState) {
                is FamilyUiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = ACCENT_GREEN)
                    }
                }
                is FamilyUiState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxSize().padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(Icons.Default.ErrorOutline, contentDescription = null, tint = ACCENT_ORANGE, modifier = Modifier.size(56.dp))
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(state.message, color = TEXT_PRIMARY, fontSize = 14.sp, textAlign = TextAlign.Center)
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(onClick = { viewModel.loadWallets() }, colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)) {
                            Text("Go to Wallets", color = Color.White)
                        }
                    }
                }
                is FamilyUiState.WalletsLoaded -> {
                    if (state.wallets.isEmpty()) {
                        EmptyWalletsView(
                            onCreateClick = { showCreateDialog = true },
                            onJoinClick = { showJoinDialog = true }
                        )
                    } else {
                        LazyColumn(
                            contentPadding = PaddingValues(16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                            modifier = Modifier.fillMaxSize()
                        ) {
                            item {
                                Text("YOUR SHARED WALLETS", color = TEXT_SECONDARY, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                            }
                            items(state.wallets) { wallet ->
                                WalletCard(wallet = wallet, onClick = { viewModel.selectWallet(wallet.id) })
                            }
                        }
                    }
                }
                is FamilyUiState.WalletDetails -> {
                    WalletDetailsView(
                        wallet = state.wallet,
                        summary = state.summary,
                        onAddExpenseClick = { showAddExpenseDialog = true }
                    )
                }
            }
        }
    }

    // dialogs
    if (showCreateDialog) {
        FamilyInputDialog(
            title = "Create Family Wallet",
            label = "Wallet Name",
            onDismiss = { showCreateDialog = false },
            onConfirm = { name ->
                viewModel.createWallet(name)
                showCreateDialog = false
            }
        )
    }

    if (showJoinDialog) {
        FamilyInputDialog(
            title = "Join Family Wallet",
            label = "Invite Code (FAM-XXXXX)",
            onDismiss = { showJoinDialog = false },
            onConfirm = { code ->
                viewModel.joinWallet(code)
                showJoinDialog = false
            }
        )
    }

    if (showAddExpenseDialog && uiState is FamilyUiState.WalletDetails) {
        val currentWalletId = (uiState as FamilyUiState.WalletDetails).wallet.id
        AddExpenseDialog(
            onDismiss = { showAddExpenseDialog = false },
            onConfirm = { amount, description ->
                viewModel.addExpense(currentWalletId, amount, description)
                showAddExpenseDialog = false
            }
        )
    }
}

@Composable
private fun EmptyWalletsView(
    onCreateClick: () -> Unit,
    onJoinClick: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text("👪", fontSize = 64.sp)
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            "Collaborative Finance",
            color = TEXT_PRIMARY,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            "Split expenses with roomies, manage family budgets together, and view leaderboard ranks in real time.",
            color = TEXT_SECONDARY,
            fontSize = 13.sp,
            textAlign = TextAlign.Center,
            lineHeight = 18.sp
        )
        Spacer(modifier = Modifier.height(32.dp))
        Button(
            onClick = onCreateClick,
            colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Create Shared Wallet", color = Color.White)
        }
        Spacer(modifier = Modifier.height(12.dp))
        OutlinedButton(
            onClick = onJoinClick,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = ACCENT_BLUE),
            border = androidx.compose.foundation.BorderStroke(1.dp, ACCENT_BLUE.copy(alpha = 0.5f)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Join with Invite Code")
        }
    }
}

@Composable
private fun WalletCard(
    wallet: FamilyWalletResponseDto,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .border(1.dp, GLASS_BORDER, RoundedCornerShape(20.dp))
            .clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
    ) {
        Row(
            modifier = Modifier.padding(20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(wallet.name, color = TEXT_PRIMARY, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                Text("Code: ${wallet.inviteCode}", color = ACCENT_BLUE, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                Spacer(modifier = Modifier.height(4.dp))
                Text("${wallet.members.size} members  •  ${wallet.expenses.size} expenses", color = TEXT_SECONDARY, fontSize = 12.sp)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(wallet.totalSpentFormatted, color = ACCENT_GREEN, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                Text("Total spent", color = TEXT_SECONDARY, fontSize = 11.sp)
            }
        }
    }
}

@Composable
private fun WalletDetailsView(
    wallet: FamilyWalletResponseDto,
    summary: FamilySummaryResponseDto,
    onAddExpenseClick: () -> Unit
) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        // Banner card: score + stats
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(24.dp))
                    .border(1.dp, GLASS_BORDER, RoundedCornerShape(24.dp)),
                colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
            ) {
                Row(
                    modifier = Modifier.padding(20.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(wallet.name, color = TEXT_PRIMARY, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("Invite Code: ${wallet.inviteCode}", color = ACCENT_BLUE, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Total Spent: ${wallet.totalSpentFormatted}", color = ACCENT_GREEN, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                    }
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .clip(CircleShape)
                            .background(ACCENT_GREEN.copy(alpha = 0.1f))
                            .border(2.dp, ACCENT_GREEN, CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("${summary.moneyScore}", color = ACCENT_GREEN, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                            Text("Score", color = TEXT_SECONDARY, fontSize = 9.sp)
                        }
                    }
                }
            }
        }

        // Leaderboard
        item {
            Text("FAMILY SAVINGS RANKINGS", color = TEXT_SECONDARY, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }
        items(summary.leaderboard) { rank ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(GLASS_WHITE)
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(rank.avatarEmoji, fontSize = 22.sp)
                    Column {
                        Text(rank.name, color = TEXT_PRIMARY, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                        Text("Rank #${rank.rank}", color = TEXT_SECONDARY, fontSize = 11.sp)
                    }
                }
                Text(rank.savedAmountFormatted, color = ACCENT_GREEN, fontSize = 14.sp, fontWeight = FontWeight.Bold)
            }
        }

        // AI Insights Card
        item {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(20.dp))
                    .border(1.dp, GLASS_BORDER, RoundedCornerShape(20.dp)),
                colors = CardDefaults.cardColors(containerColor = SURFACE_LIGHT)
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("🧠", fontSize = 18.sp)
                        Text("AI Family Insights", color = ACCENT_BLUE, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                    }
                    Text(
                        text = summary.aiInsights,
                        color = TEXT_PRIMARY,
                        fontSize = 12.sp,
                        lineHeight = 17.sp
                    )
                }
            }
        }

        // Log button
        item {
            Button(
                onClick = onAddExpenseClick,
                colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.PostAdd, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Log Shared Expense", color = Color.White)
            }
        }

        // Transactions list
        item {
            Text("SHARED SPLITS LOG", color = TEXT_SECONDARY, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }
        if (wallet.expenses.isEmpty()) {
            item {
                Text("No shared expenses logged yet. Tap the button above to log one.", color = TEXT_SECONDARY, fontSize = 13.sp)
            }
        } else {
            items(wallet.expenses) { expense ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(expense.description, color = TEXT_PRIMARY, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                        Text("Paid by: ${expense.paidByName}", color = TEXT_SECONDARY, fontSize = 11.sp)
                    }
                    Text(expense.amountFormatted, color = ACCENT_ORANGE, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

// ── Dialogs ──────────────────────────────────────────────────────────────────

@Composable
fun FamilyInputDialog(
    title: String,
    label: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit
) {
    var textVal by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title, color = TEXT_PRIMARY) },
        text = {
            OutlinedTextField(
                value = textVal,
                onValueChange = { textVal = it },
                label = { Text(label) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = ACCENT_GREEN,
                    unfocusedBorderColor = TEXT_SECONDARY,
                    focusedTextColor = TEXT_PRIMARY,
                    unfocusedTextColor = TEXT_PRIMARY
                ),
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
        },
        confirmButton = {
            Button(
                onClick = { if (textVal.isNotBlank()) onConfirm(textVal) },
                colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)
            ) {
                Text("Confirm", color = Color.White)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TEXT_SECONDARY)
            }
        },
        containerColor = SURFACE_DARK
    )
}

@Composable
fun AddExpenseDialog(
    onDismiss: () -> Unit,
    onConfirm: (Double, String) -> Unit
) {
    var amount by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Log Shared Expense", color = TEXT_PRIMARY) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it },
                    label = { Text("Amount (₹)") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ACCENT_GREEN,
                        unfocusedBorderColor = TEXT_SECONDARY,
                        focusedTextColor = TEXT_PRIMARY,
                        unfocusedTextColor = TEXT_PRIMARY
                    ),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Description") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ACCENT_GREEN,
                        unfocusedBorderColor = TEXT_SECONDARY,
                        focusedTextColor = TEXT_PRIMARY,
                        unfocusedTextColor = TEXT_PRIMARY
                    ),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val amtDouble = amount.toDoubleOrNull()
                    if (amtDouble != null && description.isNotBlank()) {
                        onConfirm(amtDouble, description)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)
            ) {
                Text("Log Split", color = Color.White)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TEXT_SECONDARY)
            }
        },
        containerColor = SURFACE_DARK
    )
}
