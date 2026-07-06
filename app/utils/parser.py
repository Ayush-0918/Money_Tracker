"""
app/utils/parser.py
─────────────────────────────────────────────────────────────────────────────
Transaction data extraction from raw notification/SMS text.

This module parses Indian bank/payment notification text to extract:
  - Amount (Decimal, exact — never float)
  - Merchant name
  - Transaction date (falls back to current UTC time if not found)

Supported formats (common Indian bank/UPI SMS patterns):
  - "Rs.499 debited from your SBI account to Netflix"
  - "₹1,234.56 paid to Swiggy via UPI"
  - "INR 2000 debited for Amazon Pay"
  - "Debit of Rs 500.00 at BigBasket on 01-Jul-2024"
  - "Your account debited with ₹99 for Hotstar subscription"

Design:
  - All functions are pure (no side effects, no DB calls).
  - Raises ParseError (a custom exception) on failure so callers can
    return a clean 422 response without crashing.
  - Uses decimal.Decimal for amount, never float.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Final
from zoneinfo import ZoneInfo

from app.utils.logging_config import get_logger

logger = get_logger(__name__)


# ── Custom Exceptions ─────────────────────────────────────────────────────────


class ParseError(Exception):
    """
    Raised when a required field (amount or merchant) cannot be extracted
    from the notification text.

    The error message is user-facing (returned in the API response body)
    so keep it descriptive but free of internal implementation details.
    """


# ── Regex Patterns ────────────────────────────────────────────────────────────
#
# SUPPORTED AMOUNT FORMATS (all Indian payment notifications):
#   "Rs.499"          "Rs 1,234.56"     "RS.99"
#   "₹500"            "₹ 500.00"        "₹1,200"
#   "INR 2000"        "INR1500.50"
#   "Sent ₹1,200"     (PhonePe, Google Pay format)
#   "debited by Rs 500" (some bank formats)
#   "debited with 500" "amount 1,000"   (last resort)
#
# COMMA HANDLING: All amount strings are stripped of commas before
# Decimal conversion. "1,234.56" → Decimal("1234.56"). This handles
# Indian lakh notation too: "1,00,000" → Decimal("100000").
#
# Order matters — more specific patterns FIRST to avoid partial matches.
# Group 1 always contains the raw amount string.
_AMOUNT_PATTERNS: Final[list[str]] = [
    # "Rs.1,234.56" / "Rs 500" / "RS.99" — most common Indian bank format
    r"(?:Rs\.?|rs\.?)\s*([\d,]+(?:\.\d{1,2})?)",
    # "₹1,234" / "₹ 500.00" / "Sent ₹1,200" (works because ₹ is the anchor)
    r"₹\s*([\d,]+(?:\.\d{1,2})?)",
    # "INR 2000" / "inr1500.50"
    r"(?:INR|inr)\s*([\d,]+(?:\.\d{1,2})?)",
    # "debited by Rs 500" — some PSU bank formats use "by" instead of "of"
    r"debited\s+by\s+(?:Rs\.?\s*)?([\d,]+(?:\.\d{1,2})?)",
    # "debited with 500" / "amount of 1,000" / "amount: 500" — last resort
    r"(?:debited\s+with|amount\s+of|amount\s*:?)\s*([\d,]+(?:\.\d{1,2})?)",
]

_COMPILED_AMOUNT_PATTERNS: Final[list[re.Pattern[str]]] = [re.compile(p, re.IGNORECASE) for p in _AMOUNT_PATTERNS]

# Merchant patterns — extract names following contextual keywords.
# Merchant names: start with a capital letter, 2–40 chars, may contain spaces/&/-
_MERCHANT_PATTERNS: Final[list[str]] = [
    # "debited to Netflix" / "paid to Swiggy" / "towards BSNL"
    r"(?:debited\s+to|paid\s+to|transferred\s+to|sent\s+to|towards)\s+([A-Za-z][A-Za-z0-9\s&.\-]{1,39}?)(?:\s+(?:via|on|using|at|for|\.|$)|\.|$)",
    # "at BigBasket" / "at HDFC"
    r"\bat\s+([A-Z][A-Za-z0-9\s&.\-]{1,39}?)(?:\s+(?:on|via|using|\.|$)|\.|$)",
    # "for Netflix" / "for Amazon Prime"
    r"\bfor\s+([A-Za-z][A-Za-z0-9\s&.\-]{1,39}?)(?:\s+(?:subscription|on|via|\.|$)|\.|$)",
    # "to MERCHANT_NAME VPA" style (UPI IDs often come after merchant name)
    r"to\s+([A-Za-z][A-Za-z0-9\s&.\-]{1,39}?)(?:\s*@|\.|$)",
]

_COMPILED_MERCHANT_PATTERNS: Final[list[re.Pattern[str]]] = [re.compile(p, re.IGNORECASE) for p in _MERCHANT_PATTERNS]

# Date patterns (optional — we fall back to now() if not found)
_DATE_PATTERNS: Final[list[tuple[str, str]]] = [
    # "01-Jul-2024" / "01 Jul 2024"
    (r"\b(\d{1,2}[-\s][A-Za-z]{3}[-\s]\d{4})\b", "%d-%b-%Y"),
    # "01/07/2024" or "01-07-2024"
    (r"\b(\d{2}[/\-]\d{2}[/\-]\d{4})\b", "%d/%m/%Y"),
    # "2024-07-01" (ISO)
    (r"\b(\d{4}-\d{2}-\d{2})\b", "%Y-%m-%d"),
]


# ── Result Dataclass ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParsedTransaction:
    """
    Immutable result of a successful transaction parse.

    Attributes:
        amount:           Exact transaction amount as Decimal.
        merchant:         Cleaned merchant/payee name.
        transaction_date: When the transaction occurred (UTC). Defaults to
                          parse time if no date found in text.
        raw_amount_str:   The raw amount string before conversion (for logging).
    """

    amount: Decimal
    merchant: str
    transaction_date: datetime
    raw_amount_str: str


# ── Public API ────────────────────────────────────────────────────────────────


def parse_transaction(text: str) -> ParsedTransaction:
    """
    Parse a raw notification/SMS string into structured transaction data.

    Attempts to extract amount, merchant, and date using ordered regex
    patterns. Stops at the first successful match for each field.

    Args:
        text: Raw notification text that has already passed the OTP filter.
              Must be non-empty.

    Returns:
        ParsedTransaction dataclass with extracted fields.

    Raises:
        ParseError: If amount OR merchant cannot be extracted. The error
                    message describes which field failed, so the Android app
                    can show a meaningful prompt to the user.

    Examples:
        >>> result = parse_transaction("Rs.499 debited to Netflix via HDFC")
        >>> result.amount
        Decimal('499')
        >>> result.merchant
        'Netflix'
    """
    if not text or not text.strip():
        raise ParseError("Notification text is empty.")

    amount, raw_amount_str = _extract_amount(text)
    merchant = _extract_merchant(text)
    transaction_date = _extract_date(text)

    logger.info(
        "parser: transaction parsed | amount=%s | merchant=%r | date=%s",
        amount,
        merchant,
        transaction_date.isoformat(),
    )

    return ParsedTransaction(
        amount=amount,
        merchant=merchant,
        transaction_date=transaction_date,
        raw_amount_str=raw_amount_str,
    )


# ── Private Helpers ───────────────────────────────────────────────────────────


def _extract_amount(text: str) -> tuple[Decimal, str]:
    """
    Extract the transaction amount from notification text.

    Tries each amount pattern in order (most specific first). Returns on
    the first match. Removes commas from the raw string before Decimal
    conversion (e.g., "1,234.56" → Decimal("1234.56")).

    Args:
        text: Raw notification text.

    Returns:
        Tuple of (Decimal amount, raw_amount_str before conversion).

    Raises:
        ParseError: If no amount pattern matches or the matched value
                    cannot be converted to Decimal.
    """
    for pattern in _COMPILED_AMOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            raw_str = match.group(1)
            clean_str = raw_str.replace(",", "")
            try:
                amount = Decimal(clean_str)
                if amount <= 0:
                    raise ParseError(f"Parsed amount '{clean_str}' is not a positive number.")
                return amount, raw_str
            except InvalidOperation as exc:
                raise ParseError(f"Found amount text '{raw_str}' but could not convert to " f"a number: {exc}") from exc

    raise ParseError("Could not find a transaction amount (e.g., Rs.500 or ₹1,234) " "in the notification text.")


def _extract_merchant(text: str) -> str:
    """
    Extract and clean the merchant/payee name from notification text.

    Tries each merchant pattern in order. Strips trailing punctuation and
    excess whitespace from the matched group.

    Args:
        text: Raw notification text.

    Returns:
        Cleaned merchant name string (title-cased for consistency).

    Raises:
        ParseError: If no merchant pattern matches.
    """
    for pattern in _COMPILED_MERCHANT_PATTERNS:
        match = pattern.search(text)
        if match:
            raw_merchant = match.group(1).strip()
            # Remove trailing punctuation artefacts
            clean_merchant = re.sub(r"[.\-\s]+$", "", raw_merchant).strip()
            if len(clean_merchant) >= 2:
                return clean_merchant.title()

    raise ParseError(
        "Could not identify the merchant/payee name in the notification text. "
        "Please check the format or add this transaction manually."
    )


def _extract_date(text: str) -> datetime:
    """
    Extract the transaction date from notification text.

    Dates in Indian bank SMS are inherently IST. This function parses the
    date in IST and converts it to UTC for database storage.

    Returns the current UTC timestamp if no recognisable date is found
    rather than raising an error — a missing date is recoverable but a
    missing amount/merchant is not.

    Args:
        text: Raw notification text.

    Returns:
        datetime (timezone-aware, UTC). Either parsed from text or now().
    """
    ist_zone = ZoneInfo("Asia/Kolkata")

    for pattern_str, date_format in _DATE_PATTERNS:
        match = re.search(pattern_str, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Normalise separator for multi-format patterns
            normalised = date_str.replace(" ", "-").replace("/", "-")
            try:
                parsed_naive = datetime.strptime(normalised, date_format.replace("/", "-"))
                # Treat the parsed date as IST, then convert to UTC for the database
                parsed_ist = parsed_naive.replace(tzinfo=ist_zone)
                return parsed_ist.astimezone(timezone.utc)
            except ValueError:
                continue  # Try next pattern

    logger.debug("parser: no date found in text — using current UTC time as fallback")
    return datetime.now(tz=timezone.utc)
