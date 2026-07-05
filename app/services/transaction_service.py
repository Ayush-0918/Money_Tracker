"""
app/services/transaction_service.py
─────────────────────────────────────────────────────────────────────────────
Business logic for transaction ingestion.

Orchestrates the full pipeline:
  1. OTP filter check (reject if sensitive)
  2. Text parsing (extract amount, merchant, date)
  3. Database persistence
  4. Recurring detection + subscription upsert

This service is intentionally thin on HTTP concerns — it raises domain
exceptions (ParseError, OTPError) and lets the route handler convert them
to appropriate HTTP responses.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.models.merchant import Merchant, MerchantAlias, MerchantRule, UserOverride
from app.models.budget import Budget
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.utils.logging_config import get_logger
from app.utils.otp_filter import is_otp_message
from app.utils.parser import ParseError, parse_transaction
from app.services.subscription_service import check_and_update_recurring

logger = get_logger(__name__)


class OTPDetectedError(Exception):
    """
    Raised when the OTP filter detects sensitive content in the input.
    The route handler converts this to HTTP 400.
    Nothing has been written to the database at this point.
    """
    pass


async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession,
) -> TransactionResponse:
    """
    Full transaction ingestion pipeline: filter → parse → save → recurring check.

    Args:
        payload: Validated request body from the route handler.
        db:      Async SQLAlchemy session (provided via dependency injection).

    Returns:
        TransactionResponse with parsed data and DB record ID.

    Raises:
        OTPDetectedError: If the raw_text contains OTP/sensitive patterns.
                          Nothing is written to DB.
        ParseError:       If amount or merchant cannot be extracted.
                          Nothing is written to DB.
    """
    logger.info(
        "transaction_service: starting ingestion | user_id=%s | source=%s",
        payload.user_id,
        payload.source,
    )

    # ── Step 0: Idempotency Check ───────────────────────────────────────────
    # If the client sends a key we've seen before, return the existing record.
    # This safely handles Android network retries without storing duplicates.
    if payload.idempotency_key:
        existing_stmt = select(Transaction).where(
            Transaction.user_id == payload.user_id,
            Transaction.idempotency_key == payload.idempotency_key,
        )
        existing_result = await db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()
        if existing:
            logger.info(
                "transaction_service: idempotency hit — returning existing | "
                "key=%s | transaction_id=%s",
                payload.idempotency_key,
                existing.id,
            )
            response = TransactionResponse.model_validate(existing)
            response = response.model_copy(update={"is_duplicate": True})
            return response

    # ── Step 1: OTP Filter ────────────────────────────────────────────────────
    # MUST be the first check after idempotency. If this returns True, abort.
    # Do not parse, do not log the text contents, do not save anything.
    if is_otp_message(payload.raw_text):
        raise OTPDetectedError("Sensitive content (OTP/PIN) detected. Request rejected.")

    # ── Step 2: Parse Transaction Data ────────────────────────────────────────
    # ParseError propagates up to the route handler → HTTP 422
    parsed = parse_transaction(payload.raw_text)

    # ── Step 2.5: AI Categorization Phase 1 ───────────────────────────────────
    # We resolve the raw merchant string into a canonical UUID and apply rules.
    final_category_id = None
    canonical_merchant_id = None
    
    # 1. Look up alias
    alias_stmt = select(MerchantAlias).where(MerchantAlias.alias == parsed.merchant.lower().strip())
    alias_result = await db.execute(alias_stmt)
    alias = alias_result.scalar_one_or_none()

    if alias:
        canonical_merchant_id = alias.merchant_id
        
        # 2. Check User Override
        override_stmt = select(UserOverride).where(
            UserOverride.user_id == payload.user_id,
            UserOverride.merchant_id == canonical_merchant_id,
            UserOverride.correction_count >= 2
        )
        override_result = await db.execute(override_stmt)
        override = override_result.scalar_one_or_none()

        if override:
            final_category_id = override.category_id
            logger.info("Categorized by UserOverride (id=%s)", canonical_merchant_id)
        else:
            # 3. Check Global Rule
            rule_stmt = select(MerchantRule).where(
                MerchantRule.merchant_id == canonical_merchant_id
            )
            rule_result = await db.execute(rule_stmt)
            rule = rule_result.scalar_one_or_none()
            if rule:
                final_category_id = rule.category_id
                logger.info("Categorized by MerchantRule (id=%s)", canonical_merchant_id)
    else:
        # Create unverified merchant
        logger.info("Unverified merchant detected: %s", parsed.merchant)
        # Note: We do not create the merchant automatically right now to prevent DB bloat 
        # from garbage parsing. The async learning queue will handle bulk unverified ingestion.

    # ── Step 3: Persist to Database ───────────────────────────────────────────
    transaction = Transaction(
        user_id=payload.user_id,
        amount=parsed.amount,
        merchant=parsed.merchant,
        category=None, # Legacy text field (deprecated in PR-5)
        category_id=final_category_id,
        transaction_date=parsed.transaction_date,
        source=payload.source,
        is_recurring=False,  # Updated below after recurring check
        raw_text=payload.raw_text,  # Safe to store: OTP filter already passed
        idempotency_key=payload.idempotency_key,  # May be None (optional)
        currency="INR",       # Phase 1-2: INR only. Multi-currency in Phase 3.
    )
    db.add(transaction)
    await db.flush()  # Get the auto-generated ID without committing yet

    # ── Step 3.5: Invalidate Budget Cache ─────────────────────────────────────
    if final_category_id:
        budget_stmt = select(Budget).where(
            Budget.user_id == payload.user_id,
            Budget.category_id == final_category_id
        )
        budget = (await db.execute(budget_stmt)).scalar_one_or_none()
        if budget:
            budget.cached_updated_at = None
            logger.info("budget: cache invalidated for category_id=%s", final_category_id)

    logger.info(
        "transaction_service: transaction saved | id=%s | merchant=%r | amount=%s",
        transaction.id,
        transaction.merchant,
        transaction.amount,
    )

    # ── Step 4: Recurring Detection ───────────────────────────────────────────
    # This may update transaction.is_recurring and upsert a subscription record.
    # Runs in the same transaction — if it fails, the whole operation rolls back.
    is_recurring = await check_and_update_recurring(
        db=db,
        user_id=payload.user_id,
        merchant=parsed.merchant,
        amount=parsed.amount,
        transaction_date=parsed.transaction_date,
    )

    if is_recurring:
        transaction.is_recurring = True
        logger.info(
            "transaction_service: marked as recurring | merchant=%r | transaction_id=%s",
            parsed.merchant,
            transaction.id,
        )

    # db.commit() is handled by the get_db() dependency after the route returns
    return TransactionResponse.model_validate(transaction)
