"""
tests/test_otp_filter.py
─────────────────────────────────────────────────────────────────────────────
Unit tests for the OTP/sensitive content filter.

This is the MOST CRITICAL test module in the project. The OTP filter is a
security gate — any false negative (OTP message classified as safe) would
result in storing sensitive credentials in the database.

Test strategy:
  - True positives: Known OTP message formats MUST return True (reject).
  - True negatives: Legitimate payment messages MUST return False (allow).
  - Edge cases: Mixed case, partial matches, different languages, special chars.

To run:
    pytest tests/test_otp_filter.py -v
"""

import pytest

from app.utils.otp_filter import get_pattern_count, is_otp_message


class TestOTPMessageDetection:
    """Tests for messages that SHOULD be detected as OTP/sensitive content."""

    def test_otp_keyword_uppercase(self):
        """Standard OTP keyword — most common Indian bank format."""
        assert is_otp_message("Your OTP for HDFC Bank is 123456. Valid for 10 min.") is True

    def test_otp_keyword_lowercase(self):
        """Case-insensitive match — lowercase 'otp'."""
        assert is_otp_message("Use otp 9982 to complete your payment.") is True

    def test_otp_keyword_mixed_case(self):
        """Mixed case OTP."""
        assert is_otp_message("Otp for your transaction: 445566") is True

    def test_one_time_password_phrase(self):
        """Verbose form used by some banks."""
        assert is_otp_message("Your one time password is 998877. Do not share with anyone.") is True

    def test_one_time_password_hyphenated(self):
        """Hyphenated variant of one-time-password."""
        assert is_otp_message("One-time-password: 123456 expires in 5 minutes.") is True

    def test_one_time_pin(self):
        """Some banks say 'one time pin' instead of 'one time password'."""
        assert is_otp_message("Your one time pin is 778899. Do not disclose.") is True

    def test_verification_code(self):
        """App-based 2FA SMS format."""
        assert is_otp_message("Your verification code is 334455. Enter it within 15 minutes.") is True

    def test_verification_code_hyphenated(self):
        """Hyphenated verification-code."""
        assert is_otp_message("verification-code: 998877") is True

    def test_do_not_share(self):
        """Universal OTP fraud-warning phrase — always signals OTP message."""
        assert is_otp_message("123456 is your code. Do not share this with anyone.") is True

    def test_do_not_share_mixed_case(self):
        """Mixed-case 'Do Not Share'."""
        assert is_otp_message("Paytm OTP 5544. Do Not Share.") is True

    def test_valid_for_minutes(self):
        """Expiry language unique to OTPs."""
        assert is_otp_message("Your code is 667788. Valid for 5 minutes.") is True

    def test_valid_for_seconds(self):
        """Expiry in seconds."""
        assert is_otp_message("OTP 112233. Valid for 30 seconds.") is True

    def test_passcode_keyword(self):
        """Some payment apps use 'passcode' instead of OTP."""
        assert is_otp_message("Your passcode is 9988. Do not share.") is True

    def test_transaction_pin(self):
        """Banking PIN messages."""
        assert is_otp_message("Your transaction pin is 4321. Use it immediately.") is True

    def test_cvv_keyword(self):
        """CVV — card security code — must never be stored."""
        assert is_otp_message("Your CVV for your card is 123. Use for online payments.") is True

    def test_cvv_lowercase(self):
        """Lowercase cvv."""
        assert is_otp_message("Do not share your cvv with anyone.") is True

    def test_pin_is_pattern(self):
        """Direct PIN disclosure pattern."""
        assert is_otp_message("Your Pin is: 5678 for your transaction.") is True


class TestSafePaymentMessages:
    """Tests for legitimate payment messages that MUST NOT be rejected."""

    def test_simple_debit_notification(self):
        """Standard bank debit notification — no OTP content."""
        assert is_otp_message("Rs.499 debited from your account for Netflix via UPI.") is False

    def test_upi_payment_confirmation(self):
        """UPI payment SMS format."""
        assert is_otp_message("₹1,234.00 paid to Swiggy via UPI on 01-Jul-2024.") is False

    def test_bank_debit_with_merchant(self):
        """SBI-style debit notification."""
        assert is_otp_message("INR 2000.00 debited from your SBI A/c to Amazon.in on 30Jun24.") is False

    def test_credit_card_transaction(self):
        """Credit card spending notification."""
        assert is_otp_message("Rs 850.00 spent at Zomato using HDFC Credit Card ending 1234.") is False

    def test_subscription_renewal(self):
        """Subscription auto-renewal notification."""
        assert is_otp_message("Your Hotstar subscription of ₹299 has been renewed.") is False

    def test_wallet_payment(self):
        """PhonePe/Paytm wallet transaction."""
        assert is_otp_message("₹150 transferred to Dunzo from your PhonePe wallet.") is False

    def test_amazon_pay_debit(self):
        """Amazon Pay debit notification."""
        assert is_otp_message("Rs.999 debited from Amazon Pay balance for your order.") is False

    def test_gym_subscription(self):
        """Local merchant subscription notification."""
        assert is_otp_message("Rs.2500 auto-debited for Cult.fit membership on 1 July 2024.") is False


class TestEdgeCases:
    """Edge cases to ensure robust pattern matching."""

    def test_empty_string(self):
        """Empty string should not trigger OTP filter (returns False)."""
        assert is_otp_message("") is False

    def test_whitespace_only(self):
        """Whitespace-only string — nothing to detect."""
        assert is_otp_message("   ") is False

    def test_otp_as_word_boundary(self):
        """The word 'HOTEL' contains 'OTP' — must NOT trigger (word boundary)."""
        assert is_otp_message("Rs.3000 paid to HOTEL Sunshine for stay.") is False

    def test_word_boundary_notopayment(self):
        """'NOTOPAYMENT' contains 'OTP' chars but not as a word — should be fine."""
        # Note: actual test depends on pattern — \\bOTP\\b should NOT match inside word
        assert is_otp_message("Rs.500 for PHOTOP printing service.") is False

    def test_amount_with_digits_no_otp(self):
        """Message with many digits (could confuse naive matching) but no OTP."""
        assert is_otp_message("₹12,345.67 transferred to savings account 9876543210.") is False

    def test_get_pattern_count(self):
        """Ensure the pattern list was not accidentally emptied."""
        count = get_pattern_count()
        assert count >= 10, f"Expected at least 10 patterns, got {count}"
