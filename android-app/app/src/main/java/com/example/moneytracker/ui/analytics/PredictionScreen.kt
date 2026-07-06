package com.example.moneytracker.ui.analytics

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moneytracker.data.remote.dto.AIPredictionResponseDto
import com.example.moneytracker.data.remote.dto.BudgetPredictionDto
import com.example.moneytracker.data.remote.dto.CashFlowForecastDto
import com.example.moneytracker.data.remote.dto.ExpenseForecastDto
import com.example.moneytracker.data.remote.dto.SalaryPredictionDto
import com.example.moneytracker.ui.components.ShimmerEffect
import com.example.moneytracker.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PredictionScreen(
    viewModel: PredictionViewModel,
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = FintechSurface,
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(
                        "AI Projections",
                        style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold)
                    )
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = Color.Transparent,
                    titleContentColor = Color.White
                ),
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(CircleShape)
                                .background(FintechSurfaceBright),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Default.ArrowBack, contentDescription = "Back", modifier = Modifier.size(20.dp), tint = Color.White)
                        }
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.refreshPredictions() }) {
                        Box(
                            modifier = Modifier
                                .size(36.dp)
                                .clip(CircleShape)
                                .background(FintechSurfaceBright),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Default.Refresh, contentDescription = "Refresh", modifier = Modifier.size(20.dp), tint = Color.White)
                        }
                    }
                }
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            when (val state = uiState) {
                is PredictionUiState.Loading -> PredictionLoadingState()
                is PredictionUiState.Error -> PredictionErrorState(
                    message = state.message,
                    onRetry = { viewModel.loadPredictions() }
                )
                is PredictionUiState.Success -> PredictionSuccessState(
                    predictions = state.predictions
                )
            }
        }
    }
}

@Composable
fun PredictionSuccessState(predictions: AIPredictionResponseDto) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(top = 16.dp, start = 20.dp, end = 20.dp, bottom = 40.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // AI Insights Card
        item {
            AIInsightsSection(insights = predictions.ai_insights)
        }

        // Salary Detection Card (if detected)
        item {
            SalaryPredictionSection(salary = predictions.salary_prediction)
        }

        // Expense Forecast
        item {
            ExpenseForecastSection(expense = predictions.expense_forecast)
        }

        // Budget Risk Alerts
        item {
            BudgetPredictionSection(budgets = predictions.budget_forecast)
        }

        // Cash Flow Timeline
        item {
            CashFlowSection(cashFlow = predictions.cash_flow_forecast)
        }
    }
}

@Composable
fun AIInsightsSection(insights: List<String>) {
    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("AI FINANCIAL COACH", style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold, letterSpacing = 1.sp), color = FintechSecondary)
        
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(24.dp))
                .background(Brush.verticalGradient(DarkGlassGradient))
                .border(1.dp, GlassBorder, RoundedCornerShape(24.dp))
                .padding(20.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                insights.forEach { insight ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.Top
                    ) {
                        Icon(
                            imageVector = Icons.Default.Lightbulb,
                            contentDescription = null,
                            tint = FintechOrange,
                            modifier = Modifier
                                .size(20.dp)
                                .offset(y = 2.dp)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = insight,
                            style = MaterialTheme.typography.bodyMedium.copy(lineHeight = 20.sp),
                            color = Color.White
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun SalaryPredictionSection(salary: SalaryPredictionDto) {
    if (salary.is_detected && salary.expected_amount != null) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(24.dp))
                .background(Brush.horizontalGradient(SuccessGradient))
                .padding(20.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        "SALARY DETECTED",
                        style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Bold, letterSpacing = 1.sp),
                        color = FintechBlack.copy(alpha = 0.6f)
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Expected on ${salary.expected_date ?: "N/A"}",
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium),
                        color = FintechBlack
                    )
                }
                Text(
                    "₹${salary.expected_amount}",
                    style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.ExtraBold),
                    color = FintechBlack
                )
            }
        }
    }
}

