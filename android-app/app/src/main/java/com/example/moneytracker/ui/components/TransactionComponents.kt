package com.example.moneytracker.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.moneytracker.data.remote.dto.TransactionItemDto
import com.example.moneytracker.ui.components.cards.PremiumCard
import com.example.moneytracker.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TransactionRowItem(
    tx: TransactionItemDto,
    onCategorize: (String) -> Unit,
) {
    val dismissState = rememberSwipeToDismissBoxState(
        confirmValueChange = {
            when (it) {
                SwipeToDismissBoxValue.StartToEnd -> {
                    onCategorize(tx.id)
                    false
                }
                SwipeToDismissBoxValue.EndToStart -> {
                    // TODO: Handle delete
                    false
                }
                else -> false
            }
        }
    )

    SwipeToDismissBox(
        state = dismissState,
        backgroundContent = {
            val color = when (dismissState.dismissDirection) {
                SwipeToDismissBoxValue.StartToEnd -> FintechBlue
                SwipeToDismissBoxValue.EndToStart -> FintechRed
                else -> Color.Transparent
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(24.dp))
                    .background(color)
                    .padding(horizontal = 24.dp),
                contentAlignment = if (dismissState.dismissDirection == SwipeToDismissBoxValue.StartToEnd) Alignment.CenterStart else Alignment.CenterEnd
            ) {
                Icon(
                    if (dismissState.dismissDirection == SwipeToDismissBoxValue.StartToEnd) Icons.Default.Edit else Icons.Default.Delete,
                    contentDescription = null,
                    tint = Color.White
                )
            }
        },
        enableDismissFromStartToEnd = true,
        enableDismissFromEndToStart = true
    ) {
        PremiumCard(
            containerColor = FintechSurfaceVariant,
            padding = 16.dp,
            cornerRadius = 24.dp
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                MerchantLogo(tx.merchant, tx.category)
                Spacer(modifier = Modifier.width(16.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        tx.merchant,
                        style = MaterialTheme.typography.bodyLarge.copy(fontWeight = FontWeight.SemiBold),
                        color = Color.White
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            tx.date,
                            style = MaterialTheme.typography.labelSmall,
                            color = FintechSecondary
                        )
                        if (tx.category != null) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Box(modifier = Modifier.size(3.dp).clip(CircleShape).background(FintechSecondary))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                tx.category,
                                style = MaterialTheme.typography.labelSmall,
                                color = FintechBlue
                            )
                        }
                    }
                }
                Text(
                    tx.amount_formatted,
                    style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                    color = Color.White
                )
            }
        }
    }
}

@Composable
fun MerchantLogo(name: String, category: String?) {
    val initials = name.take(1).uppercase()
    val bgColor = when (category?.lowercase()) {
        "food" -> FintechOrange
        "shopping" -> FintechPurple
        "bills" -> FintechBlue
        "travel" -> FintechGreen
        "entertainment" -> FintechPink
        else -> FintechIndigo
    }

    Box(
        modifier = Modifier
            .size(48.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(bgColor.copy(alpha = 0.15f)),
        contentAlignment = Alignment.Center
    ) {
        Text(
            initials,
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.Bold,
                color = bgColor
            )
        )
    }
}
