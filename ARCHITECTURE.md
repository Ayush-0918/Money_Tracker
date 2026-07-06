# Money Tracker AI — Architecture Documentation

## Overview

Money Tracker AI is a FastAPI-based personal finance backend with AI-powered transaction categorization, budgeting, subscriptions, reporting, and a financial coach. It is designed for production reliability with provider failover, caching, circuit breakers, structured logging, and monitoring.

---

## High-Level Architecture

```
Android App (Kotlin)
    │
    │  JWT-authenticated REST calls
    ▼
┌─────────────────────────────────────┐
│        FastAPI Application          │
│  (uvicorn / gunicorn multi-worker)  │
│                                     │
│  ┌───────────┐  ┌────────────────┐  │
│  │ API Layer │  │ Rate Limiter   │  │
│  │  Routes   │  │   (slowapi)    │  │
│  └─────┬─────┘  └────────────────┘  │
│        │                            │
│  ┌─────▼─────────────────────────┐  │
│  │       Service Layer            │  │
│  │ TransactionService             │  │
│  │ ReportService                  │  │
│  │ BudgetService                  │  │
│  │ AIService + ProviderManager    │  │
│  └─────┬─────────────────────────┘  │
│        │                            │
│  ┌─────▼─────┐   ┌──────────────┐  │
│  │ SQLAlchemy│   │  Celery      │  │
│  │ (Async)   │   │  Worker      │  │
│  └─────┬─────┘   └──────┬───────┘  │
└────────┼────────────────┼───────────┘
         │                │
    ┌────▼────┐      ┌────▼────┐
    │Postgres │      │  Redis  │
    │  (DB)   │      │(Broker) │
    └─────────┘      └─────────┘
```

---

## AI Provider Chain

Every categorization request cascades through providers until one succeeds:

```
Transaction Input
      │
      ▼
┌─────────────────────────────────┐
│  Pre-Classification Rules       │  ← Keyword matching (Income, EMI, Salary)
│  (no network call, instant)     │
└──────────────┬──────────────────┘
               │ no match
               ▼
┌─────────────────────────────────┐
│  In-Memory Cache                │  ← Merchant key → category (LRU-style)
└──────────────┬──────────────────┘
               │ cache miss
               ▼
┌─────────────────────────────────┐
│  PostgreSQL Cache               │  ← ai_categorization_caches table
│  (ai_categorization_caches)     │
└──────────────┬──────────────────┘
               │ cache miss
               ▼
┌─────────────────────────────────┐
│  ProviderManager                │
│  ┌─────────────────────────┐    │
│  │ 1. GroqProvider         │    │  ← llama-3.3-70b-versatile (primary)
│  │    Circuit Breaker      │    │
│  ├─────────────────────────┤    │
│  │ 2. GitHubModelsProvider │    │  ← openai/gpt-4.1 (secondary)
│  │    Circuit Breaker      │    │
│  ├─────────────────────────┤    │
│  │ 3. RuleEngineProvider   │    │  ← DB merchant rules (offline fallback)
│  └─────────────────────────┘    │
└─────────────────────────────────┘
```

---

## Database Schema

### Core Tables

| Table | Purpose |
|---|---|
| `users` | Auth and profile |
| `transactions` | All financial transactions |
| `categories` | Expense categories (system + custom) |
| `merchants` | Normalized merchant entities |
| `merchant_aliases` | Fuzzy merchant name → merchant_id mapping |
| `merchant_rules` | Merchant → category confidence rules |
| `budgets` | Monthly budget limits per category |
| `subscriptions` | Recurring subscription tracking |
| `learning_events` | Audit log of manual category corrections |
| `ai_categorization_caches` | Persistent merchant → category AI result cache |

### Alembic Migrations (in order)

| Migration | Description |
|---|---|
| `0001_initial` | Initial schema (users, transactions, categories) |
| `0002_merchants` | Merchant normalization tables |
| `0003_subscriptions` | Subscription tracking |
| `0004_budgets` | Budget management |
| `0005_learning` | Learning events and feedback loop |
| `0006_ai_cache` | AI categorization result cache |

---

## API Endpoints

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register user with phone number |
| POST | `/auth/login` | Login and receive JWT tokens |
| POST | `/auth/refresh` | Refresh access token |

