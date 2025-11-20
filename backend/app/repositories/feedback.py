"""Feedback and newsletter persistence logic."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from backend.app.integrations.supabase import get_supabase_client


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def check_feedback_rate_limit(ip_address: str, session_id: str) -> bool:
    client = get_supabase_client()
    if not client:
        print("[Supabase] Rate limiting unavailable - blocking request")
        raise Exception("Rate limiting system unavailable")

    ip_hash = _hash_value(ip_address)
    session_hash = _hash_value(session_id)

    response = client.rpc(
        "check_feedback_rate_limit",
        {"p_ip_hash": ip_hash, "p_session_hash": session_hash},
    ).execute()

    if response.data is not None:
        return bool(response.data)

    print("[Supabase] Rate limit check returned no data - blocking request")
    raise Exception("Rate limit check failed")


def submit_user_feedback(
    analysis_type: str,
    experience_rating: str,
    ip_address: str,
    session_id: str,
    analyzed_entity: Optional[str] = None,
    review_text: Optional[str] = None,
    email: Optional[str] = None,
    email_consented: bool = False,
    user_agent: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        print("[Supabase] Feedback submission not available - Supabase not configured")
        return None

    try:
        data = {
            "analysis_type": analysis_type,
            "analyzed_entity": analyzed_entity,
            "experience_rating": experience_rating,
            "review_text": review_text,
            "email": email if email_consented else None,
            "email_consented": email_consented,
            "ip_hash": _hash_value(ip_address),
            "session_hash": _hash_value(session_id),
            "user_agent": user_agent[:200] if user_agent else None,
        }
        response = client.table("user_feedback").insert(data).execute()
        if response.data:
            print("[Supabase] User feedback submitted successfully")
            return response.data[0]
        print("[Supabase] Failed to submit user feedback - no data returned")
        return None
    except Exception as exc:
        print(f"[Supabase] Failed to submit user feedback: {exc}")
        return None


def get_newsletter_subscribers() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []

    try:
        response = client.table("newsletter_subscribers").select("*").execute()
        return response.data if response.data else []
    except Exception as exc:
        print(f"[Supabase] Failed to get newsletter subscribers: {exc}")
        return []
