"""Security helpers shared across routers."""

from __future__ import annotations

import hmac
from typing import Optional

from fastapi import HTTPException

from backend.app.core.settings import get_settings


def verify_admin_auth(authorization: Optional[str]) -> None:
    """Validate the admin Authorization header."""
    settings = get_settings()
    admin_api_key = settings.admin_api_key

    if not admin_api_key:
        raise HTTPException(
            status_code=501,
            detail="Admin authentication not configured. Set ADMIN_API_KEY in .env file.",
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Authorization header required. Use: 'Authorization: Bearer YOUR_API_KEY'",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use: 'Authorization: Bearer YOUR_API_KEY'",
        )

    provided_key = authorization.replace("Bearer ", "").strip()

    if not hmac.compare_digest(provided_key, admin_api_key):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Invalid API key.",
        )
