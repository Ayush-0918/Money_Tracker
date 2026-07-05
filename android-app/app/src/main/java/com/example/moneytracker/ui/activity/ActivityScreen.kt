package com.example.moneytracker.ui.activity

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import com.example.moneytracker.R
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import com.example.moneytracker.ui.theme.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun ActivityScreen(
    viewModel: ActivityViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    // Detect when user scrolls near the end
    val shouldLoadMore = remember {
        derivedStateOf {
            val totalItems = listState.layoutInfo.totalItemsCount
            val lastVisible = listState.layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
            lastVisible >= totalItems - 5
        }
    }

    LaunchedEffect(shouldLoadMore.value) {
        if (shouldLoadMore.value) {
            viewModel.loadNextPage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.activity_title), style = MaterialTheme.typography.titleLarge) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = FintechBackground,
                    titleContentColor = Color.White
                )
            )
        },
        containerColor = FintechBackground
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Search Bar
            OutlinedTextField(
                value = uiState.searchQuery,
                onValueChange = { viewModel.onSearchQueryChanged(it) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                placeholder = { Text(stringResource(R.string.activity_search_placeholder), color = Color.Gray) },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search", tint = Color.Gray) },
                trailingIcon = {
                    if (uiState.searchQuery.isNotEmpty()) {
                        IconButton(onClick = { viewModel.onSearchQueryChanged("") }) {
                            Icon(Icons.Default.Close, contentDescription = stringResource(R.string.activity_search_clear), tint = Color.Gray)
                        }
                    }
                },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = FintechBlue,
                    unfocusedBorderColor = FintechCard,
                    focusedContainerColor = FintechCard,
                    unfocusedContainerColor = FintechCard,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                ),
                shape = RoundedCornerShape(16.dp)
            )

            // Filter Chips
            ScrollableTabRow(
                selectedTabIndex = 0,
                modifier = Modifier.padding(bottom = 8.dp),
                containerColor = FintechBackground,
                edgePadding = 16.dp,
                indicator = {},
                divider = {}
            ) {
                FilterChipItem(
                    text = stringResource(R.string.activity_filter_all),
                    selected = uiState.categoryFilter == null,
                    onClick = { viewModel.onCategoryFilterChanged(null) }
                )
                FilterChipItem(
                    text = stringResource(R.string.activity_filter_food),
                    selected = uiState.categoryFilter == "Food",
                    onClick = { viewModel.onCategoryFilterChanged("Food") }
                )
                FilterChipItem(
                    text = stringResource(R.string.activity_filter_transport),
                    selected = uiState.categoryFilter == "Transport",
                    onClick = { viewModel.onCategoryFilterChanged("Transport") }
                )
                FilterChipItem(
                    text = stringResource(R.string.activity_filter_shopping),
                    selected = uiState.categoryFilter == "Shopping",
                    onClick = { viewModel.onCategoryFilterChanged("Shopping") }
                )
            }

            if (uiState.isLoading && uiState.transactions.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = FintechBlue)
                }
            } else if (!uiState.isLoading && uiState.transactions.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(stringResource(R.string.activity_no_transactions), color = Color.Gray, style = MaterialTheme.typography.bodyLarge)
                }
            } else {
                val grouped = uiState.transactions.groupBy { 
                    // simple parsing of "2 min ago" or timestamps to Month/Year is tricky since backend returns mixed strings.
                    // Assuming we do a basic grouping for demonstration.
                    "Recent" 
                }

                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    grouped.forEach { (month, transactions) ->
                        stickyHeader {
                            Text(
                                text = month,
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(FintechBackground)
                                    .padding(vertical = 8.dp)
                            )
                        }

                        items(transactions, key = { it.id }) { tx ->
                            ActivityTransactionItem(tx)
                            Spacer(modifier = Modifier.height(12.dp))
                        }
                    }

                    if (uiState.isPaginating) {
                        item {
                            Box(modifier = Modifier.fillMaxWidth().padding(16.dp), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(color = FintechBlue, modifier = Modifier.size(24.dp))
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FilterChipItem(text: String, selected: Boolean, onClick: () -> Unit) {
    Surface(
        onClick = onClick,
        modifier = Modifier.padding(end = 8.dp),
        shape = RoundedCornerShape(20.dp),
        color = if (selected) FintechBlue else FintechCard,
    ) {
        Text(
            text = text,
            color = if (selected) Color.White else Color.Gray,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            style = MaterialTheme.typography.labelLarge
        )
    }
}

@Composable
fun ActivityTransactionItem(tx: TransactionItemDto) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(FintechCard)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(FintechBlue.copy(alpha = 0.2f)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = tx.merchant.firstOrNull()?.uppercase() ?: "?",
                color = FintechBlue,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
        }
        Spacer(modifier = Modifier.width(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(text = tx.merchant, style = MaterialTheme.typography.bodyLarge, color = Color.White)
            Text(text = tx.category ?: "Uncategorized", style = MaterialTheme.typography.labelMedium, color = Color.Gray)
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(
                text = tx.amount_formatted,
                style = MaterialTheme.typography.titleMedium,
                color = Color.White
            )
            Text(
                text = tx.date_formatted,
                style = MaterialTheme.typography.labelSmall,
                color = FintechSecondary
            )
        }
    }
}
