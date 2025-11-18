"""
Rate limiting for expensive API endpoints.
Uses IP-based tracking with daily quotas stored in Supabase.
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import Request, HTTPException
from supabase_client import supabase_client

# Daily request limit for expensive endpoints
DAILY_LIMIT = 10


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
    Raises HTTPException(429) if limit exceeded or on error (fail closed).

    Args:
        request: FastAPI request object
        endpoint_group: Category of endpoint (e.g., 'analysis', 'influencer', 'trust')

    Raises:
        HTTPException: 429 if rate limit exceeded, 503 if rate limiting system fails
    """
    client_ip = get_client_ip(request)

    # Check if Supabase is available
    if not supabase_client:
        # Fail closed: if we can't verify the rate limit, block the request
        raise HTTPException(
            status_code=503,
            detail="Rate limiting system unavailable. Please try again later."
        )

    try:
        # Call the Supabase RPC function to check and increment the rate limit
        result = supabase_client.rpc(
            'check_and_increment_rate_limit',
            {
                'p_client_ip': client_ip,
                'p_endpoint_group': endpoint_group,
                'p_daily_limit': DAILY_LIMIT
            }
        ).execute()

        if not result.data:
            # Fail closed: if we can't verify the rate limit, block the request
            raise HTTPException(
                status_code=503,
                detail="Rate limiting system unavailable. Please try again later."
            )

        response = result.data

        if not response.get('allowed', False):
            remaining = max(0, DAILY_LIMIT - response.get('current_count', DAILY_LIMIT))
            reset_time = response.get('reset_at', 'unknown')

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
        # Re-raise HTTP exceptions (429, 503)
        raise
    except Exception as e:
        # Fail closed: any unexpected error blocks the request
        print(f"Rate limiting error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Rate limiting system error. Please try again later."
        )


def get_rate_limit_status(request: Request, endpoint_group: str = "analysis") -> dict:
    """
    Get current rate limit status for a client without incrementing.
    Returns info about remaining quota.

    Returns:
        dict with 'remaining', 'limit', 'reset_at' fields
    """
    client_ip = get_client_ip(request)

    if not supabase_client:
        return {
            'remaining': 0,
            'limit': DAILY_LIMIT,
            'reset_at': 'unknown',
            'error': 'Rate limiting unavailable'
        }

    try:
        result = supabase_client.rpc(
            'get_rate_limit_status',
            {
                'p_client_ip': client_ip,
                'p_endpoint_group': endpoint_group
            }
        ).execute()

        if result.data:
            data = result.data
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
