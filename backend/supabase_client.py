"""
Supabase client for caching influencer, company, and product analysis results.
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Cache expiration in days
CACHE_EXPIRATION_DAYS = 7

# Initialize Supabase client if credentials are available
supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[Supabase] Failed to initialize client: {e}")
        supabase_client = None


def is_cache_available() -> bool:
    """Check if Supabase caching is available."""
    return supabase_client is not None


def get_cached_influencer(handle: str, platform: str = "instagram") -> Optional[Dict[str, Any]]:
    """
    Retrieve cached influencer analysis from Supabase.

    Args:
        handle: Influencer handle (without @)
        platform: Social media platform

    Returns:
        Cached analysis data or None if not found/expired
    """
    if not supabase_client:
        return None

    try:
        normalized_handle = handle.lstrip("@").lower()

        response = supabase_client.table("influencer_cache").select("*").eq(
            "handle", normalized_handle
        ).eq("platform", platform).order("updated_at", desc=True).limit(1).execute()

        if not response.data:
            return None

        record = response.data[0]

        # Check if cache is expired
        updated_at = datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
        if datetime.now(updated_at.tzinfo) - updated_at > timedelta(days=CACHE_EXPIRATION_DAYS):
            print(f"[Supabase] Cache expired for influencer: {handle}")
            return None

        print(f"[Supabase] Cache hit for influencer: {handle}")
        return record["analysis_data"]

    except Exception as e:
        print(f"[Supabase] Failed to get cached influencer {handle}: {e}")
        return None


def cache_influencer(
    handle: str, platform: str, analysis_data: Dict[str, Any]
) -> bool:
    """
    Store influencer analysis in Supabase cache.

    Args:
        handle: Influencer handle (without @)
        platform: Social media platform
        analysis_data: Complete analysis result to cache

    Returns:
        True if successful, False otherwise
    """
    if not supabase_client:
        return False

    try:
        normalized_handle = handle.lstrip("@").lower()

        data = {
            "handle": normalized_handle,
            "platform": platform,
            "analysis_data": analysis_data,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Upsert (insert or update if exists)
        supabase_client.table("influencer_cache").upsert(
            data, on_conflict="handle,platform"
        ).execute()

        print(f"[Supabase] Cached influencer: {handle}")
        return True

    except Exception as e:
        print(f"[Supabase] Failed to cache influencer {handle}: {e}")
        return False


def get_cached_company(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached company analysis from Supabase.

    Args:
        name: Company name

    Returns:
        Cached analysis data or None if not found/expired
    """
    if not supabase_client:
        return None

    try:
        normalized_name = name.strip().lower()

        response = supabase_client.table("company_cache").select("*").eq(
            "name", normalized_name
        ).order("updated_at", desc=True).limit(1).execute()

        if not response.data:
            return None

        record = response.data[0]

        # Check if cache is expired
        updated_at = datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
        if datetime.now(updated_at.tzinfo) - updated_at > timedelta(days=CACHE_EXPIRATION_DAYS):
            print(f"[Supabase] Cache expired for company: {name}")
            return None

        print(f"[Supabase] Cache hit for company: {name}")
        return record["analysis_data"]

    except Exception as e:
        print(f"[Supabase] Failed to get cached company {name}: {e}")
        return None