@Composable
fun ExpenseForecastSection(expense: ExpenseForecastDto) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("EXPENSE FORECASTS", style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold, letterSpacing = 1.sp), color = FintechSecondary)
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            ForecastCard(
                title = "Next Day",
                amount = "₹${expense.next_day}",
                modifier = Modifier.weight(1f)
            )
            ForecastCard(
                title = "Next Week",
                amount = "₹${expense.next_week}",
                modifier = Modifier.weight(1f)
            )
            ForecastCard(
                title = "Next Month",
                amount = "₹${expense.next_month}",
                modifier = Modifier.weight(1f)
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(24.dp))
                .background(FintechSurfaceBright)
                .border(1.dp, GlassBorder, RoundedCornerShape(24.dp))
                .padding(20.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(
                    "Predicted Category Breakdown",
                    style = MaterialTheme.typography.titleSmall.copy(fontWeight = FontWeight.Bold),
                    color = Color.White
                )
                
                expense.category_forecast.forEach { (catName, amt) ->
                    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(catName, style = MaterialTheme.typography.bodyMedium, color = Color.White)
                            Text("₹$amt", style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold), color = Color.White)
                        }
                        
                        LinearProgressIndicator(
                            progress = 1.0f,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(6.dp)
                                .clip(CircleShape),
                            color = FintechBlue,
                            trackColor = FintechSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ForecastCard(title: String, amount: String, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(20.dp))
            .background(FintechSurfaceBright)
            .border(1.dp, GlassBorder, RoundedCornerShape(20.dp))
            .padding(16.dp)
    ) {
        Column {
            Text(title, style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
            Spacer(modifier = Modifier.height(4.dp))
            Text(amount, style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold), color = Color.White)
        }
    }
}

@Composable
fun BudgetPredictionSection(budgets: List<BudgetPredictionDto>) {
    val atRisk = budgets.filter { it.will_exceed }
    if (atRisk.isNotEmpty()) {
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("BUDGET RISK WARNINGS", style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold, letterSpacing = 1.sp), color = FintechRed)
            
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                atRisk.forEach { budget ->
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(20.dp))
                            .background(Brush.horizontalGradient(DangerGradient).copy(alpha = 0.15f))
                            .border(1.dp, FintechRed.copy(alpha = 0.3f), RoundedCornerShape(20.dp))
                            .padding(16.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Default.Warning, contentDescription = null, tint = FintechRed, modifier = Modifier.size(24.dp))
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text(
                                    "${budget.category_name} budget at risk",
                                    style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                                    color = Color.White
                                )
                                Text(
                                    "Projected to exceed by ₹${budget.predicted_spend}. Exceeds in ~${budget.estimated_days_remaining} days.",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = FintechSecondary
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CashFlowSection(cashFlow: CashFlowForecastDto) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("30-DAY CASH FLOW ESTIMATE", style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold, letterSpacing = 1.sp), color = FintechSecondary)
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(20.dp))
                    .background(FintechSurfaceBright)
                    .border(1.dp, GlassBorder, RoundedCornerShape(20.dp))
                    .padding(16.dp)
            ) {
                Column {
                    Text("Est. Inflow", style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("₹${cashFlow.estimated_inflow}", style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold), color = FintechGreen)
                }
            }
            Box(
                modifier = Modifier
                    .weight(1f)
                    .clip(RoundedCornerShape(20.dp))
                    .background(FintechSurfaceBright)
                    .border(1.dp, GlassBorder, RoundedCornerShape(20.dp))
                    .padding(16.dp)
            ) {
                Column {
                    Text("Est. Outflow", style = MaterialTheme.typography.labelSmall, color = FintechSecondary)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("₹${cashFlow.estimated_outflow}", style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold), color = FintechRed)
                }
            }
        }

        if (cashFlow.negative_balance_risk_dates.isNotEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(20.dp))
                    .background(FintechRed.copy(alpha = 0.1f))
                    .border(1.dp, FintechRed.copy(alpha = 0.2f), RoundedCornerShape(20.dp))
                    .padding(16.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Error, contentDescription = null, tint = FintechRed, modifier = Modifier.size(20.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "Risk of negative balance on: ${cashFlow.negative_balance_risk_dates.joinToString(", ")}",
                        style = MaterialTheme.typography.labelMedium,
                        color = FintechRed
                    )
                }
            }
        }
    }
}

@Composable
fun PredictionLoadingState() {
    Column(
        modifier = Modifier.padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(140.dp).clip(RoundedCornerShape(24.dp)))
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(80.dp).clip(RoundedCornerShape(20.dp)))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            repeat(3) {
                ShimmerEffect(modifier = Modifier.weight(1f).height(100.dp).clip(RoundedCornerShape(20.dp)))
            }
        }
        ShimmerEffect(modifier = Modifier.fillMaxWidth().height(160.dp).clip(RoundedCornerShape(24.dp)))
    }
}

@Composable
fun PredictionErrorState(message: String, onRetry: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Icon(Icons.Default.Warning, contentDescription = null, tint = FintechRed, modifier = Modifier.size(48.dp))
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = FintechSecondary,
                textAlign = TextAlign.Center
            )
            Button(
                onClick = onRetry,
                colors = ButtonDefaults.buttonColors(containerColor = FintechBlue, contentColor = Color.White),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Retry")
            }
        }
    }
}
