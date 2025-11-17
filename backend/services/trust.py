"""Higher-level trust computation helpers."""

import math
from dataclasses import asdict
from typing import List, Optional

from backend.influencer_probe import get_instagram_stats
from backend.schemas import (
    CompanyTrustResponse,
    InfluencerStatsResponse,
    InfluencerTrustResponse,
    ProductTrustResponse,
    ScamPrediction,
)
from backend.services.mistral import (
    evaluate_company_reputation,
    evaluate_influencer_reputation,
    evaluate_product_reputation,
    mistral_scam_check,
)
from backend.services.snippets import (
    get_company_snippets,
    get_influencer_snippets,
    get_product_snippets,
)
from backend.supabase_client import (
    cache_company,
    cache_influencer,
    cache_product,
    get_cached_company,
    get_cached_influencer,
    get_cached_product,
)


def compute_message_history_score(sample_posts: List[str]) -> float:
    """
    Re-run the scam classifier on recent posts and derive a 0..1 score.
    """
    meaningful_posts = [text for text in sample_posts if text and text.strip()]
    if not meaningful_posts:
        return 0.5  # lack of evidence

    scores: List[float] = []
    for text in meaningful_posts:
        prediction: ScamPrediction = mistral_scam_check(text, debug=False)
        if prediction.label == "scam":
            val = 0.0
        elif prediction.label == "not_scam":
            val = 1.0
        else:
            val = 0.5
        scores.append(val)

    return sum(scores) / len(scores)


def compute_followers_score(
    followers: Optional[int],
    following: Optional[int],
) -> float:
    """
    Simple heuristic about follower volume and ratios.
    """
    if not followers or followers <= 0:
        return 0.5

    log_f = math.log10(max(followers, 1))
    followers_size_score = max(0.0, min(1.0, (log_f - 2) / 3))  # 100 -> 100k window

    ratio_score = 1.0
    if following is not None and followers > 0:
        ratio = following / followers
        if ratio > 1:
            ratio_score = max(0.0, 1.0 - (ratio - 1))

    return 0.7 * followers_size_score + 0.3 * ratio_score


def compute_disclosure_score(sample_posts: List[Optional[str]]) -> float:
    """
    Look for ad disclosure markers in recent captions.
    """
    if not sample_posts:
        return 0.3  # assume weak behavior when we cannot confirm

    markers = ("#ad", "#sponsored", "paid partnership")
    disclosures = 0
    total = 0
    for raw in sample_posts:
        if not raw:
            continue
        total += 1
        normalized = raw.lower()
        if any(marker in normalized for marker in markers):
            disclosures += 1

    if total == 0:
        return 0.3

    ratio = disclosures / total
    if ratio >= 0.6:
        return 1.0
    if ratio > 0:
        return 0.6
    return 0.3


def combine_trust_score(
    message_history_score: float,
    followers_score: float,
    web_reputation_score: float,
    disclosure_score: float,
) -> float:
    return (
        0.3 * message_history_score
        + 0.15 * followers_score
        + 0.4 * web_reputation_score
        + 0.15 * disclosure_score
    )


def label_from_trust_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


async def build_influencer_trust_response(
    handle: str,
    max_posts: int,
) -> InfluencerTrustResponse:
    cached_data = get_cached_influencer(handle, platform="instagram")
    if cached_data:
        try:
            return InfluencerTrustResponse(**cached_data)
        except Exception as exc:
            print(f"[Cache] Failed to parse cached influencer data: {exc}")

    stats_dc = get_instagram_stats(handle, max_posts=max_posts)
    stats = InfluencerStatsResponse(**asdict(stats_dc))

    mh_score = compute_message_history_score(stats.sample_posts or [])
    followers_score = compute_followers_score(stats.followers, stats.following)
    disclosure_score = compute_disclosure_score(stats.sample_posts or [])
    web_snippets = get_influencer_snippets(handle, stats.full_name)
    web_reputation = evaluate_influencer_reputation(handle, web_snippets)
    web_score = float(web_reputation.get("influencer_reliability", 0.5))

    trust_score = combine_trust_score(mh_score, followers_score, web_score, disclosure_score)
    label = label_from_trust_score(trust_score)

    recent_note = (
        "mostly safe" if mh_score > 0.7 else "mixed" if mh_score > 0.4 else "often risky"
    )
    follower_note = (
        "plausible" if followers_score > 0.7 else "unusual" if followers_score < 0.4 else "unclear"
    )
    disclosure_note = (
        "ads clearly disclosed" if disclosure_score >= 0.9
        else "disclosures are sporadic" if disclosure_score >= 0.6
        else "ads rarely flagged as sponsored"
    )
    web_note = web_reputation.get("summary") or "Little public information available."
    notes = (
        f"Recent posts look {recent_note}. "
        f"Followers profile looks {follower_note}. "
        f"Web reputation: {web_note} "
        f"Disclosure behavior: {disclosure_note}."
    )

    response = InfluencerTrustResponse(
        stats=stats,
        trust_score=trust_score,
        label=label,
        message_history_score=mh_score,
        followers_score=followers_score,
        web_reputation_score=web_score,
        disclosure_score=disclosure_score,
        notes=notes,
    )

    cache_influencer(handle, "instagram", response.model_dump())
    return response


def build_company_trust_response(
    name: str,
    max_results: int,
) -> CompanyTrustResponse:
    cached_data = get_cached_company(name)
    if cached_data:
        try:
            return CompanyTrustResponse(**cached_data)
        except Exception as exc:
            print(f"[Cache] Failed to parse cached company data: {exc}")

    snippets = get_company_snippets(name, max_results=max_results)
    reputation = evaluate_company_reputation(name, snippets)
    trust_score = float(reputation.get("company_reliability", 0.5))
    summary = reputation.get("summary") or "Insufficient public data."
    issues = reputation.get("issues") or []

    response = CompanyTrustResponse(
        name=name,
        trust_score=trust_score,
        summary=summary,
        issues=issues,
    )

    cache_company(name, response.model_dump())
    return response


def build_product_trust_response(
    name: str,
    max_results: int,
) -> ProductTrustResponse:
    cached_data = get_cached_product(name)
    if cached_data:
        try:
            return ProductTrustResponse(**cached_data)
        except Exception as exc:
            print(f"[Cache] Failed to parse cached product data: {exc}")

    snippets = get_product_snippets(name, max_results=max_results)
    reputation = evaluate_product_reputation(name, snippets)
    trust_score = float(reputation.get("product_reliability", 0.5))
    summary = reputation.get("summary") or "Insufficient public data."
    issues = reputation.get("issues") or []

    response = ProductTrustResponse(
        name=name,
        trust_score=trust_score,
        summary=summary,
        issues=issues,
    )

    cache_product(name, response.model_dump())
    return response

