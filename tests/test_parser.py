"""
tests/test_parser.py
─────────────────────────────────────────────────────────────────────────────
Unit tests for the transaction text parser.

Tests cover:
  - Various Indian bank/UPI SMS amount formats (Rs., ₹, INR).
  - Comma-separated amounts (e.g., "1,234.56").
  - Merchant extraction from different preposition patterns.
  - Date parsing from multiple formats.
  - Error cases: missing amount, missing merchant.

To run:
    pytest tests/test_parser.py -v
"""

from decimal import Decimal

import pytest

from app.utils.parser import ParseError, parse_transaction


class TestAmountExtraction:
    """Tests for extracting amounts from various SMS formats."""

    def test_rs_dot_format(self):
        """Rs. prefix — most common HDFC/SBI format."""
        result = parse_transaction("Rs.499 debited from your account to Netflix.")
        assert result.amount == Decimal("499")

    def test_rs_space_format(self):
        """Rs with space — also common."""
        result = parse_transaction("Rs 1000 paid to Swiggy via UPI.")
        assert result.amount == Decimal("1000")

    def test_rupee_symbol(self):
        """₹ symbol format."""
        result = parse_transaction("₹1,234.56 paid to BigBasket on 01-Jul-2024.")
        assert result.amount == Decimal("1234.56")

    def test_inr_prefix(self):
        """INR prefix format."""
        result = parse_transaction("INR 2000 debited from your SBI account to Amazon.")
        assert result.amount == Decimal("2000")

    def test_comma_separated_amount(self):
        """Amounts with comma thousands separator."""
        result = parse_transaction("₹12,345.00 transferred to HDFC savings.")
        assert result.amount == Decimal("12345.00")

    def test_decimal_amount(self):
        """Decimal amount with 2 places."""
        result = parse_transaction("Rs.850.50 debited for Zomato order.")
        assert result.amount == Decimal("850.50")

    def test_large_amount(self):
        """Large transaction amount."""
        result = parse_transaction("₹1,00,000.00 debited from your account for LIC Premium.")
        assert result.amount == Decimal("100000.00")

    def test_sent_rupee_format(self):
        """PhonePe / Google Pay 'Sent ₹' format."""
        result = parse_transaction("Sent ₹1,200 to Swiggy successfully.")
        assert result.amount == Decimal("1200")

    def test_debited_by_format(self):
        """PSU bank format — 'debited by Rs 500'."""
        result = parse_transaction("Your account debited by Rs 500 towards BSNL.")
        assert result.amount == Decimal("500")

    def test_amount_is_decimal_not_float(self):
        """Critical: amount must be Decimal, not float."""
        result = parse_transaction("Rs.299 debited to Spotify.")
        assert isinstance(result.amount, Decimal)
        assert not isinstance(result.amount, float)


class TestMerchantExtraction:
    """Tests for extracting merchant names from various SMS formats."""

    def test_paid_to_merchant(self):
        """'paid to' pattern."""
        result = parse_transaction("₹499 paid to Netflix via HDFC UPI.")
        assert "Netflix" in result.merchant

    def test_debited_to_merchant(self):
        """'debited to' pattern."""
        result = parse_transaction("Rs.150 debited to Dunzo from your account.")
        assert "Dunzo" in result.merchant

    def test_at_merchant(self):
        """'at MERCHANT' pattern (common for POS transactions)."""
        result = parse_transaction("Rs 850 spent at Zomato using credit card.")
        assert "Zomato" in result.merchant

    def test_for_merchant(self):
        """'for MERCHANT' pattern (subscription renewals)."""
        result = parse_transaction("₹299 debited for Hotstar subscription renewal.")
        assert "Hotstar" in result.merchant

    def test_merchant_name_is_title_case(self):
        """Merchant names should be normalised to title case."""
        result = parse_transaction("Rs.500 debited to SWIGGY via UPI.")
        assert result.merchant == result.merchant.title()


class TestDateExtraction:
    """Tests for date parsing from various formats."""

    def test_date_ddmonyyyy_format(self):
        from zoneinfo import ZoneInfo

        """01-Jul-2024 format."""
        result = parse_transaction("Rs.499 debited to Netflix on 01-Jul-2024.")
        ist_date = result.transaction_date.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist_date.day == 1
        assert ist_date.month == 7
        assert ist_date.year == 2024

    def test_date_ddmmyyyy_slash(self):
        """DD/MM/YYYY format."""
        from zoneinfo import ZoneInfo

        result = parse_transaction("₹999 paid to Amazon on 15/06/2024.")
        ist_date = result.transaction_date.astimezone(ZoneInfo("Asia/Kolkata"))
        assert ist_date.day == 15
        assert ist_date.month == 6

    def test_no_date_falls_back_to_now(self):
        """Missing date falls back to current time — should not raise error."""
        from datetime import datetime, timezone

        before = datetime.now(tz=timezone.utc)
        result = parse_transaction("Rs.200 paid to Ola.")
        after = datetime.now(tz=timezone.utc)
        # The fallback date should be between before and after
        assert before <= result.transaction_date <= after

    def test_date_is_timezone_aware(self):
        """Parsed dates must be timezone-aware (UTC)."""

        result = parse_transaction("Rs.100 paid to Swiggy.")
        assert result.transaction_date.tzinfo is not None


class TestErrorCases:
    """Tests for ParseError when required fields cannot be extracted."""

    def test_missing_amount_raises_parse_error(self):
        """No recognisable amount → ParseError."""
        with pytest.raises(ParseError) as exc_info:
            parse_transaction("Transaction successful for Netflix subscription.")
        assert "amount" in str(exc_info.value).lower() or "Could not find" in str(exc_info.value)

    def test_missing_merchant_raises_parse_error(self):
        """No recognisable merchant → ParseError."""
        with pytest.raises(ParseError):
            parse_transaction("Rs.500 was debited.")  # No 'to/at/for' pattern

    def test_empty_text_raises_parse_error(self):
        """Empty text → ParseError."""
        with pytest.raises(ParseError):
            parse_transaction("")

    def test_zero_amount_raises_parse_error(self):
        """Zero amount is not a valid transaction."""
        with pytest.raises(ParseError):
            parse_transaction("Rs.0 debited to someone.")

    def test_parse_error_message_is_user_friendly(self):
        """ParseError messages should be descriptive, not tracebacks."""
        with pytest.raises(ParseError) as exc_info:
            parse_transaction("No numbers here, no merchants either.")
        error_msg = str(exc_info.value)
        assert len(error_msg) > 10  # Not just a generic one-word error
        assert "Traceback" not in error_msg  # No internal stack traces
