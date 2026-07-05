"""
app/api/transactions.py
─────────────────────────────────────────────────────────────────────────────
Transaction ingestion route.

POST /transactions
  Receives a raw notification/SMS text from the Android app, runs it through
  the full pipeline (OTP filter → parse → save → recurring check), and
  returns the parsed transaction data for confirmation.

Security:
  - Requires valid JWT (Bearer token).
  - Rate limited to RATE_LIMIT_PER_MINUTE per user (via slowapi).
  - user_id in the request body MUST match the authenticated user's token.
  - Pydantic validates all input before any processing begins.
"""

import uuid
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.utils.limiter import limiter
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import (
    OTPRejectedResponse,
    PaginatedTransactionResponse,
    ParseFailedResponse,
    TransactionCreate,
    TransactionResponse,
    CategoryUpdateDto,
)

from app.models.budget import Budget
from app.models.merchant import MerchantAlias, LearningEvent

from app.services.transaction_service import OTPDetectedError, create_transaction
from app.utils.logging_config import get_logger
from app.utils.parser import ParseError

logger = get_logger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a payment notification",
    description=(
        "Receives raw notification/SMS text, filters for OTP content (rejected "
        "with 400 if detected), parses amount and merchant, saves the transaction, "
        "and checks for recurring subscription patterns. "
        "Rate limited to 20 requests per minute per user."
    ),
    responses={
        400: {"model": OTPRejectedResponse, "description": "OTP/sensitive content detected — nothing saved"},
        404: {"description": "User not found"},
        422: {"model": ParseFailedResponse, "description": "Could not parse amount or merchant from text"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("20/minute")
async def post_transaction(
    request: Request,
    body: TransactionCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    """
    Full transaction ingestion pipeline.

    Security check: the user_id in the request body must match the JWT token's
    user_id. This prevents a user from submitting transactions on behalf of
    another user even if they have a valid token.

    Args:
        request:         FastAPI request object (needed by slowapi for rate limiting).
        body:            Validated transaction payload.
        current_user_id: UUID from the verified JWT token (injected by dependency).
        db:              Async database session.

    Returns:
        TransactionResponse with parsed data and database record ID.

    Raises:
        HTTP 400: OTP/sensitive content detected.
        HTTP 403: user_id in body doesn't match token.
        HTTP 404: User not found in database.
        HTTP 422: Parsing failed (amount or merchant not found).
        HTTP 429: Rate limit exceeded.
    """
    # ── Authorization check: body user_id must match token ───────────────────
    if body.user_id != current_user_id:
        logger.warning(
            "transactions: user_id mismatch — token=%s body=%s",
            current_user_id,
            body.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user_id in the request body does not match your authentication token.",
        )

    # ── Verify user exists ────────────────────────────────────────────────────
    user_result = await db.execute(
        select(User).where(User.id == current_user_id)
    )
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{current_user_id}' not found.",
        )

    # ── Run the ingestion pipeline ────────────────────────────────────────────
    try:
        return await create_transaction(payload=body, db=db)

    except OTPDetectedError:
        # OTP/sensitive content: return 400, log warning (no text content logged)
        logger.warning(
            "transactions: OTP detected — rejecting | user_id=%s", current_user_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "OTP_REJECTED",
                "message": (
                    "The notification text appears to contain an OTP or sensitive "
                    "security code. This message has NOT been stored."
                ),
            },
        )

    except ParseError as exc:
        # Parsing failure: return 422 with helpful message
        logger.warning(
            "transactions: parse failed | user_id=%s | reason=%s",
            current_user_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "PARSE_FAILED",
                "message": str(exc),
                "hint": (
                    "The notification format may not be supported yet. "
                    "You can add this transaction manually."
                ),
            },
        )