def cache_company(name: str, analysis_data: Dict[str, Any]) -> bool:
    """
    Store company analysis in Supabase cache.

    Args:
        name: Company name
        analysis_data: Complete analysis result to cache

    Returns:
        True if successful, False otherwise
    """
    if not supabase_client:
        return False

    try:
        normalized_name = name.strip().lower()

        data = {
            "name": normalized_name,
            "analysis_data": analysis_data,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Upsert (insert or update if exists)
        supabase_client.table("company_cache").upsert(
            data, on_conflict="name"
        ).execute()

        print(f"[Supabase] Cached company: {name}")
        return True

    except Exception as e:
        print(f"[Supabase] Failed to cache company {name}: {e}")
        return False


def get_cached_product(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached product analysis from Supabase.

    Args:
        name: Product name

    Returns:
        Cached analysis data or None if not found/expired
    """
    if not supabase_client:
        return None

    try:
        normalized_name = name.strip().lower()

        response = supabase_client.table("product_cache").select("*").eq(
            "name", normalized_name
        ).order("updated_at", desc=True).limit(1).execute()

        if not response.data:
            return None

        record = response.data[0]

        # Check if cache is expired
        updated_at = datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
        if datetime.now(updated_at.tzinfo) - updated_at > timedelta(days=CACHE_EXPIRATION_DAYS):
            print(f"[Supabase] Cache expired for product: {name}")
            return None

        print(f"[Supabase] Cache hit for product: {name}")
        return record["analysis_data"]

    except Exception as e:
        print(f"[Supabase] Failed to get cached product {name}: {e}")
        return None


def cache_product(name: str, analysis_data: Dict[str, Any]) -> bool:
    """
    Store product analysis in Supabase cache.

    Args:
        name: Product name
        analysis_data: Complete analysis result to cache

    Returns:
        True if successful, False otherwise
    """
    if not supabase_client:
        return False

    try:
        normalized_name = name.strip().lower()

        data = {
            "name": normalized_name,
            "analysis_data": analysis_data,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Upsert (insert or update if exists)
        supabase_client.table("product_cache").upsert(
            data, on_conflict="name"
        ).execute()

        print(f"[Supabase] Cached product: {name}")
        return True

    except Exception as e:
        print(f"[Supabase] Failed to cache product {name}: {e}")
        return False


# Marketplace functions
def add_influencer_to_marketplace(
    handle: str,
    platform: str,
    profile_data: Dict[str, Any],
    trust_data: Dict[str, Any],
    admin_notes: Optional[str] = None,
    is_featured: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Add or update an influencer in the marketplace.

    Args:
        handle: Influencer handle
        platform: Social media platform
        profile_data: Profile information (followers, bio, etc.)
        trust_data: Trust score and component scores
        admin_notes: Optional admin notes
        is_featured: Whether to feature this influencer

    Returns:
        The created/updated marketplace record or None if failed
    """
    if not supabase_client:
        print("[Supabase] Marketplace not available - Supabase not configured")
        return None

    try:
        normalized_handle = handle.lstrip("@").lower()

        data = {
            "handle": normalized_handle,
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
            "last_analyzed_at": datetime.utcnow().isoformat(),
            "admin_notes": admin_notes,
            "is_featured": is_featured,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Upsert (insert or update if exists)
        response = supabase_client.table("marketplace_influencers").upsert(
            data, on_conflict="handle,platform"
        ).execute()

        print(f"[Supabase] Added/updated marketplace influencer: {handle}")
        return response.data[0] if response.data else None

    except Exception as e:
        print(f"[Supabase] Failed to add influencer to marketplace {handle}: {e}")
        return None


def get_marketplace_influencer(handle: str, platform: str = "instagram") -> Optional[Dict[str, Any]]:
    """
    Get a single influencer from marketplace.

    Args:
        handle: Influencer handle
        platform: Social media platform

    Returns:
        Marketplace influencer record or None
    """
    if not supabase_client:
        return None

    try:
        normalized_handle = handle.lstrip("@").lower()

        # SECURITY: Select only public columns, exclude admin_notes
        public_columns = (
            "id,handle,display_name,platform,followers_count,following_count,posts_count,is_verified,"
            "overall_trust_score,trust_label,message_history_score,"
            "followers_score,web_reputation_score,disclosure_score,"
            "profile_url,bio,is_featured,analysis_summary,issues,last_analyzed_at,"
            "created_at,updated_at"
        )

        response = supabase_client.table("marketplace_influencers").select(
            public_columns
        ).eq("handle", normalized_handle).eq("platform", platform).limit(1).execute()

        if not response.data:
            return None

        return response.data[0]

    except Exception as e:
        print(f"[Supabase] Failed to get marketplace influencer {handle}: {e}")
        return None


def list_marketplace_influencers(
    search: Optional[str] = None,
    trust_level: Optional[str] = None,
    sort_by: str = "trust_score",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    List marketplace influencers with filtering and pagination.

    Args:
        search: Search term for handle or display name
        trust_level: Filter by trust level ('high', 'medium', 'low')
        sort_by: Field to sort by ('trust_score', 'followers', 'last_analyzed')
        sort_order: Sort order ('asc' or 'desc')
        limit: Number of results to return
        offset: Pagination offset

    Returns:
        Dict with 'data' (list of influencers) and 'total' (total count)
    """
    if not supabase_client:
        return {"data": [], "total": 0}

    try:
        # Start building query
        # SECURITY: Select only public columns, exclude admin_notes
        public_columns = (
            "id,handle,display_name,platform,followers_count,following_count,posts_count,is_verified,"
            "overall_trust_score,trust_label,message_history_score,"
            "followers_score,web_reputation_score,disclosure_score,"
            "profile_url,bio,is_featured,analysis_summary,issues,last_analyzed_at,"
            "created_at,updated_at"
        )
        query = supabase_client.table("marketplace_influencers").select(
            public_columns, count="exact"
        )

        # Apply filters
        if search:
            # SECURITY: Sanitize search term to prevent filter injection
            # Remove special PostgREST characters: commas, parentheses, periods
            safe_search = search.replace(",", "").replace("(", "").replace(")", "").replace(".", "")
            search_term = f"%{safe_search.lower()}%"
            query = query.or_(f"handle.ilike.{search_term},display_name.ilike.{search_term}")

        if trust_level:
            query = query.eq("trust_label", trust_level)

        # Map sort_by to actual column names
        sort_column_map = {
            "trust_score": "overall_trust_score",
            "followers": "followers_count",
            "last_analyzed": "last_analyzed_at"
        }
        sort_column = sort_column_map.get(sort_by, "overall_trust_score")

        # Apply sorting
        ascending = sort_order == "asc"
        query = query.order(sort_column, desc=not ascending)

        # Apply featured sorting first (featured items always on top)
        query = query.order("is_featured", desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute query
        response = query.execute()

        return {
            "data": response.data if response.data else [],
            "total": response.count if response.count is not None else 0
        }

    except Exception as e:
        print(f"[Supabase] Failed to list marketplace influencers: {e}")
        return {"data": [], "total": 0}


def remove_from_marketplace(handle: str, platform: str = "instagram") -> bool:
    """
    Remove an influencer from the marketplace.

    Args:
        handle: Influencer handle
        platform: Social media platform

    Returns:
        True if successful, False otherwise
    """
    if not supabase_client:
        return False

    try:
        normalized_handle = handle.lstrip("@").lower()

        supabase_client.table("marketplace_influencers").delete().eq(
            "handle", normalized_handle
        ).eq("platform", platform).execute()

        print(f"[Supabase] Removed from marketplace: {handle}")
        return True

    except Exception as e:
        print(f"[Supabase] Failed to remove from marketplace {handle}: {e}")
        return False


# User feedback functions
def _hash_value(value: str) -> str:
    """
    Create SHA-256 hash of a value for privacy.

    Args:
        value: String to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def check_feedback_rate_limit(ip_address: str, session_id: str) -> bool:
    """
    Check if user has exceeded rate limits for feedback submission.

    Uses database function for rate limiting to prevent spam.

    SECURITY: This function FAILS CLOSED - if rate limiting is unavailable,
    requests are blocked to prevent abuse.

    Args:
        ip_address: User's IP address (will be hashed)
        session_id: User's session/fingerprint ID (will be hashed)

    Returns:
        True if within rate limits, False if exceeded or on error

    Raises:
        Exception: If rate limiting system is unavailable (caller should handle)
    """
    if not supabase_client:
        # SECURITY: Fail closed - block if Supabase not available
        print("[Supabase] Rate limiting unavailable - blocking request")
        raise Exception("Rate limiting system unavailable")

    try:
        ip_hash = _hash_value(ip_address)
        session_hash = _hash_value(session_id)

        # Call the database function to check rate limits
        response = supabase_client.rpc(
            'check_feedback_rate_limit',
            {'p_ip_hash': ip_hash, 'p_session_hash': session_hash}
        ).execute()

        # The function returns a boolean
        if response.data is not None:
            return bool(response.data)

        # SECURITY: Fail closed - if no response, block the request
        print("[Supabase] Rate limit check returned no data - blocking request")
        raise Exception("Rate limit check failed")

    except Exception as e:
        print(f"[Supabase] Rate limit check failed: {e}")
        # SECURITY: Fail closed - re-raise exception to block submission
        raise


def submit_user_feedback(
    analysis_type: str,
    experience_rating: str,
    ip_address: str,
    session_id: str,
    analyzed_entity: Optional[str] = None,
    review_text: Optional[str] = None,
    email: Optional[str] = None,
    email_consented: bool = False,
    user_agent: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Submit user feedback to the database with security measures.

    Args:
        analysis_type: Type of analysis performed
        experience_rating: User's experience rating ('good', 'medium', or 'bad')
        ip_address: User's IP address (will be hashed for privacy)
        session_id: User's session/fingerprint ID (will be hashed)
        analyzed_entity: Optional entity that was analyzed
        review_text: Optional review text from user
        email: Optional email for newsletter (must have consent)
        email_consented: Whether user consented to emails
        user_agent: Optional user agent string (truncated to 200 chars)

    Returns:
        The created feedback record or None if failed
    """
    if not supabase_client:
        print("[Supabase] Feedback submission not available - Supabase not configured")
        return None

    try:
        # Hash sensitive data for privacy
        ip_hash = _hash_value(ip_address)
        session_hash = _hash_value(session_id)

        # Truncate user agent for storage
        truncated_user_agent = user_agent[:200] if user_agent else None

        # Only store email if consent was given
        final_email = email if email_consented else None

        data = {
            "analysis_type": analysis_type,
            "analyzed_entity": analyzed_entity,
            "experience_rating": experience_rating,
            "review_text": review_text,
            "email": final_email,
            "email_consented": email_consented,
            "ip_hash": ip_hash,
            "session_hash": session_hash,
            "user_agent": truncated_user_agent,
        }

        # Insert feedback
        response = supabase_client.table("user_feedback").insert(data).execute()

        if response.data:
            print(f"[Supabase] User feedback submitted successfully")
            return response.data[0]
        else:
            print(f"[Supabase] Failed to submit user feedback - no data returned")
            return None

    except Exception as e:
        print(f"[Supabase] Failed to submit user feedback: {e}")
        return None


def get_newsletter_subscribers() -> list[Dict[str, Any]]:
    """
    Get list of newsletter subscribers (admin only).

    Returns:
        List of subscriber records with email and stats
    """
    if not supabase_client:
        return []

    try:
        response = supabase_client.table("newsletter_subscribers").select("*").execute()
        return response.data if response.data else []

    except Exception as e:
        print(f"[Supabase] Failed to get newsletter subscribers: {e}")
        return []
