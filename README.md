# Money Tracker AI

Production-quality FastAPI backend for the Money Tracker Android app, powered by GitHub Models.

Receives Android payment notifications → filters OTP → parses transactions → **AI Categorization (GPT-4o)** → stores in PostgreSQL (Supabase) → serves spending reports & insights.

---

## Folder Structure

```
money_tracker/
├── app/
│   ├── main.py               # FastAPI app factory
│   ├── config.py             # Pydantic Settings (reads .env)
│   ├── database.py           # Async SQLAlchemy engine + session
│   ├── api/
│   │   ├── deps.py           # Shared dependencies (auth, DB)
│   │   ├── auth.py           # POST /auth/register
│   │   ├── transactions.py   # POST /transactions
│   │   └── reports.py        # GET /reports/monthly, /subscriptions
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic
│   └── utils/
│       ├── otp_filter.py     # SECURITY: OTP/sensitive content filter
│       ├── parser.py         # Amount/merchant/date extraction
│       ├── security.py       # JWT create/verify
│       └── logging_config.py
├── tests/
│   ├── test_otp_filter.py    # Unit tests (31 test cases)
│   ├── test_parser.py        # Parser tests (22 test cases)
│   └── test_api.py           # Integration tests
├── alembic/                  # Database migrations
├── supabase_setup.sql        # Supabase dashboard SQL
├── requirements.txt
└── .env.example
```

---

## Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → New Project
2. **SQL Editor** → New Query → paste contents of `supabase_setup.sql` → Run
3. **Settings → Database → Connection string (URI)** → copy the URI

---

## Step 2 — Local Setup

```bash
# 1. Clone and enter project
cd /Users/aayu/Desktop/Money_Tracker

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env — fill in DATABASE_URL and generate JWT_SECRET_KEY:
python3 -c "import secrets; print(secrets.token_hex(32))"

# ── GitHub Models ─────────────────────────────────────────────────────────────
# Get token from: https://github.com/marketplace/models
GITHUB_TOKEN=your_github_pat
GITHUB_MODEL=openai/gpt-4o
GITHUB_MODELS_ENDPOINT=https://models.inference.ai.azure.com
AI_ENABLED=true

# 5. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Step 3 — Run Tests

```bash
# All tests
pytest tests/ -v

# OTP filter tests only (critical security tests)
pytest tests/test_otp_filter.py -v

# Parser tests only
pytest tests/test_parser.py -v

# With coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Step 4 — Test with curl

### Register a user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "name": "Aayu",
    "language_preference": "hi"
  }'

# Response:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   "user_id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Aayu"
# }
```

### Post a payment notification
```bash
TOKEN="eyJ..."        # from register response
USER_ID="550e..."     # from register response

curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "raw_text": "Rs.499 debited from your account for Netflix via UPI.",
    "source": "notification"
  }'
```

### Test OTP rejection
```bash
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'$USER_ID'",
    "raw_text": "Your OTP is 123456. Valid for 10 minutes. Do not share.",
    "source": "sms"
  }'
# Expect: HTTP 400 with error "OTP_REJECTED"
```

### Get monthly report
```bash
curl http://localhost:8000/reports/monthly/$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Get subscription report
```bash
curl http://localhost:8000/reports/subscriptions/$USER_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Health check
```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "1.0.0"}
```

---

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | ❌ | Register user, get JWT token |
| POST | `/transactions` | ✅ JWT | Submit payment notification |
| GET | `/predictions` | ✅ JWT | Get AI financial forecasts (PR-15) |
| POST | `/predictions/refresh` | ✅ JWT | Force refresh AI forecasts |
| GET | `/reports/monthly/{user_id}` | ✅ JWT | Current month spending report |
| GET | `/reports/subscriptions/{user_id}` | ✅ JWT | Subscription health report |
| GET | `/health` | ❌ | Liveness probe |

---

## Security Architecture

```
Android App
    │
    │  POST /transactions { raw_text, user_id, source }
    ▼
┌─────────────────────────────────────────┐
│  JWT Auth Middleware (deps.py)          │  ← 401 if token invalid/missing
│  Pydantic Input Validation              │  ← 422 if schema mismatch
│  user_id ownership check               │  ← 403 if token ≠ body user_id
└────────────────┬────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │  OTP Filter (FIRST)     │  ← 400 if OTP/PIN/CVV detected — NOTHING saved
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  Text Parser            │  ← 422 if amount/merchant not found
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  SQLAlchemy ORM Save    │  ← Parameterized queries (no SQL injection)
    │  (NUMERIC amount)       │  ← Decimal precision, not float
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────┐
    │  Recurring Detection    │  ← Upsert subscription if pattern found
    └─────────────────────────┘
```

---

## Phase 3 Roadmap (Future)

| Feature | Status |
|---------|--------|
| AI category assignment | `category` column is NULL, ready for population |
| WhatsApp report sending | Data is ready; Twilio/WhatsApp Business API integration next |
| Redis rate limiting | Currently in-memory (slowapi default) |
| Refresh tokens | Single JWT for now |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` (from Supabase) |
| `JWT_SECRET_KEY` | ✅ | Min 32 chars. Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | ❌ | Default: `HS256` |
| `JWT_EXPIRE_MINUTES` | ❌ | Default: `10080` (7 days) |
| `ALLOWED_ORIGINS` | ❌ | Comma-separated CORS origins. Default: `http://localhost:3000` |
| `RATE_LIMIT_PER_MINUTE` | ❌ | POST /transactions limit per user. Default: `20` |
| `ENVIRONMENT` | ❌ | `development` (auto-creates tables) or `production` |
| `GROQ_API_KEY` | ❌ | API Key for Groq Cloud. Enabled when provided. |
| `GROQ_MODEL` | ❌ | Default: `llama-3.3-70b-versatile` |
| `GITHUB_TOKEN` | ❌ | Token for GitHub Models. Enabled when provided. |
| `GITHUB_MODEL` | ❌ | Default: `openai/gpt-5` |
| `AI_TIMEOUT_GROQ` | ❌ | Timeout in seconds for Groq API calls. Default: `10.0` |
| `AI_TIMEOUT_GITHUB` | ❌ | Timeout in seconds for GitHub Models API calls. Default: `10.0` |

---

## AI Resilience & Circuit Breakers

The backend implements a decoupled `AIProvider` model with auto-failover and circuit breakers:
1. **Groq Provider** (Primary, if key present)
2. **GitHub Models Provider** (Secondary, if token present)
3. **Local Database Rule Engine** (Fallback)

If a provider fails repeatedly (3 consecutive failures), its circuit breaker transitions to `OPEN` for a 60-second cooldown period, causing requests to immediately fall back to secondary providers. Caching is stored persistently in the database (`ai_categorization_caches`) to reduce redundant API calls.

