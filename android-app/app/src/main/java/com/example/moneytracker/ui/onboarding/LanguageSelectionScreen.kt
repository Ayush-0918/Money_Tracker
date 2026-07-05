package com.example.moneytracker.ui.onboarding

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.compose.ui.res.stringResource
import com.example.moneytracker.R
import com.example.moneytracker.ui.components.buttons.PremiumPrimaryButton
import com.example.moneytracker.ui.theme.FintechBlue
import com.example.moneytracker.ui.theme.MoneyTrackerTheme

@Composable
fun LanguageSelectionScreen(
    onLanguageSelected: (String) -> Unit
) {
    val languages = listOf(
        "English" to "en",
        "हिंदी (Hindi)" to "hi",
        "मराठी (Marathi)" to "mr",
        "తెలుగు (Telugu)" to "te",
        "தமிழ் (Tamil)" to "ta"
    )

    var selectedLang by remember { mutableStateOf("en") }

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
                text = stringResource(R.string.language_selection_title),
                style = MaterialTheme.typography.displayLarge.copy(
                    lineHeight = 62.sp,
                    letterSpacing = (-1).sp
                )
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                text = stringResource(R.string.language_selection_subtitle),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(48.dp))

            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                items(languages) { (displayName, code) ->
                    LanguageCard(
                        displayName = displayName,
                        isSelected = selectedLang == code,
                        onClick = { selectedLang = code }
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))
            
            PremiumPrimaryButton(
                text = stringResource(R.string.language_selection_button_continue),
                onClick = { 
                    AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(selectedLang))
                    onLanguageSelected(selectedLang) 
                }
            )
            
            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
fun LanguageCard(
    displayName: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .clip(MaterialTheme.shapes.large),
        color = if (isSelected) FintechBlue.copy(alpha = 0.1f) else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
        shape = MaterialTheme.shapes.large,
        border = if (isSelected) BorderStroke(2.dp, FintechBlue) else null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = displayName,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                color = if (isSelected) FintechBlue else MaterialTheme.colorScheme.onSurface
            )
            if (isSelected) {
                RadioButton(selected = true, onClick = null, colors = RadioButtonDefaults.colors(selectedColor = FintechBlue))
            }
        }
    }
}

@Preview
@Composable
fun LanguageSelectionPreview() {
    MoneyTrackerTheme(darkTheme = true) {
        LanguageSelectionScreen(onLanguageSelected = {})
    }
}
