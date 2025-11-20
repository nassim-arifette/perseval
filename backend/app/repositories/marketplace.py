"""Marketplace persistence helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend.app.integrations.supabase import get_supabase_client

PUBLIC_MARKETPLACE_COLUMNS = (
    "id,handle,display_name,platform,followers_count,following_count,posts_count,is_verified,"
    "overall_trust_score,trust_label,message_history_score,"
    "followers_score,web_reputation_score,disclosure_score,"
    "profile_url,bio,is_featured,analysis_summary,issues,"
    "last_analyzed_at,added_to_marketplace_at,created_at,updated_at"
)


def _normalize_handle(handle: str) -> str:
    return handle.lstrip("@").lower()


def add_influencer_to_marketplace(
    handle: str,
    platform: str,
    profile_data: Dict[str, Any],
    trust_data: Dict[str, Any],
    admin_notes: Optional[str] = None,
    is_featured: bool = False,
) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        print("[Supabase] Marketplace not available - Supabase not configured")
        return None

    try:
        now_iso = datetime.utcnow().isoformat()
        data = {
            "handle": _normalize_handle(handle),
            "platform": platform,
            "display_name": profile_data.get("full_name"),
            "bio": profile_data.get("bio"),
            "profile_url": profile_data.get("url"),
            "followers_count": profile_data.get("followers"),
            "following_count": profile_data.get("following"),
            "posts_count": profile_data.get("posts_count"),
            "is_verified": profile_data.get("is_verified", False),
            "overall_trust_score": trust_data.get("trust_score"),
            "trust_label": trust_data.get("label"),
            "message_history_score": trust_data.get("message_history_score"),
            "followers_score": trust_data.get("followers_score"),
            "web_reputation_score": trust_data.get("web_reputation_score"),
            "disclosure_score": trust_data.get("disclosure_score"),
            "analysis_summary": trust_data.get("notes"),
            "issues": trust_data.get("issues", []),
            "last_analyzed_at": now_iso,
            "admin_notes": admin_notes,
            "is_featured": is_featured,
            "updated_at": now_iso,
        }

        response = client.table("marketplace_influencers").upsert(
            data, on_conflict="handle,platform"
        ).execute()

        print(f"[Supabase] Added/updated marketplace influencer: {handle}")
        return response.data[0] if response.data else None

    except Exception as exc:
        print(f"[Supabase] Failed to add influencer to marketplace {handle}: {exc}")
        return None


def get_marketplace_influencer(handle: str, platform: str = "instagram") -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = (
            client.table("marketplace_influencers")
            .select(PUBLIC_MARKETPLACE_COLUMNS)
            .eq("handle", _normalize_handle(handle))
            .eq("platform", platform)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return response.data[0]

    except Exception as exc:
        print(f"[Supabase] Failed to get marketplace influencer {handle}: {exc}")
        return None


def list_marketplace_influencers(
    search: Optional[str] = None,
    trust_level: Optional[str] = None,
    sort_by: str = "trust_score",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    client = get_supabase_client()
    if not client:
        return {"data": [], "total": 0}

    try:
        query = client.table("marketplace_influencers").select(
            PUBLIC_MARKETPLACE_COLUMNS, count="exact"
        )

        if search:
            safe_search = (
                search.replace(",", "")
                .replace("(", "")
                .replace(")", "")
                .replace(".", "")
            )
            search_term = f"%{safe_search.lower()}%"
            query = query.or_(f"handle.ilike.{search_term},display_name.ilike.{search_term}")

        if trust_level:
            query = query.eq("trust_label", trust_level)

        sort_column_map = {
            "trust_score": "overall_trust_score",
            "followers": "followers_count",
            "last_analyzed": "last_analyzed_at",
        }
        sort_column = sort_column_map.get(sort_by, "overall_trust_score")
        ascending = sort_order == "asc"

        query = (
            query.order(sort_column, desc=not ascending)
            .order("is_featured", desc=True)
            .range(offset, offset + limit - 1)
        )

        response = query.execute()
        return {
            "data": response.data if response.data else [],
            "total": response.count if response.count is not None else 0,
        }

    except Exception as exc:
        print(f"[Supabase] Failed to list marketplace influencers: {exc}")
        return {"data": [], "total": 0}


def remove_from_marketplace(handle: str, platform: str = "instagram") -> bool:
    client = get_supabase_client()
    if not client:
        return False

    try:
        (
            client.table("marketplace_influencers")
            .delete()
            .eq("handle", _normalize_handle(handle))
            .eq("platform", platform)
            .execute()
        )
        print(f"[Supabase] Removed from marketplace: {handle}")
        return True
    except Exception as exc:
        print(f"[Supabase] Failed to remove from marketplace {handle}: {exc}")
        return False
