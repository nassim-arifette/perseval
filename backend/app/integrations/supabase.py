"""Supabase client initialization and helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from backend.app.core.settings import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional[Client]:
    """Return a shared Supabase client instance if credentials are configured."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None

    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as exc:  # pragma: no cover - network/init errors
        print(f"[Supabase] Failed to initialize client: {exc}")
        return None


def is_supabase_available() -> bool:
    """Convenience helper used by routes to check for Supabase availability."""
    return get_supabase_client() is not None