@router.get(
    "",
    response_model=PaginatedTransactionResponse,
    summary="Get paginated transaction history",
    description="Returns a paginated list of transactions for the authenticated user, sorted by date (newest first).",
)
async def list_transactions(
    request: Request,
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort: Literal["date_desc", "date_asc", "amount_desc", "amount_asc"] = "date_desc",
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedTransactionResponse:
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20

    offset = (page - 1) * size

    # Build the base query conditions
    conditions = [Transaction.user_id == user_id]

    if search:
        conditions.append(Transaction.merchant.ilike(f"%{search}%"))
    if category:
        conditions.append(Transaction.category.ilike(f"%{category}%"))
    if merchant:
        conditions.append(Transaction.merchant.ilike(f"%{merchant}%"))
    if from_date:
        conditions.append(Transaction.transaction_date >= from_date)
    if to_date:
        conditions.append(Transaction.transaction_date <= to_date)
    if min_amount is not None:
        conditions.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conditions.append(Transaction.amount <= max_amount)

    # Query total count
    count_stmt = select(func.count(Transaction.id)).where(*conditions)
    total = await db.scalar(count_stmt) or 0

    # Determine sort order
    if sort == "date_desc":
        order_col = Transaction.transaction_date.desc()
    elif sort == "date_asc":
        order_col = Transaction.transaction_date.asc()
    elif sort == "amount_desc":
        order_col = Transaction.amount.desc()
    elif sort == "amount_asc":
        order_col = Transaction.amount.asc()
    else:
        order_col = Transaction.transaction_date.desc()

    # Query items
    items_stmt = (
        select(Transaction)
        .where(*conditions)
        .order_by(order_col)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(items_stmt)
    transactions = result.scalars().all()

    return PaginatedTransactionResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        size=size,
        has_more=(offset + size) < total,
    )

@router.patch(
    "/{tx_id}/category",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update transaction category",
    description="Updates the category of an existing transaction. Must belong to the authenticated user.",
)
@limiter.limit("10/minute")
async def update_transaction_category(
    tx_id: uuid.UUID,
    request: Request,
    body: CategoryUpdateDto,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 1. Ownership Check (Transaction)
    stmt = select(Transaction).where(
        Transaction.id == tx_id,
        Transaction.user_id == current_user_id
    )
    result = await db.execute(stmt)
    tx = result.scalar_one_or_none()

    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or you do not have permission to modify it."
        )

    # 2. Validation Check (Category existence and accessibility)
    # User can only assign a system category or one they created themselves.
    cat_stmt = select(Category).where(
        Category.id == body.category_id,
        or_(Category.system == True, Category.user_id == current_user_id)
    )
    cat_result = await db.execute(cat_stmt)
    if cat_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category_id. Category does not exist or access is denied."
        )

    # ── Logic ─────────────────────────────────────────────────────────────
    # Invalidate old budget cache if there is one
    if tx.category_id:
        old_budget_stmt = select(Budget).where(Budget.user_id == current_user_id, Budget.category_id == tx.category_id)
        old_budget = (await db.execute(old_budget_stmt)).scalar_one_or_none()
        if old_budget:
            old_budget.cached_updated_at = None

    tx.category_id = body.category_id
    tx.category = None # Nullify free-text to prevent inconsistency
    
    # Invalidate new budget cache
    new_budget_stmt = select(Budget).where(Budget.user_id == current_user_id, Budget.category_id == body.category_id)
    new_budget = (await db.execute(new_budget_stmt)).scalar_one_or_none()
    if new_budget:
        new_budget.cached_updated_at = None

    # Queue AI Learning Event (Phase 1)
    alias_stmt = select(MerchantAlias).where(MerchantAlias.alias == tx.merchant.lower().strip())
    alias = (await db.execute(alias_stmt)).scalar_one_or_none()
    
    learning_event = LearningEvent(
        transaction_id=tx.id,
        merchant_id=alias.merchant_id if alias else None,
        old_category_id=tx.category_id,
        new_category_id=body.category_id,
        feedback_source="MANUAL"
    )
    db.add(learning_event)
    
    # SQLAlchemy will automatically commit this change because of the FastAPI Dependency 
    # (if the get_db yield block runs successfully)
    
    logger.info("transactions: category updated | tx_id=%s | category_id=%s", tx_id, body.category_id)
    return None
