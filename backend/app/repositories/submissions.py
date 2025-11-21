"""Repository for user influencer submissions."""

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


def check_submission_rate_limit(ip_hash: str) -> bool:
    """
    Check if a user has exceeded their submission rate limit (3 per 24 hours).

    Args:
        ip_hash: SHA-256 hash of the user's IP address

    Returns:
        True if submission is allowed, False if rate limit exceeded
    """
    supabase = get_supabase_client()
    if not supabase:
        # Graceful degradation: allow if Supabase unavailable
        print(f"[Submissions] WARNING: Supabase unavailable, allowing submission (no rate limiting)")
        return True

    try:
        result = supabase.rpc("check_submission_rate_limit", {"p_ip_hash": ip_hash}).execute()
        return result.data if result.data is not None else True
    except Exception as e:
        print(f"[Submissions] Rate limit check error: {e}")
        # Graceful degradation: allow on error
        return True


def check_duplicate_submission(handle: str, platform: str) -> bool:
    """
    Check if an influencer has already been submitted recently (within 7 days).

    Args:
        handle: Influencer handle (without @ prefix)
        platform: Platform name (e.g., 'instagram')

    Returns:
        True if submission is allowed (no duplicate), False if duplicate exists
    """
    supabase = get_supabase_client()
    if not supabase:
        # Graceful degradation: allow if Supabase unavailable
        print(f"[Submissions] WARNING: Supabase unavailable, allowing submission (no duplicate check)")
        return True

    try:
        result = supabase.rpc(
            "check_duplicate_submission",
            {"p_handle": handle, "p_platform": platform}
        ).execute()
        return result.data if result.data is not None else True
    except Exception as e:
        print(f"[Submissions] Duplicate check error: {e}")
        # Graceful degradation: allow on error
        return True


def create_influencer_submission(
    handle: str,
    platform: str,
    submitter_ip_hash: str,
    reason: Optional[str] = None,
    submitter_session_hash: Optional[str] = None,
) -> Optional[dict]:
    """
    Create a new influencer submission.

    Args:
        handle: Influencer handle (without @ prefix)
        platform: Platform name (e.g., 'instagram')
        submitter_ip_hash: SHA-256 hash of submitter's IP
        reason: Optional reason for submission
        submitter_session_hash: Optional session hash

    Returns:
        Created submission record or None if failed
    """
    supabase = get_supabase_client()
    if not supabase:
        print("[Submissions] ERROR: Supabase unavailable, cannot create submission")
        return None

    try:
        data = {
            "handle": handle.lstrip("@"),
            "platform": platform,
            "submitter_ip_hash": submitter_ip_hash,
            "reason": reason,
            "submitter_session_hash": submitter_session_hash,
            "status": "pending",
        }

        result = supabase.table("influencer_submissions").insert(data).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[Submissions] Error creating submission: {e}")
        return None


def get_submission_by_id(submission_id: str) -> Optional[dict]:
    """
    Get a submission by ID.

    Args:
        submission_id: UUID of the submission

    Returns:
        Submission record or None if not found
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        result = supabase.table("influencer_submissions").select("*").eq("id", submission_id).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[Submissions] Error fetching submission: {e}")
        return None


def list_submissions(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """
    List influencer submissions with optional filtering.

    Args:
        status: Filter by status ('pending', 'analyzing', 'approved', 'rejected')
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        Dict with 'data' (list of submissions) and 'total' count
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"data": [], "total": 0}

    try:
        # Build query
        query = supabase.table("influencer_submissions").select("*", count="exact")

        if status:
            query = query.eq("status", status)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return {
            "data": result.data or [],
            "total": result.count or 0,
        }
    except Exception as e:
        print(f"[Submissions] Error listing submissions: {e}")
        return {"data": [], "total": 0}


def update_submission_status(
    submission_id: str,
    status: str,
    analysis_data: Optional[dict] = None,
    trust_score: Optional[float] = None,
    analysis_error: Optional[str] = None,
) -> Optional[dict]:
    """
    Update a submission's status and analysis results.

    Args:
        submission_id: UUID of the submission
        status: New status ('pending', 'analyzing', 'approved', 'rejected')
        analysis_data: Full analysis results as JSON
        trust_score: Automated trust score (0.00-1.00)
        analysis_error: Error message if analysis failed

    Returns:
        Updated submission record or None if failed
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        update_data = {"status": status}

        if analysis_data is not None:
            update_data["analysis_data"] = analysis_data

        if trust_score is not None:
            update_data["trust_score"] = trust_score
            update_data["analysis_completed_at"] = "now()"

        if analysis_error is not None:
            update_data["analysis_error"] = analysis_error

        result = supabase.table("influencer_submissions").update(update_data).eq("id", submission_id).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[Submissions] Error updating submission: {e}")
        return None


def review_submission(
    submission_id: str,
    status: str,
    reviewed_by: str,
    admin_notes: Optional[str] = None,
    rejection_reason: Optional[str] = None,
) -> Optional[dict]:
    """
    Review a submission (approve or reject).

    Args:
        submission_id: UUID of the submission
        status: New status ('approved' or 'rejected')
        reviewed_by: Admin username/identifier
        admin_notes: Admin's decision notes
        rejection_reason: Specific reason if rejected

    Returns:
        Updated submission record or None if failed
    """
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        update_data = {
            "status": status,
            "reviewed_by": reviewed_by,
            "reviewed_at": "now()",
            "admin_notes": admin_notes,
        }

        if rejection_reason:
            update_data["rejection_reason"] = rejection_reason

        result = supabase.table("influencer_submissions").update(update_data).eq("id", submission_id).execute()

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[Submissions] Error reviewing submission: {e}")
        return None


def get_user_submissions(ip_hash: str, limit: int = 10) -> list:
    """
    Get submissions from a specific user (by IP hash).

    Args:
        ip_hash: SHA-256 hash of user's IP address
        limit: Maximum number of results

    Returns:
        List of submission records
    """
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        result = (
            supabase.table("influencer_submissions")
            .select("*")
            .eq("submitter_ip_hash", ip_hash)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []
    except Exception as e:
        print(f"[Submissions] Error fetching user submissions: {e}")
        return []
