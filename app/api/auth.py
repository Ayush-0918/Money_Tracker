"""
app/api/auth.py
─────────────────────────────────────────────────────────────────────────────
Authentication routes.

POST /auth/register
  Creates a new user account (or returns existing if phone_number already
  registered — idempotent). Returns a JWT access token.

This endpoint intentionally does NOT require a pre-existing token so that
new Android app installations can register on first launch.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_db
from app.config import settings
from app.utils.limiter import limiter
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.utils.logging_config import get_logger
from app.utils.security import create_access_token

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Register or retrieve user account",
    description=(
        "Register a new user with a phone number and name. "
        "If the phone number is already registered, returns a new token for "
        "the existing account (idempotent). "
        "The returned JWT must be included as 'Authorization: Bearer <token>' "
        "in all subsequent API calls."
    ),
)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user or retrieve token for an existing account.

    Args:
        body: Validated registration data (phone_number, name, language_preference).
        db:   Async database session.

    Returns:
        TokenResponse containing the JWT access token and user details.
    """
    # Check if user already exists with this phone number
    stmt = select(User).where(User.phone_number == body.phone_number)
    result = await db.execute(stmt)
    existing_user: Optional[User] = result.scalar_one_or_none()

    if existing_user:
        logger.info(
            "auth: existing user login | user_id=%s | phone=%s",
            existing_user.id,
            body.phone_number,
        )
        token = create_access_token(user_id=existing_user.id)
        return TokenResponse(
            access_token=token,
            user_id=existing_user.id,
            name=existing_user.name,
        )

    # Create new user
    new_user = User(
        phone_number=body.phone_number,
        name=body.name,
        language_preference=body.language_preference,
    )
    db.add(new_user)
    await db.flush()  # Get the UUID before commit

    logger.info(
        "auth: new user registered | user_id=%s | phone=%s",
        new_user.id,
        body.phone_number,
    )

    token = create_access_token(user_id=new_user.id)
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        name=new_user.name,
    )
