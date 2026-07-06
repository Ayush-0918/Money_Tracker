package com.example.moneytracker.ui.main

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberCoroutineScope
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.moneytracker.di.ServiceLocator
import com.example.moneytracker.ui.dashboard.DashboardScreen
import com.example.moneytracker.ui.dashboard.DashboardViewModel
import com.example.moneytracker.ui.dashboard.DashboardViewModelFactory
import com.example.moneytracker.ui.activity.ActivityViewModel
import com.example.moneytracker.ui.activity.ActivityViewModelFactory
import com.example.moneytracker.ui.analytics.AnalyticsViewModel
import com.example.moneytracker.ui.analytics.AnalyticsViewModelFactory
import com.example.moneytracker.ui.analytics.PredictionViewModel
import com.example.moneytracker.ui.analytics.PredictionViewModelFactory
import com.example.moneytracker.ui.analytics.PredictionScreen
import com.example.moneytracker.ui.budget.BudgetViewModel
import com.example.moneytracker.ui.budget.BudgetViewModelFactory
import com.example.moneytracker.ui.onboarding.LanguageSelectionScreen
import com.example.moneytracker.ui.onboarding.WelcomeScreen
import com.example.moneytracker.ui.permissions.PermissionScreen
import com.example.moneytracker.ui.registration.RegistrationScreen
import com.example.moneytracker.ui.theme.MoneyTrackerTheme
import com.example.moneytracker.util.SecurePrefs
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val securePrefs = SecurePrefs(applicationContext)
        
        // Clear invalid legacy state to force re-login
        val currentToken = securePrefs.getToken()
        if (securePrefs.getUserId() != null && (currentToken == null || currentToken == "mock_premium_token_2024")) {
            android.util.Log.w("MainActivity", "Legacy or mock token detected, clearing to force login")
            securePrefs.saveUserId("")
            securePrefs.saveToken("")
        }

        val repository = ServiceLocator.provideTransactionRepository(applicationContext)

        setContent {
            MoneyTrackerTheme {
                val navController = rememberNavController()

                LaunchedEffect(Unit) {
                    ServiceLocator.authExpiredEvent.collect { expired ->
                        if (expired) {
                            android.util.Log.e("MainActivity", "Session expired, redirecting to login")
                            navController.navigate("language_selection") {
                                popUpTo("dashboard") { inclusive = true }
                            }
                        }
                    }
                }
                
                val startDestination = if (securePrefs.getUserId().isNullOrEmpty()) "language_selection" else "dashboard"

                NavHost(navController = navController, startDestination = startDestination) {
                    composable("language_selection") {
                        LanguageSelectionScreen(onLanguageSelected = { lang ->
                            navController.navigate("onboarding")
                        })
                    }
                    composable("onboarding") {
                        WelcomeScreen(onContinueClicked = { navController.navigate("registration") })
                    }
                    composable("registration") {
                        val scope = rememberCoroutineScope()
                        RegistrationScreen(
                            onRegisterSuccess = { navController.navigate("permissions") },
                            onRegisterClicked = { name, phone -> 
                                android.util.Log.d("MainActivity", "Attempting real registration for $name")
                                scope.launch {
                                    try {
                                        val api = ServiceLocator.provideApiService(applicationContext)
                                        val response = api.register(mapOf("name" to name, "phone_number" to phone))
                                        
                                        if (response.isSuccessful) {
                                            val body = response.body()
                                            val userId = body?.get("user_id") ?: "user_${System.currentTimeMillis()}"
                                            val token = body?.get("access_token")

                                            if (token.isNullOrEmpty()) {
                                                android.util.Log.e("MainActivity", "Registration Success but missing token in response.")
                                                return@launch
                                            }
                                            
                                            android.util.Log.d("MainActivity", "Registration Success: userId=$userId, token=${token.take(5)}...")
                                            
                                            securePrefs.saveUserId(userId)
                                            securePrefs.saveToken(token)
                                            
                                            navController.navigate("permissions")
                                        } else {
                                            android.util.Log.e("MainActivity", "Registration Failed: ${response.code()} ${response.errorBody()?.string()}")
                                            // Do not use mock tokens. Show error.
                                            // Stay on registration screen or handle properly.
                                        }
                                    } catch (e: Exception) {
                                        android.util.Log.e("MainActivity", "Registration Exception", e)
                                        // Do not use mock tokens. Show error.
                                    }
                                }
                            }
                        )
                    }
                    composable("permissions") {
                        val scope = rememberCoroutineScope()
                        val context = applicationContext
                        PermissionScreen(
                            hasPermission = false, 
                            onGrantClicked = { 
                                android.util.Log.d("MainActivity", "User clicked Grant. Attempting Force-Sync before Dashboard.")
                                scope.launch {
                                    try {
                                        val api = ServiceLocator.provideApiService(context)
                                        // Force a registration to get a REAL token if we don't have one
                                        val response = api.register(mapOf("name" to "Demo User", "phone_number" to "9999999999"))
                                        if (response.isSuccessful) {
                                            val body = response.body()
                                            val userId = body?.get("user_id") ?: "user_123"
                                            val token = body?.get("access_token") ?: ""
                                            android.util.Log.d("MainActivity", "Migration Sync Success: $userId")
                                            securePrefs.saveUserId(userId)
                                            securePrefs.saveToken(token)
                                        }
                                    } catch (e: Exception) {
                                        android.util.Log.e("MainActivity", "Migration Sync Failed", e)
                                    }
                                    navController.navigate("dashboard") {
                                        popUpTo("onboarding") { inclusive = true }
                                    }
                                }
                            }
                        )
                    }
                    composable("dashboard") {
                        val userId = securePrefs.getUserId() ?: "default_user"
                        val dashboardFactory = DashboardViewModelFactory(repository, userId)
                        val dashboardViewModel: DashboardViewModel = viewModel(factory = dashboardFactory)
                        
                        val activityFactory = ActivityViewModelFactory(repository)
                        val activityViewModel: ActivityViewModel = viewModel(factory = activityFactory)
                        
                        val budgetRepository = ServiceLocator.provideBudgetRepository(applicationContext)
                        val categoryRepository = ServiceLocator.provideCategoryRepository(applicationContext)
                        val budgetFactory = BudgetViewModelFactory(budgetRepository, categoryRepository)
                        val budgetViewModel: BudgetViewModel = viewModel(factory = budgetFactory)
                        
                        val analyticsFactory = AnalyticsViewModelFactory(repository, userId)
                        val analyticsViewModel: AnalyticsViewModel = viewModel(factory = analyticsFactory)
                        
                        DashboardScreen(
                            viewModel = dashboardViewModel, 
                            activityViewModel = activityViewModel,
                            budgetViewModel = budgetViewModel,
                            analyticsViewModel = analyticsViewModel,
                            onPredictionsClick = { navController.navigate("predictions") }
                        )
                    }
                    composable("predictions") {
                        val predictionRepository = ServiceLocator.providePredictionRepository(applicationContext)
                        val factory = PredictionViewModelFactory(predictionRepository)
                        val predictionViewModel: PredictionViewModel = viewModel(factory = factory)
                        PredictionScreen(
                            viewModel = predictionViewModel,
                            onNavigateBack = { navController.popBackStack() }
                        )
                    }
                }
            }
        }
    }
}
