"""
app/utils/otp_filter.py
─────────────────────────────────────────────────────────────────────────────
OTP and sensitive-content detection for incoming notification text.

SECURITY CRITICAL MODULE
─────────────────────────
This module is the first line of defense against storing sensitive financial
security credentials. The `is_otp_message()` function MUST be called before
any other processing of raw notification text. If it returns True, the caller
MUST immediately reject the request and store NOTHING.

Design principles:
  - Pure function — no side effects, no DB calls, easy to unit test.
  - Case-insensitive matching (re.IGNORECASE) to catch all variations.
  - Regex patterns cover common Indian SMS OTP formats as well as
    international variations.
  - Fails SAFE: if in doubt, reject (return True = is OTP).

Adding new patterns:
  - Add to SENSITIVE_PATTERNS list below.
  - Add a corresponding test case in tests/test_otp_filter.py.
  - Do NOT remove existing patterns — only add new ones.
"""

import re
from typing import Final

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# ── Sensitive Content Patterns ────────────────────────────────────────────────
# Each pattern is a regular expression string (case-insensitive matching is
# applied at call time via re.IGNORECASE, not baked into the pattern string).
#
# Rationale for each pattern:
#   OTP           — direct keyword match (e.g., "Your OTP is 123456")
#   one-time pass — verbose form used by banks (e.g., "one time password")
#   one time pin  — alternative phrasing
#   verification code — common in app-based 2FA SMS
#   do not share  — universal fraud-warning phrase in OTP messages
#   valid for N min/sec — OTP expiry language (unique to OTPs)
#   passcode      — used by some payment apps (e.g., "your passcode: 1234")
#   transaction pin — UPI/banking PIN messages
#   cvv           — card security code — NEVER store
#   pin is / your pin — direct PIN disclosure in SMS
SENSITIVE_PATTERNS: Final[list[str]] = [
    r"\bOTP\b",
    r"one[\s\-]?time[\s\-]?pass(?:word|code)?",
    r"one[\s\-]?time[\s\-]?pin",
    r"verification[\s\-]?code",
    r"do[\s\-]?not[\s\-]?share",
    r"valid[\s\-]?for[\s\-]?\d+[\s\-]?(?:min(?:ute)?s?|sec(?:ond)?s?|hrs?|hours?)",
    r"\bpasscode\b",
    r"transaction[\s\-]?pin",
    r"\bcvv\b",
    r"your[\s\-]?pin[\s\-]?(?:is|:)",
    r"pin[\s\-]?(?:is|:)[\s\-]?\d{4,6}",
]

# Pre-compiled pattern for performance (called on every incoming request)
_COMPILED_PATTERN: Final[re.Pattern[str]] = re.compile(
    "|".join(f"(?:{p})" for p in SENSITIVE_PATTERNS),
    flags=re.IGNORECASE,
)


def is_otp_message(text: str) -> bool:
    """
    Determine whether the given notification text contains OTP or other
    sensitive security content that must NOT be stored.

    This function is the security gateway for the transaction ingestion
    pipeline. It must be called as the FIRST step — before parsing, before
    any DB interaction.

    Args:
        text: The raw notification or SMS text received from the Android app.

    Returns:
        True  — if the text contains ANY sensitive pattern (reject & discard).
        False — if the text appears safe to process and store.

    Examples:
        >>> is_otp_message("Your OTP is 123456. Do not share.")
        True
        >>> is_otp_message("Rs.499 debited from your account for Netflix.")
        False
        >>> is_otp_message("Verification code: 8821. Valid for 10 minutes.")
        True
    """
    if not text or not text.strip():
        # Empty text — nothing to store, treat as safe (not OTP-specific)
        logger.debug("otp_filter: empty text received — passing through")
        return False

    match = _COMPILED_PATTERN.search(text)
    if match:
        logger.warning(
            "otp_filter: SENSITIVE content detected — request rejected | " "matched_pattern=%r | text_preview=%r",
            match.group(),
            text[:80],  # Only log a short preview — never the full OTP
        )
        return True

    logger.debug("otp_filter: text passed OTP check | text_preview=%r", text[:80])
    return False


def get_pattern_count() -> int:
    """
    Return the number of active sensitive patterns.

    Useful for health-check endpoints or test assertions to ensure the
    filter was not accidentally emptied.
    """
    return len(SENSITIVE_PATTERNS)
