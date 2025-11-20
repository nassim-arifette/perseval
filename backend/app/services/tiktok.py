"""TikTok helpers (optional) for pulling captions via TikTokApi."""

import os
from typing import Dict, Any

from fastapi import HTTPException

try:
    # Optional dependency used for TikTok URL support
    from TikTokApi import TikTokApi  # type: ignore
except ImportError:  # pragma: no cover - optional feature
    TikTokApi = None  # type: ignore


async def get_tiktok_video_info(url: str) -> Dict[str, Any]:
    """
    Fetch basic info for a TikTok video using TikTokApi.

    Returns a dict with at least:
        - caption: str
        - username: Optional[str]
        - nickname: Optional[str]
        - followers: Optional[int]
        - verified: bool
    """
    if TikTokApi is None:  # type: ignore[name-defined]
        raise HTTPException(
            status_code=500,
            detail="TikTok support is not available. Install the 'TikTokApi' package to enable it.",
        )

    ms_token = os.environ.get("TIKTOK_MS_TOKEN") or os.environ.get("ms_token")
    if not ms_token:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing TikTok session cookie. Set TIKTOK_MS_TOKEN (or ms_token) "
                "in the backend environment to enable TikTok URL analysis."
            ),
        )

    try:
        async with TikTokApi() as api:  # type: ignore[operator]
            await api.create_sessions(
                ms_tokens=[ms_token],
                num_sessions=1,
                sleep_after=3,
            )
            video = api.video(url=url)
            data = await video.info()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network / TikTok specific
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch TikTok video: {exc}",
        ) from exc

    author = data.get("author") or {}
    stats = author.get("stats") or {}
    return {
        "caption": data.get("desc", "") or "",
        "username": author.get("uniqueId"),
        "nickname": author.get("nickname"),
        "followers": stats.get("followerCount"),
        "verified": bool(author.get("verified", False)),
    }

