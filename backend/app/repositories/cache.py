"""Caching helpers backed by Supabase tables."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from backend.app.integrations.supabase import get_supabase_client

CACHE_EXPIRATION_DAYS = 7


def _normalize_handle(handle: str) -> str:
    return handle.lstrip("@").lower()


def _is_expired(updated_at: str) -> bool:
    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return datetime.now(dt.tzinfo) - dt > timedelta(days=CACHE_EXPIRATION_DAYS)


def _get_latest_record(table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return None

    query = client.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)

    response = query.order("updated_at", desc=True).limit(1).execute()
    if not response.data:
        return None

    record = response.data[0]
    updated_at = record.get("updated_at")
    if isinstance(updated_at, str) and _is_expired(updated_at):
        print(f"[Supabase] Cache expired for {table} filters={filters}")
        return None

    return record


def get_cached_influencer(handle: str, platform: str = "instagram") -> Optional[Dict[str, Any]]:
    record = _get_latest_record(
        "influencer_cache",
        {"handle": _normalize_handle(handle), "platform": platform},
    )
    return record["analysis_data"] if record else None


def cache_influencer(handle: str, platform: str, analysis_data: Dict[str, Any]) -> bool:
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("influencer_cache").upsert(
            {
                "handle": _normalize_handle(handle),
                "platform": platform,
                "analysis_data": analysis_data,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="handle,platform",
        ).execute()
        print(f"[Supabase] Cached influencer: {handle}")
        return True
    except Exception as exc:
        print(f"[Supabase] Failed to cache influencer {handle}: {exc}")
        return False


def get_cached_company(name: str) -> Optional[Dict[str, Any]]:
    record = _get_latest_record("company_cache", {"name": name.lower()})
    return record["analysis_data"] if record else None


def cache_company(name: str, analysis_data: Dict[str, Any]) -> bool:
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("company_cache").upsert(
            {
                "name": name.lower(),
                "analysis_data": analysis_data,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="name",
        ).execute()
        print(f"[Supabase] Cached company: {name}")
        return True
    except Exception as exc:
        print(f"[Supabase] Failed to cache company {name}: {exc}")
        return False


def get_cached_product(name: str) -> Optional[Dict[str, Any]]:
    record = _get_latest_record("product_cache", {"name": name.lower()})
    return record["analysis_data"] if record else None


def cache_product(name: str, analysis_data: Dict[str, Any]) -> bool:
    client = get_supabase_client()
    if not client:
        return False

    try:
        client.table("product_cache").upsert(
            {
                "name": name.lower(),
                "analysis_data": analysis_data,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="name",
        ).execute()
        print(f"[Supabase] Cached product: {name}")
        return True
    except Exception as exc:
        print(f"[Supabase] Failed to cache product {name}: {exc}")
        return False
