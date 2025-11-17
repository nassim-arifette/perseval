"""
Supabase client for caching influencer, company, and product analysis results.
"""
import os
import json
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
