package com.example.moneytracker.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Category
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.moneytracker.data.remote.dto.CategoryResponse
import java.util.UUID

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CategoryPickerBottomSheet(
    categories: List<CategoryResponse>,
    onCategorySelected: (UUID) -> Unit,
    onDismissRequest: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismissRequest,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = false)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 32.dp, top = 8.dp)
        ) {
            Text(
                text = "Select Category",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )
            
            Divider(modifier = Modifier.padding(bottom = 8.dp))
            
            if (categories.isEmpty()) {
                Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                LazyColumn {
                    val systemCategories = categories.filter { it.system }
                    val customCategories = categories.filter { !it.system }
                    
                    if (systemCategories.isNotEmpty()) {
                        item {
                            Text(
                                "System Categories", 
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                            )
                        }
                        items(systemCategories) { category ->
                            CategoryItem(category = category, onClick = { onCategorySelected(category.id) })
                        }
                    }
                    
                    if (customCategories.isNotEmpty()) {
                        item {
                            Text(
                                "Custom Categories", 
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                            )
                        }
                        items(customCategories) { category ->
                            CategoryItem(category = category, onClick = { onCategorySelected(category.id) })
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CategoryItem(
    category: CategoryResponse,
    onClick: () -> Unit
) {
    // Parse color safely if present
    val iconColor = try {
        if (!category.color.isNullOrEmpty()) {
            Color(android.graphics.Color.parseColor(category.color))
        } else {
            MaterialTheme.colorScheme.primary
        }
    } catch (e: Exception) {
        MaterialTheme.colorScheme.primary
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = Icons.Default.Category, // Fallback, could load via URL or mapping if we had icons
            contentDescription = category.display_name,
            tint = iconColor,
            modifier = Modifier.size(24.dp)
        )
        Spacer(modifier = Modifier.width(16.dp))
        Text(text = category.display_name, style = MaterialTheme.typography.bodyLarge)
    }
}
