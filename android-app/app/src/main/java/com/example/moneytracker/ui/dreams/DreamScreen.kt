package com.example.moneytracker.ui.dreams

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
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
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.*
import kotlin.random.Random

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
fun DreamScreen(
    viewModel: DreamViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var showCreateDialog by remember { mutableStateOf(false) }
    var showLogProgressDialog by remember { mutableStateOf<DreamResponseDto?>(null) }
    var selectedDreamDetails by remember { mutableStateOf<DreamResponseDto?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("AI Dream Planner", color = TEXT_PRIMARY, fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = {
                        if (selectedDreamDetails != null) {
                            selectedDreamDetails = null
                        } else {
                            onNavigateBack()
                        }
                    }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = TEXT_PRIMARY)
                    }
                },
                actions = {
                    if (selectedDreamDetails == null && uiState is DreamUiState.Success) {
                        IconButton(onClick = { showCreateDialog = true }) {
                            Icon(Icons.Default.AddCard, contentDescription = "Add Dream", tint = ACCENT_GREEN)
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
                is DreamUiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = ACCENT_GREEN)
                    }
                }
                is DreamUiState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxSize().padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(Icons.Default.Dangerous, contentDescription = null, tint = ACCENT_RED, modifier = Modifier.size(56.dp))
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(state.message, color = TEXT_PRIMARY, fontSize = 14.sp, textAlign = TextAlign.Center)
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(onClick = { viewModel.loadDreams() }, colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)) {
                            Text("Retry", color = Color.White)
                        }
                    }
                }
                is DreamUiState.Success -> {
                    val activeDetails = selectedDreamDetails?.let { details ->
                        state.dreams.find { it.id == details.id }
                    }

                    if (activeDetails != null) {
                        DreamDetailsView(
                            dream = activeDetails,
                            onLogClick = { showLogProgressDialog = activeDetails }
                        )
                    } else {
                        DreamsListView(
                            dreams = state.dreams,
                            onDreamClick = { selectedDreamDetails = it },
                            onLogClick = { showLogProgressDialog = it },
                            onCreateClick = { showCreateDialog = true }
                        )
                    }
                }
            }
        }
    }

    if (showCreateDialog) {
        CreateDreamDialog(
            onDismiss = { showCreateDialog = false },
            onConfirm = { name, target, deadline ->
                viewModel.createDream(name, target, deadline)
                showCreateDialog = false
            }
        )
    }

    if (showLogProgressDialog != null) {
        LogProgressDialog(
            dream = showLogProgressDialog!!,
            onDismiss = { showLogProgressDialog = null },
            onConfirm = { amount ->
                viewModel.logProgress(showLogProgressDialog!!.id, amount)
                showLogProgressDialog = null
            }
        )
    }
}

