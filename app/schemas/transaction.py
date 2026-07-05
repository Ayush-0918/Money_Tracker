"""
app/schemas/transaction.py
─────────────────────────────────────────────────────────────────────────────
Pydantic request/response schemas for the transactions endpoint.

TransactionCreate:  Input for POST /transactions
TransactionResponse: Output — what was parsed and saved
ErrorDetail:        Consistent error payload format
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TransactionCreate(BaseModel):
    """
    Request body for POST /transactions.

    The Android app sends this when a payment notification arrives.

    Attributes:
        user_id:          UUID of the user this transaction belongs to.
        raw_text:         Raw notification/SMS text to parse.
        source:           'sms' or 'notification'.
        idempotency_key:  Optional client-generated deduplication key.
                          Recommended format: SHA256(user_id + raw_text + hour_bucket)
                          If provided and the key already exists for this user,
                          the existing transaction is returned (no duplicate insert).
                          Clients SHOULD send this to survive network retries safely.
    """

    user_id: uuid.UUID = Field(
        ...,
        description="UUID of the user this transaction belongs to.",
    )
    raw_text: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Raw notification or SMS text to parse for transaction data.",
        examples=["Rs.499 debited from your account to Netflix via UPI"],
    )
    source: Literal["sms", "notification"] = Field(
        ...,
        description="Source of the notification: 'sms' or 'notification'.",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=128,
        description=(
            "Optional client-generated deduplication key. "
            "If a transaction with this key already exists for this user, "
            "the existing record is returned instead of creating a duplicate."
        ),
        examples=["a3f2bc91d4e7..."],
    )

    @field_validator("raw_text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace from raw_text."""
        return v.strip()


class TransactionResponse(BaseModel):
    """
    Response body for a successfully processed transaction.

    Contains both the database record ID and the parsed fields so the
    Android app can display a confirmation to the user.

    Attributes:
        id:               UUID of the saved transaction record.
        user_id:          UUID of the owning user.
        amount:           Parsed amount as Decimal string (e.g., "499.00").
        merchant:         Extracted merchant name.
        category:         Always null in the current version (Phase 3 — AI categorizer).
        transaction_date: When the transaction occurred.
        source:           'sms' or 'notification'.
        is_recurring:     Whether recurring detection flagged this transaction.
        created_at:       When the DB record was created.
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    merchant: str
    category: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    transaction_date: datetime
    source: str
    is_recurring: bool
    currency: str = "INR"
    is_duplicate: bool = Field(
        default=False,
        description=(
            "True if this response is for an existing transaction (idempotency hit). "
            "The Android app can use this to show 'already saved' vs 'new transaction'."
        ),
    )
    created_at: datetime


class PaginatedTransactionResponse(BaseModel):
    """
    Paginated list of transactions.
    
    Provides standard pagination metadata so the Android app can implement
    infinite scrolling for the transaction history.
    """
    items: list[TransactionResponse]
    total: int = Field(description="Total number of transactions across all pages.")
    page: int = Field(description="Current page number (1-indexed).")
    size: int = Field(description="Number of items per page.")
    has_more: bool = Field(description="True if there is a next page.")

class OTPRejectedResponse(BaseModel):
    """
    Response body when an OTP/sensitive message is detected and rejected.

    HTTP Status: 400 Bad Request
    """

    error: str = "OTP_REJECTED"
    message: str = (
        "The notification text appears to contain an OTP or sensitive security "
        "code. This message has NOT been stored. Please do not send OTP messages."
    )


class ParseFailedResponse(BaseModel):
    """
    Response body when transaction parsing fails (amount or merchant not found).

    HTTP Status: 422 Unprocessable Entity
    """

    error: str = "PARSE_FAILED"
    message: str
    hint: str = (
        "The notification format may not be supported yet. "
        "You can add this transaction manually."
    )

class CategoryUpdateDto(BaseModel):
    category_id: uuid.UUID = Field(
        ...,
        description="The new category_id (UUID) to assign to the transaction."
    )