### Transactions
| Method | Path | Description |
|---|---|---|
| GET | `/transactions/{user_id}` | List transactions (paginated) |
| POST | `/transactions/{user_id}` | Add a new transaction |
| PUT | `/transactions/{tx_id}/category` | Update category (triggers learning) |

### Budgets
| Method | Path | Description |
|---|---|---|
| GET | `/budgets/{user_id}` | Get all budgets |
| POST | `/budgets/{user_id}` | Create a budget |
| PUT | `/budgets/{user_id}/{category_id}` | Update budget limit |
| DELETE | `/budgets/{user_id}/{category_id}` | Delete a budget |

### Reports
| Method | Path | Description |
|---|---|---|
| GET | `/reports/monthly/{user_id}` | Monthly expense report |
| GET | `/reports/subscriptions/{user_id}` | Active subscriptions list |
| GET | `/reports/weekly/{user_id}` | Last 7 days spending chart |
| **GET** | **`/reports/coach/{user_id}`** | **AI Financial Coach insights** |

### Admin
| Method | Path | Description |
|---|---|---|
| GET | `/admin/duplicates` | List duplicate merchants |
| POST | `/admin/merge-merchant` | Merge two merchants |

---

## AI Financial Coach (`GET /reports/coach/{user_id}`)

The coach endpoint returns:
```json
{
  "insights": [
    "You spent 18% more on food than last month.",
    "Your top expense was ₹4,500 at Swiggy. Try reducing orders next week."
  ],
  "active_subscriptions": 5,
  "financial_health_score": 72,
  "budget_runout_days": 6
}
```

### Health Score Formula
```
base_score         = 100
- exceeded_budgets × 15
- active_subs      ×  5
- spend_increased  ? 10 : 0

health_score = clamp(base_score, 10, 100)
```

---

## DevOps Stack

### Docker Compose Services
| Service | Image | Role |
|---|---|---|
| `db` | postgres:15-alpine | Primary database |
| `redis` | redis:7-alpine | Cache & Celery broker |
| `web` | local Dockerfile | FastAPI REST API |
| `worker` | local Dockerfile | Celery background tasks |

### GitHub Actions CI Pipeline
Triggered on every push/PR to `main`:
1. ✅ Install dependencies
2. ✅ Lint with `black` (format check)
3. ✅ Lint with `flake8` (syntax errors)
4. ✅ Run `pytest` (89+ tests)

### Monitoring
- **Sentry SDK** — initialized at startup if `SENTRY_DSN` is set
- Captures all unhandled exceptions with full request context
- Environment-aware (`development` vs `production`)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL async connection string |
| `JWT_SECRET_KEY` | ✅ | — | Minimum 32-char secret for JWT signing |
| `ENVIRONMENT` | ✅ | `development` | `development` or `production` |
| `GROQ_API_KEY` | ⭐ | — | Primary AI provider key |
| `GITHUB_TOKEN` | ⭐ | — | Secondary AI provider key |
| `SENTRY_DSN` | ☑️ | None | Sentry error tracking DSN |
| `REDIS_URL` | ☑️ | `redis://localhost:6379/0` | Redis URL |
| `CELERY_BROKER_URL` | ☑️ | `redis://localhost:6379/0` | Celery message broker |
| `AI_TIMEOUT_GROQ` | ☑️ | `10.0` | Groq request timeout (seconds) |
| `AI_TIMEOUT_GITHUB` | ☑️ | `10.0` | GitHub Models timeout (seconds) |

---

## Project Structure

```
Money_Tracker/
├── app/
│   ├── api/              # Route handlers
│   │   ├── auth.py
│   │   ├── budgets.py
│   │   ├── reports.py    # includes /coach endpoint
│   │   ├── transactions.py
│   │   └── admin.py
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response DTOs
│   ├── services/         # Business logic
│   │   ├── ai_service.py   # ProviderManager + AIService
│   │   ├── report_service.py
│   │   └── transaction_service.py
│   ├── worker.py         # Celery task definitions
│   ├── config.py         # Settings (pydantic-settings)
│   ├── database.py       # AsyncSession factory
│   └── main.py           # App factory, middleware, startup
├── alembic/              # Database migrations
├── tests/                # Pytest test suite (89+ tests)
├── android-app/          # Kotlin Android client
├── Dockerfile            # Multi-stage container build
├── docker-compose.yml    # Full dev/prod stack
├── .github/workflows/    # GitHub Actions CI
│   └── ci.yml
├── ARCHITECTURE.md       # This file
└── requirements.txt
```
