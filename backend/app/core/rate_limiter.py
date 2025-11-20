"""Rate limiting for expensive API endpoints."""

from fastapi import HTTPException, Request

from backend.app.core.settings import get_settings
from backend.app.integrations.supabase import is_supabase_available
from backend.app.repositories import rate_limit as rate_limit_repo

settings = get_settings()
DAILY_LIMIT = settings.rate_limit_daily_limit


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP from the request.
    DO NOT trust X-Forwarded-For or other client-supplied headers in production.

    For local development, we'll use the direct client IP.
    In production behind a trusted proxy (like Cloudflare), you should:
    1. Configure the proxy to strip/overwrite X-Forwarded-For
    2. Use a signed header from the proxy
    3. Or use request.client.host as we do here
    """
    # Use the direct connection IP - this cannot be spoofed by the client
    if request.client and request.client.host:
        return request.client.host

    # Fallback to unknown (will be rate limited aggressively)
    return "unknown"


def check_rate_limit(request: Request, endpoint_group: str = "analysis") -> None:
    """
    Check if the client has exceeded their daily rate limit.
    Raises HTTPException(429) if limit exceeded.

    GRACEFUL DEGRADATION: If Supabase/rate limiting is unavailable, allows request
    with a warning log instead of blocking (fail open for better UX).

    Args:
        request: FastAPI request object
        endpoint_group: Category of endpoint (e.g., 'analysis', 'influencer', 'trust')

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    client_ip = get_client_ip(request)

    # GRACEFUL DEGRADATION: Allow requests if Supabase unavailable
    if not is_supabase_available():
        print(f"[RateLimit] WARNING: Supabase unavailable, allowing request from {client_ip} (no rate limiting)")
        return

    try:
        result = rate_limit_repo.check_and_increment_rate_limit(
            client_ip,
            endpoint_group,
            settings.rate_limit_daily_limit,
        )

        # GRACEFUL DEGRADATION: Allow if rate limit check fails
        if not result:
            print(f"[RateLimit] WARNING: Rate limit check failed, allowing request from {client_ip}")
            return

        if not result.get('allowed', False):
            remaining = max(0, DAILY_LIMIT - result.get('current_count', DAILY_LIMIT))
            reset_time = result.get('reset_at', 'unknown')

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": DAILY_LIMIT,
                    "remaining": remaining,
                    "reset_at": reset_time,
                    "message": f"You have exceeded the daily limit of {DAILY_LIMIT} requests. Please try again after {reset_time}."
                }
            )

    except HTTPException:
        # Re-raise HTTP exceptions (429)
        raise
    except Exception as e:
        # GRACEFUL DEGRADATION: Log error but allow request
        print(f"[RateLimit] WARNING: Rate limiting error, allowing request: {e}")
        return


def get_rate_limit_status(request: Request, endpoint_group: str = "analysis") -> dict:
    """
    Get current rate limit status for a client without incrementing.
    Returns info about remaining quota.

    Returns:
        dict with 'remaining', 'limit', 'reset_at' fields
    """
    client_ip = get_client_ip(request)

    if not is_supabase_available():
        return {
            'remaining': 0,
            'limit': DAILY_LIMIT,
            'reset_at': 'unknown',
            'error': 'Rate limiting unavailable'
        }

    try:
        data = rate_limit_repo.get_rate_limit_status(client_ip, endpoint_group)

        if data:
            remaining = max(0, DAILY_LIMIT - data.get('current_count', 0))
            return {
                'remaining': remaining,
                'limit': DAILY_LIMIT,
                'reset_at': data.get('reset_at', 'unknown')
            }

        # No existing record means full quota available
        return {
            'remaining': DAILY_LIMIT,
            'limit': DAILY_LIMIT,
            'reset_at': 'Not yet set'
        }

    except Exception as e:
        print(f"Error getting rate limit status: {e}")
        return {
            'remaining': 0,
            'limit': DAILY_LIMIT,
            'reset_at': 'unknown',
            'error': 'Could not retrieve status'
        }
