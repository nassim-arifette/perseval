"""Repository for user voting on influencers."""

import hashlib
from typing import Optional

from backend.app.integrations.supabase import get_supabase_client


def hash_ip_address(ip: str) -> str:
    """
    Hash an IP address using SHA-256 for privacy.

    Args:
        ip: The IP address to hash

    Returns:
        SHA-256 hash of the IP address
    """
    return hashlib.sha256(ip.encode()).hexdigest()


def check_vote_rate_limit(ip_hash: str) -> bool:
    """
    Check if a user has exceeded their vote rate limit (20 per hour).

    Args:
        ip_hash: SHA-256 hash of the user's IP address

    Returns:
        True if voting is allowed, False if rate limit exceeded
    """
    supabase = get_supabase_client()
    if not supabase:
        # Graceful degradation: allow if Supabase unavailable
        print(f"[Votes] WARNING: Supabase unavailable, allowing vote (no rate limiting)")
        return True

    try:
        result = supabase.rpc("check_vote_rate_limit", {"p_ip_hash": ip_hash}).execute()
        return result.data if result.data is not None else True
    except Exception as e:
        print(f"[Votes] Rate limit check error: {e}")
        # Graceful degradation: allow on error
        return True


def submit_vote(
    handle: str,
    platform: str,
    vote_type: str,
    voter_ip_hash: str,
    comment: Optional[str] = None,
) -> Optional[dict]:
    """
    Submit or update a vote for an influencer.

    If the user has already voted, this will update their existing vote (upsert).

    Args:
        handle: Influencer handle (without @ prefix)
        platform: Platform name (e.g., 'instagram')
        vote_type: 'trust' or 'distrust'
        voter_ip_hash: SHA-256 hash of voter's IP
        comment: Optional comment explaining the vote

    Returns:
        Vote record or None if failed
    """
    supabase = get_supabase_client()
    if not supabase:
        print("[Votes] ERROR: Supabase unavailable, cannot submit vote")
        return None

    try:
        data = {
            "influencer_handle": handle.lstrip("@"),
            "influencer_platform": platform,
            "vote_type": vote_type,
            "voter_ip_hash": voter_ip_hash,
            "comment": comment,
        }

        # Use upsert to update existing vote or insert new one
        result = supabase.table("influencer_votes").upsert(
            data,
            on_conflict="influencer_handle,influencer_platform,voter_ip_hash"
        ).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[Votes] Error submitting vote: {e}")
        return None


def get_user_vote(handle: str, platform: str, ip_hash: str) -> Optional[str]:
    """
    Get the current user's vote for an influencer.

    Args:
        handle: Influencer handle
        platform: Platform name
        ip_hash: SHA-256 hash of user's IP

    Returns:
        'trust', 'distrust', or None if no vote
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        result = supabase.rpc(
            "get_user_vote",
            {
                "p_handle": handle.lstrip("@"),
                "p_platform": platform,
                "p_ip_hash": ip_hash
            }
        ).execute()
        return result.data if result.data else None
    except Exception as e:
        print(f"[Votes] Error getting user vote: {e}")
        return None


def get_vote_stats(handle: str, platform: str) -> dict:
    """
    Get voting statistics for an influencer.

    Args:
        handle: Influencer handle
        platform: Platform name

    Returns:
        Dict with trust_votes, distrust_votes, total_votes, user_trust_score
    """
    supabase = get_supabase_client()
    if not supabase:
        return {
            "trust_votes": 0,
            "distrust_votes": 0,
            "total_votes": 0,
            "user_trust_score": 0.50,
        }

    try:
        # Get vote counts
        result = supabase.table("influencer_votes").select(
            "vote_type",
            count="exact"
        ).eq("influencer_handle", handle.lstrip("@")).eq("influencer_platform", platform).execute()

        if not result.data:
            return {
                "trust_votes": 0,
                "distrust_votes": 0,
                "total_votes": 0,
                "user_trust_score": 0.50,
            }

        # Count votes by type
        trust_votes = sum(1 for v in result.data if v.get("vote_type") == "trust")
        distrust_votes = sum(1 for v in result.data if v.get("vote_type") == "distrust")
        total_votes = len(result.data)

        # Calculate user trust score using the database function
        score_result = supabase.rpc(
            "calculate_user_trust_score",
            {"p_handle": handle.lstrip("@"), "p_platform": platform}
        ).execute()

        user_trust_score = float(score_result.data) if score_result.data is not None else 0.50

        return {
            "trust_votes": trust_votes,
            "distrust_votes": distrust_votes,
            "total_votes": total_votes,
            "user_trust_score": user_trust_score,
        }
    except Exception as e:
        print(f"[Votes] Error getting vote stats: {e}")
        return {
            "trust_votes": 0,
            "distrust_votes": 0,
            "total_votes": 0,
            "user_trust_score": 0.50,
        }


def update_marketplace_user_score(handle: str, platform: str) -> bool:
    """
    Update the user_trust_score and total_votes in marketplace_influencers table.

    This should be called after votes are submitted to keep the marketplace in sync.

    Args:
        handle: Influencer handle
        platform: Platform name

    Returns:
        True if successful, False otherwise
    """
    supabase = get_supabase_client()
    if not supabase:
        return False

    try:
        # Get vote stats
        stats = get_vote_stats(handle, platform)

        # Update marketplace record
        result = supabase.table("marketplace_influencers").update({
            "user_trust_score": stats["user_trust_score"],
            "total_votes": stats["total_votes"],
        }).eq("handle", handle.lstrip("@")).eq("platform", platform).execute()

        return result.data is not None and len(result.data) > 0
    except Exception as e:
        print(f"[Votes] Error updating marketplace user score: {e}")
        return False


def get_all_vote_stats(limit: int = 100, offset: int = 0) -> list:
    """
    Get voting statistics for all influencers.

    Args:
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        List of vote statistics
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        result = (
            supabase.from_("influencer_vote_stats")
            .select("*")
            .order("total_votes", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return result.data or []
    except Exception as e:
        print(f"[Votes] Error getting all vote stats: {e}")
        return []


def delete_vote(handle: str, platform: str, ip_hash: str) -> bool:
    """
    Delete a user's vote for an influencer.

    Args:
        handle: Influencer handle
        platform: Platform name
        ip_hash: SHA-256 hash of user's IP

    Returns:
        True if successful, False otherwise
    """
    supabase = get_supabase_client()
    if not supabase:
        return False

    try:
        result = supabase.table("influencer_votes").delete().eq(
            "influencer_handle", handle.lstrip("@")
        ).eq("influencer_platform", platform).eq("voter_ip_hash", ip_hash).execute()

        return result.data is not None
    except Exception as e:
        print(f"[Votes] Error deleting vote: {e}")
        return False
