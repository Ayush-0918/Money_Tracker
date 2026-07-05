-- ═══════════════════════════════════════════════════════════════════════════
-- supabase_setup.sql  ·  Money Tracker Backend
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Run this SQL in the Supabase Dashboard → SQL Editor (New Query).
--
-- IMPORTANT:
--   • Amount columns use NUMERIC(12, 2), NOT FLOAT — financial precision.
--   • Enums are implemented as VARCHAR + CHECK constraints (more portable
--     than PostgreSQL ENUM types, which require ALTER TYPE to modify).
--   • All UUID primary keys use gen_random_uuid() as default.
--   • Indexes are added on frequently-queried columns.
--
-- Run order: users → transactions → subscriptions (respects FK dependencies).
-- ═══════════════════════════════════════════════════════════════════════════


-- ── Enable UUID extension (required for gen_random_uuid) ──────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ══════════════════════════════════════════════════════════════════════════════
-- Table: users
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number        VARCHAR(20)     NOT NULL UNIQUE,
    name                VARCHAR(100)    NOT NULL,
    language_preference VARCHAR(5)      NOT NULL DEFAULT 'en',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_phone_length   CHECK (char_length(phone_number) >= 7),
    CONSTRAINT chk_lang_format    CHECK (language_preference ~ '^[a-z]{2,5}$')
);

-- Index for fast token verification (lookup by user_id) — already PK indexed.
-- Index for registration uniqueness check is covered by UNIQUE on phone_number.

COMMENT ON TABLE  users                      IS 'Application users identified by phone number.';
COMMENT ON COLUMN users.id                   IS 'UUID primary key.';
COMMENT ON COLUMN users.phone_number         IS 'WhatsApp-capable phone number (E.164 format recommended).';
COMMENT ON COLUMN users.language_preference  IS 'Two-letter language code for report generation.';


-- ══════════════════════════════════════════════════════════════════════════════
-- Table: transactions
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS transactions (
    id               UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount           NUMERIC(12, 2)  NOT NULL CHECK (amount > 0),
    merchant         VARCHAR(200)    NOT NULL,
    category         VARCHAR(100)    NULL,  -- Phase 3: AI categorizer will populate this
    transaction_date TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    source           VARCHAR(20)     NOT NULL,
    is_recurring     BOOLEAN         NOT NULL DEFAULT FALSE,
    raw_text         VARCHAR(2000)   NULL,  -- Stored ONLY after OTP filter passes
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Enum-style constraint for source
    CONSTRAINT chk_source_values CHECK (source IN ('sms', 'notification'))
);

-- Performance indexes for report queries (date range + user scoping)
CREATE INDEX IF NOT EXISTS idx_transactions_user_date
    ON transactions(user_id, transaction_date DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant
    ON transactions(user_id, merchant);

CREATE INDEX IF NOT EXISTS idx_transactions_category
    ON transactions(user_id, category)
    WHERE category IS NOT NULL;

COMMENT ON TABLE  transactions              IS 'Payment transactions parsed from Android notifications.';
COMMENT ON COLUMN transactions.amount       IS 'Transaction amount. NUMERIC(12,2) — never FLOAT.';
COMMENT ON COLUMN transactions.category     IS 'Spending category. NULL until Phase 3 AI categorizer assigns it.';
COMMENT ON COLUMN transactions.source       IS 'Origin: sms | notification.';
COMMENT ON COLUMN transactions.raw_text     IS 'Original notification text. Stored only after OTP filter passes.';


-- ══════════════════════════════════════════════════════════════════════════════
-- Table: subscriptions
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS subscriptions (
    id                      UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant                VARCHAR(200)    NOT NULL,
    amount                  NUMERIC(12, 2)  NOT NULL CHECK (amount > 0),
    billing_cycle           VARCHAR(20)     NOT NULL DEFAULT 'monthly',
    next_billing_date       DATE            NULL,
    last_used_confirmed_at  TIMESTAMPTZ     NULL,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'active',
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Unique: one subscription record per merchant per user
    CONSTRAINT uq_subscriptions_user_merchant UNIQUE (user_id, merchant),

    -- Enum-style constraints
    CONSTRAINT chk_billing_cycle CHECK (billing_cycle IN ('monthly', 'weekly', 'yearly')),
    CONSTRAINT chk_status        CHECK (status        IN ('active', 'paused', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
    ON subscriptions(user_id, status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_next_billing
    ON subscriptions(user_id, next_billing_date)
    WHERE next_billing_date IS NOT NULL;

COMMENT ON TABLE  subscriptions                          IS 'Detected recurring subscription charges.';
COMMENT ON COLUMN subscriptions.billing_cycle            IS 'monthly | weekly | yearly.';
COMMENT ON COLUMN subscriptions.next_billing_date        IS 'Estimated next charge date.';
COMMENT ON COLUMN subscriptions.last_used_confirmed_at   IS 'User confirmation of active use. Null = never confirmed.';
COMMENT ON COLUMN subscriptions.status                   IS 'active | paused | cancelled.';


-- ══════════════════════════════════════════════════════════════════════════════
-- Row Level Security (RLS) — Recommended for Supabase
-- ══════════════════════════════════════════════════════════════════════════════
-- Enable RLS so that the Supabase PostgREST API cannot be abused even if
-- someone bypasses our FastAPI layer. Our backend connects as the service
-- role (bypasses RLS), so these policies protect against direct API access.

ALTER TABLE users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions  ENABLE ROW LEVEL SECURITY;

-- Deny all direct PostgREST access (our FastAPI service role bypasses this)
-- To allow direct Supabase client access in future, replace with proper policies.
CREATE POLICY deny_all_users         ON users          FOR ALL USING (FALSE);
CREATE POLICY deny_all_transactions  ON transactions   FOR ALL USING (FALSE);
CREATE POLICY deny_all_subscriptions ON subscriptions  FOR ALL USING (FALSE);


-- ══════════════════════════════════════════════════════════════════════════════
-- Verify Setup
-- ══════════════════════════════════════════════════════════════════════════════
-- Run this to confirm all tables and indexes were created:

SELECT
    table_name,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('users', 'transactions', 'subscriptions')
ORDER BY table_name;
