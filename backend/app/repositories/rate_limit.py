"""Supabase-backed rate limiting helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.app.integrations.supabase import get_supabase_client


def check_and_increment_rate_limit(
    client_ip: str,
    endpoint_group: str,
    daily_limit: int,
) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.rpc(
            "check_and_increment_rate_limit",
            {
                "p_client_ip": client_ip,
                "p_endpoint_group": endpoint_group,
                "p_daily_limit": daily_limit,
            },
        ).execute()
        return response.data if response.data else None
    except Exception as exc:
        print(f"[Supabase] Rate limit RPC failed: {exc}")
        return None


def get_rate_limit_status(
    client_ip: str,
    endpoint_group: str,
) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return None

    try:
        response = client.rpc(
            "get_rate_limit_status",
            {"p_client_ip": client_ip, "p_endpoint_group": endpoint_group},
        ).execute()
        return response.data if response.data else None
    except Exception as exc:
        print(f"[Supabase] Rate limit status RPC failed: {exc}")
        return None
