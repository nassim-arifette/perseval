"""Seed the Supabase marketplace table with baseline influencer data."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.supabase_client import supabase_client

if supabase_client is None:
    print("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in backend/.env.")
    sys.exit(1)


def trust_label_from_score(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


PLATFORM_URL_PATTERNS = {
    "instagram": "https://www.instagram.com/{handle}",
    "tiktok": "https://www.tiktok.com/@{handle}",
    "youtube": "https://www.youtube.com/@{handle}",
    "twitch": "https://www.twitch.tv/{handle}",
    "x": "https://x.com/{handle}",
    "facebook": "https://www.facebook.com/{handle}",
}


def profile_url_for(handle: str, platform: str) -> Optional[str]:
    template = PLATFORM_URL_PATTERNS.get(platform.lower())
    return template.format(handle=handle) if template else None


SEED_INFLUENCERS: List[Dict[str, Any]] = [
    {
        "handle": "cristiano",
        "display_name": "Cristiano Ronaldo",
        "platform": "instagram",
        "score": 88,
        "niche": "Sports, lifestyle, big brand collabs",
        "summary": "Global football star with huge reach; posts are mostly lifestyle and major brand partnerships (Nike, luxury, etc.).",
        "is_featured": True,
    },
    {
        "handle": "leomessi",
        "display_name": "Lionel Messi",
        "platform": "instagram",
        "score": 86,
        "niche": "Sports, lifestyle",
        "summary": "Massive football audience; classic big-brand deals across sportswear and beverages.",
        "is_featured": True,
    },
    {
        "handle": "kyliejenner",
        "display_name": "Kylie Jenner",
        "platform": "instagram",
        "score": 80,
        "niche": "Beauty, fashion, Kylie Cosmetics",
        "summary": "Beauty mogul and Kardashian-Jenner member; powerful for launches but feed is strongly commercial.",
        "is_featured": True,
    },
    {
        "handle": "kimkardashian",
        "display_name": "Kim Kardashian",
        "platform": "instagram",
        "score": 70,
        "niche": "Beauty, fashion, lifestyle",
        "summary": "Huge reach with mainstream brands; fined by SEC for an undisclosed crypto promotion so treat finance posts carefully.",
        "issues": ["SEC fine for inadequate crypto promotion disclosure in 2022."],
    },
    {
        "handle": "khaby.lame",
        "display_name": "Khaby Lame",
        "platform": "tiktok",
        "score": 85,
        "niche": "Comedy, reaction videos",
        "summary": "Known for silent reaction skits and mocking over-complicated life hacks; generally brand-safe humor.",
    },
    {
        "handle": "mrbeast",
        "display_name": "MrBeast",
        "platform": "youtube",
        "score": 90,
        "niche": "Stunts, philanthropy, consumer brands",
        "summary": "Massive YouTuber with large-scale challenge videos and philanthropy; data-driven collabs like Feastables.",
        "is_featured": True,
    },
    {
        "handle": "charlidamelio",
        "display_name": "Charli D'Amelio",
        "platform": "tiktok",
        "score": 78,
        "niche": "Dance, lifestyle",
        "summary": "TikTok dance star turned mainstream creator mixing fashion, TV spots, and sponsorships.",
    },
    {
        "handle": "dixiedamelio",
        "display_name": "Dixie D'Amelio",
        "platform": "tiktok",
        "score": 76,
        "niche": "Music, lifestyle",
        "summary": "Music-focused creator from the D'Amelio family with modeling, fashion, and sponsored content.",
    },
    {
        "handle": "addisonraee",
        "display_name": "Addison Rae",
        "platform": "tiktok",
        "score": 73,
        "niche": "Dance, beauty, acting",
        "summary": "Early TikTok star with beauty and fashion partnerships; strong reach with a young audience.",
    },
    {
        "handle": "naraazizasmith",
        "display_name": "Nara Smith",
        "platform": "tiktok",
        "score": 84,
        "niche": "Aesthetic cooking, lifestyle",
        "summary": "Soft-spoken cooking videos in luxury settings and collaborations with high-end fashion brands.",
    },
    {
        "handle": "hudabeauty",
        "display_name": "Huda Kattan",
        "platform": "instagram",
        "score": 83,
        "niche": "Beauty, cosmetics brand founder",
        "summary": "Founder of Huda Beauty with long-term credibility in makeup tutorials and product launches.",
    },
    {
        "handle": "nikkietutorials",
        "display_name": "NikkieTutorials",
        "platform": "youtube",
        "score": 86,
        "niche": "Beauty, LGBTQ+ advocate",
        "summary": "Veteran beauty YouTuber, generally transparent about sponsorships and product opinions.",
    },
    {
        "handle": "jamescharles",
        "display_name": "James Charles",
        "platform": "youtube",
        "score": 60,
        "niche": "Beauty",
        "summary": "Extremely influential but carries multiple public controversies; evaluate risk tolerance.",
        "issues": ["Multiple public controversies involving behavior and brand conflicts."],
    },
    {
        "handle": "pewdiepie",
        "display_name": "PewDiePie",
        "platform": "youtube",
        "score": 77,
        "niche": "Gaming, commentary",
        "summary": "Legacy YouTuber; past controversies but now more lifestyle focused.",
        "issues": ["History of commentary controversies; currently lower activity."],
    },
    {
        "handle": "mkbhd",
        "display_name": "Marques Brownlee",
        "platform": "youtube",
        "score": 92,
        "niche": "Tech reviews",
        "summary": "Highly trusted for in-depth, relatively unbiased tech reviews; go-to for serious product analysis.",
        "is_featured": True,
    },
    {
        "handle": "caseyneistat",
        "display_name": "Casey Neistat",
        "platform": "youtube",
        "score": 82,
        "niche": "Vlogs, filmmaking",
        "summary": "Iconic daily vlogger with strong storytelling who partners with mainstream brands.",
    },
    {
        "handle": "kaicenat",
        "display_name": "Kai Cenat",
        "platform": "twitch",
        "score": 68,
        "niche": "Streaming, gaming, IRL",
        "summary": "Huge streamer with chaotic IRL content; great Gen-Z pull but tone can be edgy.",
        "issues": ["Chaotic IRL streams can conflict with conservative brand guidelines."],
    },
    {
        "handle": "loganpaul",
        "display_name": "Logan Paul",
        "platform": "youtube",
        "score": 55,
        "niche": "Entertainment, boxing, Prime",
        "summary": "Prime co-founder with massive reach; CryptoZoo saga cleared in court but remains reputational baggage.",
        "issues": ["CryptoZoo/NFT backlash and periodic controversies."],
    },
    {
        "handle": "ksi",
        "display_name": "KSI",
        "platform": "youtube",
        "score": 75,
        "niche": "Gaming, music, boxing, Prime",
        "summary": "Long-time YouTuber and Prime co-founder; loud persona yet usually brand-compatible.",
    },
    {
        "handle": "bellapoarch",
        "display_name": "Bella Poarch",
        "platform": "tiktok",
        "score": 79,
        "niche": "Music, short-form content",
        "summary": "Went from viral lip-syncs to music; lots of beauty and fashion sponsorships.",
    },
    {
        "handle": "zachking",
        "display_name": "Zach King",
        "platform": "tiktok",
        "score": 89,
        "niche": "Visual magic, family-friendly",
        "summary": "Magic vines and clever edits; extremely family-friendly and brand-safe.",
        "is_featured": True,
    },
    {
        "handle": "emmachamberlain",
        "display_name": "Emma Chamberlain",
        "platform": "youtube",
        "score": 82,
        "niche": "Lifestyle, fashion, coffee",
        "summary": "Strong parasocial connection; fashion collaborations plus her coffee brand.",
    },
    {
        "handle": "chiaraferragni",
        "display_name": "Chiara Ferragni",
        "platform": "instagram",
        "score": 65,
        "niche": "Fashion, luxury, entrepreneur",
        "summary": "Pioneer fashion blogger with luxury deals; recent Italy charity/tax controversy introduced noise.",
        "issues": ["Under scrutiny in Italy for charity/tax controversy tied to her brand."],
    },
    {
        "handle": "sssniperwolf",
        "display_name": "SSSniperWolf",
        "platform": "youtube",
        "score": 58,
        "niche": "Reaction, gaming",
        "summary": "Massive reaction channel; drama around other creators makes brands cautious.",
        "issues": ["Recent doxxing/creator conflicts raised brand-safety concerns."],
    },
    {
        "handle": "ishowspeed",
        "display_name": "IShowSpeed",
        "platform": "youtube",
        "score": 52,
        "niche": "Streaming, gaming, IRL",
        "summary": "High-energy streamer with repeated on-stream controversies; volatile for conservative brands.",
        "issues": ["Frequent on-stream controversies and unpredictable behavior."],
    },
    {
        "handle": "hasanabi",
        "display_name": "HasanAbi",
        "platform": "twitch",
        "score": 62,
        "niche": "Political commentary",
        "summary": "Left-leaning political streamer; extremely engaged but polarizing.",
        "issues": ["Polarizing political commentary can alienate segments of the audience."],
    },
    {
        "handle": "alexandracooper",
        "display_name": "Alex Cooper",
        "platform": "podcast",
        "score": 74,
        "niche": "Relationships, lifestyle",
        "summary": "Host of Call Her Daddy; edgy tone with strong audience trust.",
        "issues": ["Explicit topics may not align with conservative brands."],
    },
    {
        "handle": "lorengray",
        "display_name": "Loren Gray",
        "platform": "tiktok",
        "score": 76,
        "niche": "Music, beauty",
        "summary": "Early TikTok/Musical.ly star focusing on music and beauty sponsorships.",
    },
    {
        "handle": "selenagomez",
        "display_name": "Selena Gomez",
        "platform": "instagram",
        "score": 90,
        "niche": "Music, beauty, advocacy",
        "summary": "Among the most-followed Instagram accounts; balances music, advocacy, and Rare Beauty.",
        "is_featured": True,
    },
    {
        "handle": "cobratate",
        "display_name": "Andrew Tate",
        "platform": "x",
        "score": 35,
        "niche": "Self-help, masculinity coaching",
        "summary": "Extremely polarizing figure with frequent bans; marketplace flags as low trust.",
        "issues": ["Ongoing legal issues, deplatforming history, and extreme rhetoric."],
    },
    {
        "handle": "squeezie",
        "display_name": "Squeezie (Lucas Hauchard)",
        "platform": "youtube",
        "score": 88,
        "niche": "Entertainment, gaming, large IRL concepts",
        "summary": "Top French YouTuber producing massive IRL concepts, gaming, GP Explorer, and frequent charity collaborations.",
        "is_featured": True,
    },
    {
        "handle": "tiboinshape",
        "display_name": "Tibo InShape",
        "platform": "youtube",
        "score": 80,
        "niche": "Fitness, lifestyle, shorts",
        "summary": "#1 French YouTube fitness creator with hyper-energetic institutional vlogs and InShape Nutrition brand.",
    },
    {
        "handle": "cyprien",
        "display_name": "Cyprien",
        "platform": "youtube",
        "score": 84,
        "niche": "Comedy, short films",
        "summary": "Historic French YouTube comedian producing sketches and short films like \"Roger et ses humains.\"",
    },
    {
        "handle": "michou",
        "display_name": "Michou",
        "platform": "youtube",
        "score": 86,
        "niche": "Gaming, vlogs, music",
        "summary": "Mainstream Team Croûton member moving from Fortnite to large IRL shows and new ventures like a restaurant.",
        "is_featured": True,
    },
    {
        "handle": "inoxtag",
        "display_name": "Inoxtag",
        "platform": "youtube",
        "score": 87,
        "niche": "Challenges, travel, outdoor",
        "summary": "Large-scale challenge specialist (Everest Kaizen, Atlantic crossing) inspiring teens toward outdoor adventures.",
        "is_featured": True,
    },
    {
        "handle": "amixem",
        "display_name": "Amixem",
        "platform": "youtube",
        "score": 83,
        "niche": "Vlogs, humor, experiments",
        "summary": "French entertainer mixing travel, wacky challenges, and entrepreneurship with Spacefox and restaurant ventures.",
    },
    {
        "handle": "mcflyetcarlito",
        "display_name": "McFly & Carlito",
        "platform": "youtube",
        "score": 78,
        "niche": "Comedy duo, challenges",
        "summary": "Comedy duo behind \"histoires de darons\" and mainstream challenge videos including public-health collaborations.",
    },
    {
        "handle": "seblafrite",
        "display_name": "SEB (Seb la Frite)",
        "platform": "youtube",
        "score": 85,
        "niche": "Humor, docu-style, rap",
        "summary": "Veteran YouTuber blending humor, doc-style projects, and rap explorations like \"L'Histoire du rap.\"",
    },
    {
        "handle": "yvick",
        "display_name": "Mister V (Yvick)",
        "platform": "youtube",
        "score": 84,
        "niche": "Comedy, rap",
        "summary": "First-gen French YouTuber turned rapper, mixing sketches, albums, and brand collabs in food and sneakers.",
    },
    {
        "handle": "gotaga",
        "display_name": "Gotaga",
        "platform": "twitch",
        "score": 88,
        "niche": "Esports, FPS, variety",
        "summary": "Former pro Call of Duty player and Gentlemates founder; mainstay of charity streams like Z Event.",
        "is_featured": True,
    },
    {
        "handle": "enjoyphoenix",
        "display_name": "EnjoyPhoenix (Marie Lopez)",
        "platform": "youtube",
        "score": 82,
        "niche": "Beauty, lifestyle, mental health",
        "summary": "OG beauty creator turned entrepreneur (Leaves & Clouds) now covering eco-lifestyle and mental health on Twitch.",
    },
    {
        "handle": "natoo",
        "display_name": "Natoo",
        "platform": "youtube",
        "score": 82,
        "niche": "Comedy, lifestyle",
        "summary": "Long-running comedic YouTuber mixing sketches, lifestyle content, and mainstream collaborations in France.",
    },
]


def build_records() -> List[Dict[str, Any]]:
    timestamp = datetime.now(timezone.utc).isoformat()
    records: List[Dict[str, Any]] = []
    for entry in SEED_INFLUENCERS:
        handle = entry["handle"].lstrip("@").lower()
        platform = entry["platform"].lower()
        score = float(entry["score"])
        record: Dict[str, Any] = {
            "handle": handle,
            "platform": platform,
            "display_name": entry["display_name"],
            "bio": entry.get("niche"),
            "profile_url": profile_url_for(handle, platform),
            "overall_trust_score": round(score / 100, 2),
            "trust_label": entry.get("trust_label", trust_label_from_score(int(score))),
            "analysis_summary": entry.get("summary"),
            "issues": entry.get("issues", []),
            "last_analyzed_at": entry.get("last_analyzed_at", timestamp),
            "added_to_marketplace_at": entry.get("added_to_marketplace_at", timestamp),
            "is_featured": entry.get("is_featured", False),
            "is_verified": True,
            "admin_notes": "Seeded via backend/seed_marketplace.py",
        }
        records.append(record)
    return records


def main() -> None:
    records = build_records()
    response = supabase_client.table("marketplace_influencers").upsert(
        records, on_conflict="handle,platform"
    ).execute()
    count = len(response.data) if response.data else 0
    print(f"Upserted {count} marketplace influencers.")


if __name__ == "__main__":
    main()
