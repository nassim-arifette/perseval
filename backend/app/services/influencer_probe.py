#!/usr/bin/env python3
"""
influencer_probe.py

Minimal CLI to fetch basic stats for an influencer on Instagram via Instaloader.
(Twitter/X scraping is temporarily disabled in this build.)

Usage example:
    python influencer_probe.py instagram --handle healthyfit_queen
"""

import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urlparse

# Instagram
import instaloader

# # X / Twitter (temporarily disabled)
# from twscrape import API, gather
# from twscrape.logger import set_log_level


@dataclass
class InfluencerStats:
    platform: str
    handle: str
    full_name: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    posts_count: Optional[int] = None
    is_verified: Optional[bool] = None
    bio: Optional[str] = None
    url: Optional[str] = None
    sample_posts: Optional[List[str]] = None


# ---------- Instagram ----------

def _create_instaloader() -> instaloader.Instaloader:
    return instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_comments=False,
        download_geotags=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
    )


def get_instagram_stats(handle: str, max_posts: int = 5) -> InfluencerStats:
    """
    Fetch basic profile info + a few recent captions for an Instagram user.
    """
    username = handle.lstrip("@")
    loader = _create_instaloader()
    profile = instaloader.Profile.from_username(loader.context, username)

    sample_posts: List[str] = []
    for i, post in enumerate(profile.get_posts()):
        if i >= max_posts:
            break
        if post.caption:
            sample_posts.append(post.caption[:300])  # truncate to avoid huge blobs

    return InfluencerStats(
        platform="instagram",
        handle=profile.username,
        full_name=profile.full_name or None,
        followers=profile.followers,
        following=profile.followees,
        posts_count=profile.mediacount,
        is_verified=profile.is_verified,
        bio=profile.biography or None,
        url=f"https://www.instagram.com/{profile.username}/",
        sample_posts=sample_posts or None,
    )


def get_instagram_post_from_url(url: str) -> instaloader.Post:
    """
    Given an Instagram post/reel URL, return the Instaloader Post object.
    """
    loader = _create_instaloader()
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if len(path_parts) < 2:
        raise ValueError(f"Cannot extract shortcode from URL: {url}")

    shortcode = path_parts[1]
    return instaloader.Post.from_shortcode(loader.context, shortcode)


# ---------- Twitter / X ----------
#
# async def get_twitter_stats_async(
#     handle: str,
#     max_tweets: int = 5,
#     accounts_db: str = "accounts.db",
# ) -> InfluencerStats:
#     """
#     Fetch basic profile info + a few recent tweets for a Twitter/X user using twscrape.
#
#     NOTE: This assumes you already have at least one account stored in accounts.db.
#     See README in twscrape or the notes at the bottom of this file.
#     """
#     set_log_level("WARNING")  # be quiet
#
#     # API() will use the default accounts.db in current directory if not specified
#     api = API(accounts_db)
#     login = handle.lstrip("@")
#     user = await api.user_by_login(login)
#     user_dict = user.dict()
#
#     followers = user_dict.get("followersCount") or user_dict.get("followers_count")
#     following = user_dict.get("friendsCount") or user_dict.get("friends_count")
#     statuses = user_dict.get("statusesCount") or user_dict.get("statuses_count")
#     verified = user_dict.get("verified")
#     full_name = user_dict.get("name")
#     bio = user_dict.get("description")
#     url = f"https://x.com/{user_dict.get('username', login)}"
#
#     # Latest tweets
#     tweets_text: List[str] = []
#     user_id = user_dict.get("id") or user_dict.get("rest_id")
#     if user_id is not None:
#         # gather() collects the async generator into a list
#         tweets = await gather(api.user_tweets(user_id, limit=max_tweets))
#         for tw in tweets:
#             # Tweet model also has .dict() if you prefer
#             text = getattr(tw, "rawContent", None) or getattr(tw, "fullText", None)
#             if text:
#                 tweets_text.append(text[:300])
#
#     return InfluencerStats(
#         platform="twitter",
#         handle=login,
#         full_name=full_name or None,
#         followers=followers,
#         following=following,
#         posts_count=statuses,
#         is_verified=bool(verified) if verified is not None else None,
#         bio=bio or None,
#         url=url,
#         sample_posts=tweets_text or None,
#     )

async def get_twitter_stats_async(
    handle: str,
    max_tweets: int = 5,
    accounts_db: str = "accounts.db",
) -> InfluencerStats:
    """
    Placeholder while Twitter/X scraping is disabled.
    """
    raise NotImplementedError(
        "Twitter/X scraping is temporarily disabled. Uncomment the section above to restore."
    )


# ---------- CLI & main ----------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch basic stats for an influencer (Instagram only for now)."
    )
    parser.add_argument(
        "platform",
        choices=["instagram"],
        help="Target platform (Instagram only while Twitter is disabled).",
    )
    parser.add_argument(
        "--handle",
        required=True,
        help="Username / handle (without @ or with @, both are fine).",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=5,
        help="Number of recent posts/tweets to fetch (default: 5).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.platform == "instagram":
        stats = get_instagram_stats(args.handle, max_posts=args.max_posts)
        data = asdict(stats)
        print(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False))
    else:
        raise SystemExit("Twitter/X scraping is commented out for now.")


if __name__ == "__main__":
    main()
