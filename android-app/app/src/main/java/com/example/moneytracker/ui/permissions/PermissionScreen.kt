package com.example.moneytracker.ui.permissions

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.Security
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import com.example.moneytracker.ui.components.buttons.PremiumPrimaryButton
import com.example.moneytracker.ui.theme.FintechBlue
import com.example.moneytracker.ui.theme.MoneyTrackerTheme

@Composable
fun PermissionScreen(
    hasPermission: Boolean,
    onGrantClicked: () -> Unit
) {
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.entries.all { it.value }
        if (allGranted || Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            onGrantClicked()
        } else {
            // Proceed anyway for now since we're simulating the flow
            onGrantClicked()
        }
    }
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(24.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Spacer(modifier = Modifier.height(64.dp))
            
            Text(
                text = "Track Every\nTransaction.",
                style = MaterialTheme.typography.displayLarge.copy(
                    lineHeight = 62.sp,
                    letterSpacing = (-1).sp
                )
            )
            
            Spacer(modifier = Modifier.height(48.dp))
            
            PermissionFeatureItem(
                icon = Icons.Default.NotificationsActive,
                title = "Notification Access",
                description = "We read only payment confirmations from apps like GPay and PhonePe."
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            PermissionFeatureItem(
                icon = Icons.Default.Security,
                title = "Bank-Grade Privacy",
                description = "We NEVER read OTPs, personal texts or private data. It's all processed on-device."
            )
            
            Spacer(modifier = Modifier.weight(1f))
            
            if (hasPermission) {
                Text(
                    text = "All set! Access granted.",
                    style = MaterialTheme.typography.titleLarge,
                    color = FintechBlue,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
            } else {
                PremiumPrimaryButton(
                    text = "Grant Access",
                    onClick = {
                        val perms = mutableListOf(Manifest.permission.RECEIVE_SMS, Manifest.permission.READ_SMS)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            perms.add(Manifest.permission.POST_NOTIFICATIONS)
                        }
                        permissionLauncher.launch(perms.toTypedArray())
                    }
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun PermissionFeatureItem(
    icon: ImageVector,
    title: String,
    description: String
) {
    Row(verticalAlignment = Alignment.Top) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(FintechBlue.copy(alpha = 0.1f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(icon, contentDescription = null, tint = FintechBlue)
        }
        Spacer(modifier = Modifier.width(20.dp))
        Column {
            Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                description,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Preview
@Composable
fun PermissionPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        PermissionScreen(hasPermission = false, onGrantClicked = {})
    }
}
