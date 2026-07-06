package com.example.moneytracker.ui.notifications

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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.NotificationDto

// ── Aesthetics & Palette ──────────────────────────────────────────────────────
private val BG_DARK = Color(0xFF0B0F17)
private val SURFACE_DARK = Color(0xFF131924)
private val SURFACE_LIGHT = Color(0xFF1E293B)
private val GLASS_WHITE = Color(0x12FFFFFF)
private val GLASS_BORDER = Color(0x1EFFFFFF)
private val ACCENT_GREEN = Color(0xFF4CAF7D)
private val ACCENT_BLUE = Color(0xFF90CAF9)
private val ACCENT_ORANGE = Color(0xFFF5A623)
private val ACCENT_RED = Color(0xFFEF5350)
private val ACCENT_PURPLE = Color(0xFFCE93D8)
private val TEXT_PRIMARY = Color(0xFFF1F5F9)
private val TEXT_SECONDARY = Color(0xFF94A3B8)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotificationScreen(
    viewModel: NotificationViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var selectedFilter by remember { mutableStateOf("All") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Smart Notifications", color = TEXT_PRIMARY, fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TEXT_PRIMARY)
                    }
                },
                actions = {
                    if (uiState is NotificationUiState.Success) {
                        val notifs = (uiState as NotificationUiState.Success).notifications
                        val unreadIds = notifs.filter { !it.isRead }.map { it.id }
                        if (unreadIds.isNotEmpty()) {
                            TextButton(
                                onClick = { viewModel.markAsRead(unreadIds) },
                                colors = ButtonDefaults.textButtonColors(contentColor = ACCENT_GREEN)
                            ) {
                                Text("Mark All Read", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = BG_DARK)
            )
        },
        containerColor = BG_DARK
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Filter chips
            FilterBar(
                selectedFilter = selectedFilter,
                onFilterSelected = { selectedFilter = it }
            )

            Box(modifier = Modifier.fillGrid()) {
                when (val state = uiState) {
                    is NotificationUiState.Loading -> {
                        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator(color = ACCENT_GREEN)
                        }
                    }
                    is NotificationUiState.Error -> {
                        Column(
                            modifier = Modifier.fillMaxSize().padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center
                        ) {
                            Icon(Icons.Default.Warning, contentDescription = null, tint = ACCENT_RED, modifier = Modifier.size(48.dp))
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(state.message, color = TEXT_PRIMARY, fontSize = 14.sp, textAlign = TextAlign.Center)
                            Spacer(modifier = Modifier.height(24.dp))
                            Button(onClick = { viewModel.loadNotifications() }, colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)) {
                                Text("Retry", color = Color.White)
                            }
                        }
                    }
                    is NotificationUiState.Success -> {
                        val filteredList = state.notifications.filter {
                            when (selectedFilter) {
                                "All" -> true
                                "Alerts" -> it.notificationType == "alert"
                                "Subscriptions" -> it.notificationType == "subscription"
                                "Insights" -> it.notificationType == "insight"
                                else -> true
                            }
                        }

                        if (filteredList.isEmpty()) {
                            Column(
                                modifier = Modifier.fillMaxSize().padding(32.dp),
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center
                            ) {
                                Text("🔔", fontSize = 48.sp)
                                Spacer(modifier = Modifier.height(16.dp))
                                Text("All caught up!", color = TEXT_PRIMARY, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("No notifications found matching your filter.", color = TEXT_SECONDARY, fontSize = 12.sp, textAlign = TextAlign.Center)
                            }
                        } else {
                            LazyColumn(
                                contentPadding = PaddingValues(16.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp),
                                modifier = Modifier.fillMaxSize()
                            ) {
                                items(filteredList) { item ->
                                    NotificationItemCard(
                                        item = item,
                                        onClick = {
                                            if (!item.isRead) {
                                                viewModel.markAsRead(listOf(item.id))
                                            }
                                        }
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

private fun Modifier.fillGrid() = this.fillMaxWidth().fillMaxHeight()

@Composable
private fun FilterBar(
    selectedFilter: String,
    onFilterSelected: (String) -> Unit
) {
    val filters = listOf("All", "Alerts", "Subscriptions", "Insights")
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        filters.forEach { filter ->
            val active = selectedFilter == filter
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(20.dp))
                    .background(if (active) ACCENT_GREEN.copy(alpha = 0.2f) else SURFACE_DARK)
                    .border(1.dp, if (active) ACCENT_GREEN else GLASS_BORDER, RoundedCornerShape(20.dp))
                    .clickable { onFilterSelected(filter) }
                    .padding(horizontal = 14.dp, vertical = 8.dp)
            ) {
                Text(
                    text = filter,
                    color = if (active) ACCENT_GREEN else TEXT_PRIMARY,
                    fontSize = 12.sp,
                    fontWeight = if (active) FontWeight.Bold else FontWeight.Normal
                )
            }
        }
    }
}

@Composable
private fun NotificationItemCard(
    item: NotificationDto,
    onClick: () -> Unit
) {
    val opacity = if (item.isRead) 0.5f else 1f
    val (icon, tint) = when (item.notificationType) {
        "alert" -> Icons.Default.Warning to ACCENT_ORANGE
        "subscription" -> Icons.Default.CreditCard to ACCENT_BLUE
        "insight" -> Icons.Default.Lightbulb to ACCENT_GREEN
        else -> Icons.Default.Notifications to ACCENT_PURPLE
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .border(1.dp, GLASS_BORDER, RoundedCornerShape(16.dp))
            .clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            // Icon
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(tint.copy(alpha = 0.15f * opacity)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = tint.copy(alpha = opacity), modifier = Modifier.size(20.dp))
            }

            // Body
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = item.title,
                        color = TEXT_PRIMARY.copy(alpha = opacity),
                        fontSize = 14.sp,
                        fontWeight = if (item.isRead) FontWeight.Medium else FontWeight.Bold
                    )
                    // Unread indicator dot
                    if (!item.isRead) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(ACCENT_GREEN)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = item.body,
                    color = TEXT_SECONDARY.copy(alpha = opacity),
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }
    }
}
