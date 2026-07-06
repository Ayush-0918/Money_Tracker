package com.example.moneytracker.di

import android.content.Context
import com.example.moneytracker.data.local.AppDatabase
import com.example.moneytracker.data.local.dao.TransactionDao
import com.example.moneytracker.data.local.dao.CacheDao
import com.example.moneytracker.data.remote.AuthInterceptor
import com.example.moneytracker.data.remote.RetrofitClient
import com.example.moneytracker.data.remote.api.ApiService
import com.example.moneytracker.data.repository.TransactionRepositoryImpl
import com.example.moneytracker.domain.repository.TransactionRepository
import com.example.moneytracker.domain.repository.BudgetRepository
import com.example.moneytracker.domain.repository.CategoryRepository
import com.example.moneytracker.data.repository.BudgetRepositoryImpl
import com.example.moneytracker.data.repository.CategoryRepositoryImpl
import com.example.moneytracker.domain.repository.PredictionRepository
import com.example.moneytracker.data.repository.PredictionRepositoryImpl
import com.example.moneytracker.domain.repository.WeeklyReportRepository
import com.example.moneytracker.data.repository.WeeklyReportRepositoryImpl
import com.example.moneytracker.domain.repository.MoneyStoryRepository
import com.example.moneytracker.data.repository.MoneyStoryRepositoryImpl
import com.example.moneytracker.util.SecurePrefs
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow

object ServiceLocator {

    private val _authExpiredEvent = MutableSharedFlow<Boolean>(extraBufferCapacity = 1)
    val authExpiredEvent: SharedFlow<Boolean> = _authExpiredEvent.asSharedFlow()

    fun notifyAuthExpired() {
        _authExpiredEvent.tryEmit(true)
    }

    private var database: AppDatabase? = null
    private var repository: TransactionRepository? = null
    private var budgetRepository: BudgetRepository? = null
    private var categoryRepository: CategoryRepository? = null
    private var predictionRepository: PredictionRepository? = null
    private var weeklyReportRepository: WeeklyReportRepository? = null
    private var moneyStoryRepository: MoneyStoryRepository? = null

    private fun provideDatabase(context: Context): AppDatabase {
        return database ?: synchronized(this) {
            val instance = AppDatabase.getDatabase(context)
            database = instance
            instance
        }
    }

    private fun provideDao(context: Context): TransactionDao {
        return provideDatabase(context).transactionDao()
    }

    private fun provideCacheDao(context: Context): CacheDao {
        return provideDatabase(context).cacheDao()
    }

    private fun provideSecurePrefs(context: Context): SecurePrefs {
        return SecurePrefs(context)
    }

    fun provideApiService(context: Context): ApiService {
        val securePrefs = provideSecurePrefs(context)
        val authInterceptor = AuthInterceptor(securePrefs)
        return RetrofitClient.getApi(authInterceptor)
    }

    fun provideTransactionRepository(context: Context): TransactionRepository {
        return repository ?: synchronized(this) {
            val instance = TransactionRepositoryImpl(
                api = provideApiService(context),
                dao = provideDao(context),
                cacheDao = provideCacheDao(context),
                securePrefs = provideSecurePrefs(context),
                context = context
            )
            repository = instance
            instance
        }
    }

    fun provideBudgetRepository(context: Context): BudgetRepository {
        return budgetRepository ?: synchronized(this) {
            val instance = BudgetRepositoryImpl(
                api = provideApiService(context),
                cacheDao = provideCacheDao(context)
            )
            budgetRepository = instance
            instance
        }
    }

    fun provideCategoryRepository(context: Context): CategoryRepository {
        return categoryRepository ?: synchronized(this) {
            val instance = CategoryRepositoryImpl(provideApiService(context))
            categoryRepository = instance
            instance
        }
    }

    fun providePredictionRepository(context: Context): PredictionRepository {
        return predictionRepository ?: synchronized(this) {
            val instance = PredictionRepositoryImpl(
                api = provideApiService(context),
                securePrefs = provideSecurePrefs(context)
            )
            predictionRepository = instance
            instance
        }
    }

    fun provideWeeklyReportRepository(context: Context): WeeklyReportRepository {
        return weeklyReportRepository ?: synchronized(this) {
            val instance = WeeklyReportRepositoryImpl(
                api = provideApiService(context),
                securePrefs = provideSecurePrefs(context)
            )
            weeklyReportRepository = instance
            instance
        }
    }

    fun provideMoneyStoryRepository(context: Context): MoneyStoryRepository {
        return moneyStoryRepository ?: synchronized(this) {
            val instance = MoneyStoryRepositoryImpl(
                api = provideApiService(context),
                securePrefs = provideSecurePrefs(context)
            )
            moneyStoryRepository = instance
            instance
        }
    }

    // For WorkManager
    fun provideSyncWorkerDependencies(context: Context): SyncWorkerDependencies {
        return SyncWorkerDependencies(
            dao = provideDao(context),
            api = provideApiService(context),
            securePrefs = provideSecurePrefs(context)
        )
    }
}

data class SyncWorkerDependencies(
    val dao: TransactionDao,
    val api: ApiService,
    val securePrefs: SecurePrefs
)
