"""
app/utils/security.py
─────────────────────────────────────────────────────────────────────────────
JWT token creation and verification for API authentication.

Token format:
    Header:  {"alg": "HS256", "typ": "JWT"}
    Payload: {"sub": "<user_id_uuid>", "exp": <unix_timestamp>}

Usage:
    token = create_access_token(user_id=user.id)
    user_id = verify_access_token(token)  # raises HTTPException if invalid
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Token field names — centralised to avoid typos in multiple places
_SUBJECT_FIELD = "sub"
_EXPIRY_FIELD = "exp"


def create_access_token(user_id: uuid.UUID) -> str:
    """
    Create a signed JWT access token for the given user.

    The token payload contains:
        sub: str(user_id)  — the user's UUID as a string
        exp: int           — UNIX timestamp of expiration

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A signed JWT string to be returned to the client and sent as
        `Authorization: Bearer <token>` in subsequent requests.
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        _SUBJECT_FIELD: str(user_id),
        _EXPIRY_FIELD: expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.info("security: access token created | user_id=%s | expires=%s", user_id, expire.isoformat())
    return token


def verify_access_token(token: str) -> uuid.UUID:
    """
    Verify a JWT token and return the embedded user_id.

    Validates:
      - Signature (using JWT_SECRET_KEY)
      - Expiration (raises 401 if expired)
      - Presence of 'sub' claim

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        The user_id (UUID) extracted from the token's 'sub' claim.

    Raises:
        HTTPException(401): If the token is invalid, expired, or tampered.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Token may be expired or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject: Optional[str] = payload.get(_SUBJECT_FIELD)
        if subject is None:
            logger.warning("security: token missing 'sub' claim")
            raise credentials_exception

        return uuid.UUID(subject)

    except JWTError as exc:
        logger.warning("security: JWT verification failed | error=%s", str(exc))
        raise credentials_exception from exc
    except (ValueError, AttributeError) as exc:
        # UUID parsing error or other malformed payload
        logger.warning("security: malformed token payload | error=%s", str(exc))
        raise credentials_exception from exc
