"""
app/schemas/auth.py
─────────────────────────────────────────────────────────────────────────────
Pydantic request/response schemas for authentication endpoints.

RegisterRequest:  Input for POST /auth/register
TokenResponse:    Output — JWT token + basic user info
"""

import re
import uuid

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    """
    Request body for user registration.

    Attributes:
        phone_number: User's phone number in E.164 format (e.g., +919876543210).
                      Used as the unique identifier and for WhatsApp reports.
        name:         Display name. Must be between 2 and 100 characters.
        language_preference: Two-letter language code for reports. Defaults to 'en'.
    """

    phone_number: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Phone number in E.164 format (e.g., +919876543210).",
        examples=["+919876543210"],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Display name of the user.",
        examples=["Aayu"],
    )
    language_preference: str = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="Two-letter language code (e.g., 'en', 'hi').",
        examples=["en", "hi"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """
        Ensure phone number contains only valid characters.
        Allows + prefix, digits, spaces, hyphens, and parentheses.
        """
        cleaned = re.sub(r"[\s\-()]", "", v)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise ValueError("Invalid phone number format. Use E.164 format, e.g., +919876543210")
        return v.strip()

    @field_validator("language_preference")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Ensure language code is lowercase alpha characters only."""
        if not re.match(r"^[a-zA-Z]{2,5}$", v):
            raise ValueError("Language preference must be a 2-5 letter code (e.g., 'en', 'hi').")
        return v.lower()


class TokenResponse(BaseModel):
    """
    Response body for successful registration.

    Attributes:
        access_token: The JWT Bearer token to use in all subsequent requests.
        token_type:   Always "bearer".
        user_id:      The UUID of the newly created (or existing) user.
        name:         User's display name (for the Android app to display).
    """

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    name: str
