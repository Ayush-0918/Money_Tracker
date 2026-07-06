"""
app/api/deps.py
─────────────────────────────────────────────────────────────────────────────
FastAPI shared dependencies used across multiple route modules.

Centralising dependencies here avoids circular imports and keeps route
handlers clean — they declare what they need, not how to get it.

Dependencies:
  get_db         — yields an AsyncSession per request (from database.py)
  get_current_user_id — extracts and verifies the JWT from Authorization header
"""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db  # re-export for convenience
from app.utils.security import verify_access_token

# Re-export get_db so routes only need to import from deps
__all__ = ["get_db", "get_current_user_id"]

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
# auto_error=False lets us write a custom 401 message
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> uuid.UUID:
    """
    FastAPI dependency that verifies the Bearer JWT and returns the user_id.

    Usage in route:
        @router.get("/some-endpoint")
        async def handler(user_id: uuid.UUID = Depends(get_current_user_id)):
            ...

    Args:
        credentials: Parsed Authorization header (injected by FastAPI).

    Returns:
        UUID of the authenticated user extracted from the token payload.

    Raises:
        HTTPException(401): If no token is provided or token is invalid/expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Include 'Authorization: Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_access_token(credentials.credentials)


from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

# Dependency for admin API key
admin_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=True)


async def verify_admin_api_key(api_key: str = Security(admin_api_key_header)):
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin API Key",
        )
    return api_key