@Composable
private fun DreamsListView(
    dreams: List<DreamResponseDto>,
    onDreamClick: (DreamResponseDto) -> Unit,
    onLogClick: (DreamResponseDto) -> Unit,
    onCreateClick: () -> Unit
) {
    if (dreams.isEmpty()) {
        Column(
            modifier = Modifier.fillMaxSize().padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text("🔮", fontSize = 64.sp)
            Spacer(modifier = Modifier.height(16.dp))
            Text("AI Dream Planner", color = TEXT_PRIMARY, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Map your financial dreams like buying a MacBook, traveling, or purchasing an EV. " +
                "AI automatically crafts your saving timeline, SIP recommendations, and milestone timeline.",
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
                Text("Add Financial Dream Goal", color = Color.White)
            }
        }
    } else {
        LazyColumn(
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            item {
                Text("YOUR FINANCIAL DREAMS", color = TEXT_SECONDARY, fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
            }
            items(dreams) { dream ->
                DreamCard(
                    dream = dream,
                    onClick = { onDreamClick(dream) },
                    onLogClick = { onLogClick(dream) }
                )
            }
        }
    }
}

@Composable
private fun DreamCard(
    dream: DreamResponseDto,
    onClick: () -> Unit,
    onLogClick: () -> Unit
) {
    val reached = dream.status == "completed"

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .border(1.dp, if (reached) ACCENT_GREEN.copy(alpha = 0.5f) else GLASS_BORDER, RoundedCornerShape(20.dp))
            .clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(dream.name, color = TEXT_PRIMARY, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text("Target: ${dream.targetAmountFormatted}", color = TEXT_SECONDARY, fontSize = 12.sp)
                }
                if (reached) {
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(8.dp))
                            .background(ACCENT_GREEN.copy(alpha = 0.15f))
                            .padding(horizontal = 10.dp, vertical = 4.dp)
                    ) {
                        Text("COMPLETED 🏆", color = ACCENT_GREEN, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                } else {
                    Text("${dream.daysRemaining} days left", color = ACCENT_BLUE, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Progress bar
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                LinearProgressIndicator(
                    progress = (dream.progressPct / 100f).toFloat().coerceIn(0f, 1f),
                    color = if (reached) ACCENT_GREEN else ACCENT_BLUE,
                    trackColor = GLASS_WHITE,
                    modifier = Modifier
                        .weight(1f)
                        .height(6.dp)
                        .clip(RoundedCornerShape(3.dp))
                )
                Text("${dream.progressPct.toInt()}%", color = TEXT_PRIMARY, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Saved: ${dream.currentSavingsFormatted}",
                    color = TEXT_SECONDARY,
                    fontSize = 12.sp
                )
                if (!reached) {
                    TextButton(
                        onClick = onLogClick,
                        colors = ButtonDefaults.textButtonColors(contentColor = ACCENT_GREEN)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Add Savings", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun DreamDetailsView(
    dream: DreamResponseDto,
    onLogClick: () -> Unit
) {
    val reached = dream.status == "completed"

    Box(modifier = Modifier.fillMaxSize()) {
        LazyColumn(
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            // Dream Title Card
            item {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(24.dp))
                        .border(1.dp, GLASS_BORDER, RoundedCornerShape(24.dp)),
                    colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
                ) {
                    Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(dream.name, color = TEXT_PRIMARY, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Column {
                                Text("Target Goal", color = TEXT_SECONDARY, fontSize = 11.sp)
                                Text(dream.targetAmountFormatted, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text("Saved So Far", color = TEXT_SECONDARY, fontSize = 11.sp)
                                Text(dream.currentSavingsFormatted, color = ACCENT_GREEN, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                            }
                        }

                        // Progress ring/bar
                        LinearProgressIndicator(
                            progress = (dream.progressPct / 100f).toFloat().coerceIn(0f, 1f),
                            color = if (reached) ACCENT_GREEN else ACCENT_BLUE,
                            trackColor = GLASS_WHITE,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(6.dp)
                                .clip(RoundedCornerShape(3.dp))
                        )
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Text("${dream.progressPct.toInt()}% reached", color = TEXT_SECONDARY, fontSize = 12.sp)
                            Text(if (reached) "Goal Complete! 🏆" else "${dream.daysRemaining} days remaining", color = ACCENT_BLUE, fontSize = 12.sp)
                        }
                    }
                }
            }

            if (reached) {
                // Celebration Completion certificate card
                item {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(24.dp))
                            .border(2.dp, ACCENT_GREEN, RoundedCornerShape(24.dp)),
                        colors = CardDefaults.cardColors(containerColor = ACCENT_GREEN.copy(alpha = 0.05f))
                    ) {
                        Column(
                            modifier = Modifier.padding(20.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Text("🎓", fontSize = 48.sp)
                            Text(
                                "Dream Achieved!",
                                color = ACCENT_GREEN,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                "Certificate of Accomplishment registered. " +
                                "You successfully met your savings goal for ${dream.name} on deadline schedule.",
                                color = TEXT_PRIMARY,
                                fontSize = 13.sp,
                                textAlign = TextAlign.Center,
                                lineHeight = 18.sp
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(
                                onClick = { /* Share dialog */ },
                                colors = ButtonDefaults.outlinedButtonColors(contentColor = ACCENT_GREEN),
                                border = androidx.compose.foundation.BorderStroke(1.dp, ACCENT_GREEN.copy(alpha = 0.4f))
                            ) {
                                Icon(Icons.Default.Share, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Share Achievement Card")
                            }
                        }
                    }
                }
            } else {
                // Actions & Savings Roadmap
                item {
                    Button(
                        onClick = onLogClick,
                        colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.Add, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Add Savings Progress", color = Color.White)
                    }
                }

                dream.roadmap?.let { rm ->
                    // Forecast card
                    item {
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(20.dp))
                                .border(1.dp, GLASS_BORDER, RoundedCornerShape(20.dp)),
                            colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
                        ) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Icon(Icons.Default.Shield, contentDescription = null, tint = ACCENT_BLUE)
                                        Text("AI Forecast & Risk", color = ACCENT_BLUE, fontSize = 13.sp, fontWeight = FontWeight.Bold)
                                    }
                                    val probColor = try {
                                        Color(android.graphics.Color.parseColor(rm.forecastColor))
                                    } catch (e: Exception) {
                                        ACCENT_GREEN
                                    }
                                    Box(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(probColor.copy(alpha = 0.15f))
                                            .padding(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Text(
                                            "PROBABILITY: ${rm.forecastProbability.uppercase()}",
                                            color = probColor,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                }
                                Text(rm.riskAnalysis, color = TEXT_PRIMARY, fontSize = 12.sp, lineHeight = 17.sp)
                            }
                        }
                    }

                    // savings plan targets
                    item {
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                            Card(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(16.dp))
                                    .border(1.dp, GLASS_BORDER, RoundedCornerShape(16.dp)),
                                colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
                            ) {
                                Column(modifier = Modifier.padding(12.dp)) {
                                    Text("WEEKLY TARGET", color = TEXT_SECONDARY, fontSize = 10.sp)
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(rm.weeklyTargetFormatted, color = TEXT_PRIMARY, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                            Card(
                                modifier = Modifier
                                    .weight(1f)
                                    .clip(RoundedCornerShape(16.dp))
                                    .border(1.dp, GLASS_BORDER, RoundedCornerShape(16.dp)),
                                colors = CardDefaults.cardColors(containerColor = SURFACE_DARK)
                            ) {
                                Column(modifier = Modifier.padding(12.dp)) {
                                    Text("MONTHLY TARGET", color = TEXT_SECONDARY, fontSize = 10.sp)
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(rm.monthlyTargetFormatted, color = TEXT_PRIMARY, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }

                    // SIP Investment suggestions
                    item {
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(20.dp))
                                .border(1.dp, GLASS_BORDER, RoundedCornerShape(20.dp)),
                            colors = CardDefaults.cardColors(containerColor = SURFACE_LIGHT)
                        ) {
                            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                Text("💡 SIP & INVESTMENT RECOMMENDATIONS", color = ACCENT_PURPLE, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                rm.investmentSuggestions.forEach { suggest ->
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Box(modifier = Modifier.size(6.dp).clip(CircleShape).background(ACCENT_PURPLE))
                                        Text(suggest, color = TEXT_PRIMARY, fontSize = 12.sp, lineHeight = 16.sp)
                                    }
                                }
                            }
                        }
                    }

                    // Milestone timeline
                    item {
                        Text("MOTIVATIONAL TIMELINE", color = TEXT_SECONDARY, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                    items(rm.motivationalTimeline) { ms ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(24.dp)
                                    .clip(CircleShape)
                                    .background(if (ms.reached) ACCENT_GREEN.copy(alpha = 0.2f) else GLASS_WHITE),
                                contentAlignment = Alignment.Center
                            ) {
                                if (ms.reached) {
                                    Icon(Icons.Default.Check, contentDescription = null, tint = ACCENT_GREEN, modifier = Modifier.size(14.dp))
                                } else {
                                    Text("${ms.percent}%", fontSize = 8.sp, color = TEXT_SECONDARY)
                                }
                            }
                            Text(
                                text = ms.label,
                                color = if (ms.reached) TEXT_PRIMARY else TEXT_SECONDARY,
                                fontSize = 13.sp,
                                fontWeight = if (ms.reached) FontWeight.Bold else FontWeight.Normal
                            )
                        }
                    }
                }
            }
        }

        // Floating Confetti particles on success
        if (reached) {
            CustomConfettiEffect()
        }
    }
}

// ── Confetti Particle ────────────────────────────────────────────────────────

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

// ── Dialogs ──────────────────────────────────────────────────────────────────

@Composable
fun CreateDreamDialog(
    onDismiss: () -> Unit,
    onConfirm: (String, Double, String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var target by remember { mutableStateOf("") }
    var deadline by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Add Financial Dream Goal", color = TEXT_PRIMARY) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Dream name (e.g. MacBook Air)") },
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
                    value = target,
                    onValueChange = { target = it },
                    label = { Text("Target Amount (₹)") },
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
                    value = deadline,
                    onValueChange = { deadline = it },
                    label = { Text("Deadline date (YYYY-MM-DD)") },
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
                    val amtDouble = target.toDoubleOrNull()
                    if (name.isNotBlank() && amtDouble != null && deadline.isNotBlank()) {
                        onConfirm(name, amtDouble, deadline)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)
            ) {
                Text("Register Dream", color = Color.White)
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
fun LogProgressDialog(
    dream: DreamResponseDto,
    onDismiss: () -> Unit,
    onConfirm: (Double) -> Unit
) {
    var amount by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Log Savings Progress", color = TEXT_PRIMARY) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("How much have you saved towards ${dream.name}?", color = TEXT_SECONDARY, fontSize = 12.sp)
                Spacer(modifier = Modifier.height(4.dp))
                OutlinedTextField(
                    value = amount,
                    onValueChange = { amount = it },
                    label = { Text("Savings Amount (₹)") },
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
                    if (amtDouble != null) {
                        onConfirm(amtDouble)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = ACCENT_GREEN)
            ) {
                Text("Log Progress", color = Color.White)
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
