"""FastAPI routes for the Perseval backend."""

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Header
from rate_limiter import check_rate_limit

from influencer_probe import (
    get_instagram_post_from_url,
    get_instagram_stats,
)
from schemas import (
    CompanyTrustRequest,
    CompanyTrustResponse,
    FullAnalysisRequest,
    FullAnalysisResponse,
    FullAnalysisSource,
    InfluencerStatsRequest,
    InfluencerStatsResponse,
    InfluencerTrustResponse,
    InstagramPostAnalyzeRequest,
    ProductTrustRequest,
    ProductTrustResponse,
    ScamPrediction,
    TextAnalyzeRequest,
    MarketplaceInfluencer,
    AddToMarketplaceRequest,
    MarketplaceListRequest,
    MarketplaceListResponse,
    UserFeedbackRequest,
    UserFeedbackResponse,
)
from services.mistral import (
    detect_company_and_product_from_text,
    mistral_scam_check,
)
from services.tiktok import get_tiktok_video_info
from services.trust import (
    build_company_trust_response,
    build_influencer_trust_response,
    build_product_trust_response,
)
from supabase_client import (
    add_influencer_to_marketplace,
    get_marketplace_influencer,
    list_marketplace_influencers,
    remove_from_marketplace,
    is_cache_available,
    check_feedback_rate_limit,
    submit_user_feedback,
    get_newsletter_subscribers,
)

router = APIRouter()


def verify_admin_auth(authorization: Optional[str]) -> None:
    """
    Verify admin authentication via Authorization header.

    SECURITY: Requires Bearer token matching ADMIN_API_KEY env var.
    Uses constant-time comparison to prevent timing attacks.

    Args:
        authorization: Authorization header value

    Raises:
        HTTPException: 401 if unauthorized, 501 if not configured
    """
    import os
    import hmac

    admin_api_key = os.getenv("ADMIN_API_KEY")

    if not admin_api_key:
        raise HTTPException(
            status_code=501,
            detail="Admin authentication not configured. Set ADMIN_API_KEY in .env file.",
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Authorization header required. Use: 'Authorization: Bearer YOUR_API_KEY'",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use: 'Authorization: Bearer YOUR_API_KEY'",
        )

    provided_key = authorization.replace("Bearer ", "").strip()

    # SECURITY: Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_key, admin_api_key):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized. Invalid API key.",
        )


@router.post("/analyze/text", response_model=ScamPrediction)
def analyze_text(req: TextAnalyzeRequest, request: Request):
    """
    Accept pasted text directly and evaluate whether it looks like a scam or not.
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="analysis")

    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Text to analyze cannot be empty.")

    prediction = mistral_scam_check(cleaned_text)
    return prediction


@router.post("/influencer/stats", response_model=InfluencerStatsResponse)
async def influencer_stats(req: InfluencerStatsRequest, request: Request):
    """
    Fetch influencer metadata + sample posts via Instaloader (Instagram only for now).
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="influencer")

    handle = req.handle.strip()
    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty.")

    try:
        stats = get_instagram_stats(handle, max_posts=req.max_posts)
        return InfluencerStatsResponse(**asdict(stats))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch {req.platform} stats: {exc}",
        ) from exc


@router.post("/influencer/trust", response_model=InfluencerTrustResponse)
async def influencer_trust(req: InfluencerStatsRequest, request: Request):
    """
    Return influencer stats plus a composite trust score.
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="influencer")

    handle = req.handle.strip()
    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty.")

    try:
        return await build_influencer_trust_response(handle, max_posts=req.max_posts)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch {req.platform} stats: {exc}",
        ) from exc


@router.post("/company/trust", response_model=CompanyTrustResponse)
def company_trust(req: CompanyTrustRequest, request: Request):
    """
    Use Serper + Mistral to estimate overall company reputation.
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="trust")

    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    return build_company_trust_response(name, max_results=req.max_results)


@router.post("/product/trust", response_model=ProductTrustResponse)
def product_trust(req: ProductTrustRequest, request: Request):
    """
    Use Serper + Mistral to estimate product-level reliability.
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="trust")

    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name cannot be empty.")

    return build_product_trust_response(name, max_results=req.max_results)


@router.get("/")
def root():
    return {"status": "ok", "message": "Scam checker API running"}


@router.post("/analyze/full", response_model=FullAnalysisResponse)
async def analyze_full(req: FullAnalysisRequest, request: Request):
    """
    Unified endpoint: accept raw text and/or Instagram URL, optionally enrich with influencer + company trust.
    Rate limited to 10 requests per day per IP.
    """
    # Check rate limit before processing expensive request
    check_rate_limit(request, endpoint_group="analysis")

    text = (req.text or "").strip()
    influencer_handle = (req.influencer_handle or "").strip() or None
    source_details: FullAnalysisSource = FullAnalysisSource(text_origin="input")

    if req.instagram_url and req.tiktok_url:
        raise HTTPException(
            status_code=400,
            detail="Provide either an Instagram URL or a TikTok URL, not both.",
        )

    if req.instagram_url:
        try:
            post = get_instagram_post_from_url(str(req.instagram_url))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch Instagram post: {exc}",
            ) from exc

        caption = (post.caption or "").strip()
        source_details = FullAnalysisSource(
            text_origin="instagram",
            instagram_url=str(req.instagram_url),
            instagram_owner=post.owner_username,
        )
        if caption:
            text = caption
        elif not text:
            raise HTTPException(
                status_code=400,
                detail="Instagram post has no caption and no fallback text was provided.",
            )
        if not influencer_handle:
            influencer_handle = post.owner_username

    if req.tiktok_url:
        try:
            video_info = await get_tiktok_video_info(str(req.tiktok_url))
        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch TikTok video: {exc}",
            ) from exc

        caption = (video_info.get("caption") or "").strip()
        source_details = FullAnalysisSource(
            text_origin="tiktok",
            tiktok_url=str(req.tiktok_url),
            tiktok_author=video_info.get("username"),
        )
        if caption:
            text = caption
        elif not text:
            raise HTTPException(
                status_code=400,
                detail="TikTok video has no caption and no fallback text was provided.",
            )

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Provide message text, an Instagram URL, or a TikTok URL.",
        )

    prediction = mistral_scam_check(text, debug=False)

    influencer_trust: Optional[InfluencerTrustResponse] = None
    if influencer_handle:
        try:
            influencer_trust = await build_influencer_trust_response(
                influencer_handle,
                max_posts=req.max_posts,
            )

            # Automatically add influencer to marketplace after analysis
            if influencer_trust and is_cache_available():
                try:
                    # Prepare profile and trust data
                    profile_data = {
                        "full_name": influencer_trust.stats.full_name,
                        "bio": influencer_trust.stats.bio,
                        "url": influencer_trust.stats.url,
                        "followers": influencer_trust.stats.followers,
                        "following": influencer_trust.stats.following,
                        "posts_count": influencer_trust.stats.posts_count,
                        "is_verified": influencer_trust.stats.is_verified,
                    }

                    trust_data = {
                        "trust_score": influencer_trust.trust_score,
                        "label": influencer_trust.label,
                        "message_history_score": influencer_trust.message_history_score,
                        "followers_score": influencer_trust.followers_score,
                        "web_reputation_score": influencer_trust.web_reputation_score,
                        "disclosure_score": influencer_trust.disclosure_score,
                        "notes": influencer_trust.notes,
                        "issues": [],
                    }

                    # Add to marketplace (will update if already exists)
                    add_influencer_to_marketplace(
                        handle=influencer_handle,
                        platform="instagram",  # Default to Instagram for now
                        profile_data=profile_data,
                        trust_data=trust_data,
                        admin_notes=None,
                        is_featured=False,
                    )
                except Exception:
                    # Silently fail marketplace addition - don't break the analysis flow
                    pass

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build influencer trust: {exc}",
            ) from exc

    inferred_company = None
    inferred_product = None
    company_name = (req.company_name or "").strip() or None
    product_name = (req.product_name or "").strip() or None
    detected_company = None
    detected_product = None
    if not company_name or not product_name:
        detected_company, detected_product = detect_company_and_product_from_text(text)
    if not company_name and detected_company:
        inferred_company = detected_company
        company_name = detected_company
    if not product_name and detected_product:
        inferred_product = detected_product
        product_name = detected_product
    company_trust: Optional[CompanyTrustResponse] = None
    if company_name:
        try:
            company_trust = build_company_trust_response(
                company_name,
                max_results=req.company_max_results,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build company trust: {exc}",
            ) from exc
    product_trust: Optional[ProductTrustResponse] = None
    if product_name:
        try:
            product_trust = build_product_trust_response(
                product_name,
                max_results=req.product_max_results,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to build product trust: {exc}",
            ) from exc
    source_details.inferred_company_name = inferred_company
    source_details.inferred_product_name = inferred_product

    summary_parts: List[str] = []
    summary_parts.append(
        f"Message assessment: {prediction.label.replace('_', ' ')} — {prediction.reason or 'no additional context'}."
    )
    if influencer_trust:
        summary_parts.append(
            f"Influencer trust: {influencer_trust.label} ({int(influencer_trust.trust_score * 100)}%). {influencer_trust.notes}"
        )
    if company_trust:
        summary_parts.append(
            f"Company reputation ({company_name}): {int(company_trust.trust_score * 100)}%. {company_trust.summary}"
        )
    elif company_name:
        summary_parts.append(f"Company mentioned ({company_name}) but reputation lookup failed.")
    if product_trust:
        summary_parts.append(
            f"Product reliability ({product_name}): {int(product_trust.trust_score * 100)}%. {product_trust.summary}"
        )
    elif product_name:
        summary_parts.append(f"Product mentioned ({product_name}) but reliability lookup failed.")
    if not company_name and not product_name:
        summary_parts.append("No clear company or product was detected in the content.")
    final_summary = " ".join(summary_parts).strip()

    return FullAnalysisResponse(
        message_prediction=prediction,
        influencer_trust=influencer_trust,
        company_trust=company_trust,
        product_trust=product_trust,
        source_details=source_details,
        final_summary=final_summary,
    )


@router.post("/instagram/post/analyze", response_model=ScamPrediction)
def analyze_instagram_post(req: InstagramPostAnalyzeRequest):
    """
    Given a public Instagram post URL, fetch its caption via Instaloader and run the scam checker.
    """
    try:
        post = get_instagram_post_from_url(str(req.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - instaloader-specific failures
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch Instagram post: {exc}",
        ) from exc

    caption = (post.caption or "").strip()
    if not caption:
        raise HTTPException(
            status_code=400,
            detail="This Instagram post has no caption to analyze.",
        )

    return mistral_scam_check(caption)


# Marketplace endpoints
@router.get("/marketplace/influencers", response_model=MarketplaceListResponse)
def list_marketplace(
    search: Optional[str] = None,
    trust_level: Optional[str] = None,
    sort_by: str = "trust_score",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
):
    """
    List marketplace influencers with filtering, sorting, and pagination.
    """
    if not is_cache_available():
        raise HTTPException(
            status_code=503,
            detail="Marketplace is not available. Supabase must be configured to use marketplace features.",
        )

    result = list_marketplace_influencers(
        search=search,
        trust_level=trust_level,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    # Convert database records to MarketplaceInfluencer models
    influencers = [
        MarketplaceInfluencer(
            id=str(record["id"]),
            handle=record["handle"],
            platform=record["platform"],
            display_name=record.get("display_name"),
            bio=record.get("bio"),
            profile_url=record.get("profile_url"),
            followers_count=record.get("followers_count"),
            following_count=record.get("following_count"),
            posts_count=record.get("posts_count"),
            is_verified=record.get("is_verified", False),
            overall_trust_score=float(record["overall_trust_score"]),
            trust_label=record["trust_label"],
            message_history_score=float(record["message_history_score"]) if record.get("message_history_score") else None,
            followers_score=float(record["followers_score"]) if record.get("followers_score") else None,
            web_reputation_score=float(record["web_reputation_score"]) if record.get("web_reputation_score") else None,
            disclosure_score=float(record["disclosure_score"]) if record.get("disclosure_score") else None,
            analysis_summary=record.get("analysis_summary"),
            issues=record.get("issues", []),
            last_analyzed_at=record["last_analyzed_at"],
            added_to_marketplace_at=record["added_to_marketplace_at"],
            is_featured=record.get("is_featured", False),
            admin_notes=record.get("admin_notes"),
        )
        for record in result["data"]
    ]

    return MarketplaceListResponse(
        influencers=influencers,
        total=result["total"],
        limit=limit,
        offset=offset,
    )


@router.get("/marketplace/influencers/{handle}", response_model=MarketplaceInfluencer)
def get_marketplace_influencer_detail(handle: str, platform: str = "instagram"):
    """
    Get detailed information for a single marketplace influencer.
    """
    if not is_cache_available():
        raise HTTPException(
            status_code=503,
            detail="Marketplace is not available. Supabase must be configured to use marketplace features.",
        )

    record = get_marketplace_influencer(handle, platform)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Influencer @{handle} not found in marketplace.",
        )

    return MarketplaceInfluencer(
        id=str(record["id"]),
        handle=record["handle"],
        platform=record["platform"],
        display_name=record.get("display_name"),
        bio=record.get("bio"),
        profile_url=record.get("profile_url"),
        followers_count=record.get("followers_count"),
        following_count=record.get("following_count"),
        posts_count=record.get("posts_count"),
        is_verified=record.get("is_verified", False),
        overall_trust_score=float(record["overall_trust_score"]),
        trust_label=record["trust_label"],
        message_history_score=float(record["message_history_score"]) if record.get("message_history_score") else None,
        followers_score=float(record["followers_score"]) if record.get("followers_score") else None,
        web_reputation_score=float(record["web_reputation_score"]) if record.get("web_reputation_score") else None,
        disclosure_score=float(record["disclosure_score"]) if record.get("disclosure_score") else None,
        analysis_summary=record.get("analysis_summary"),
        issues=record.get("issues", []),
        last_analyzed_at=record["last_analyzed_at"],
        added_to_marketplace_at=record["added_to_marketplace_at"],
        is_featured=record.get("is_featured", False),
        admin_notes=record.get("admin_notes"),
    )


@router.post("/marketplace/influencers", response_model=MarketplaceInfluencer)
async def add_to_marketplace(
    req: AddToMarketplaceRequest,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Analyze an influencer and add them to the marketplace.

    SECURITY: Admin authentication required via Authorization header.
    Usage: Authorization: Bearer YOUR_API_KEY
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_cache_available():
        raise HTTPException(
            status_code=503,
            detail="Marketplace is not available. Supabase must be configured to use marketplace features.",
        )

    handle = req.handle.strip()
    if not handle:
        raise HTTPException(status_code=400, detail="Handle cannot be empty.")

    # First, perform full influencer analysis
    try:
        influencer_trust = await build_influencer_trust_response(handle, max_posts=5)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to analyze influencer: {exc}",
        ) from exc

    # Extract profile and trust data
    profile_data = {
        "full_name": influencer_trust.stats.full_name,
        "bio": influencer_trust.stats.bio,
        "url": influencer_trust.stats.url,
        "followers": influencer_trust.stats.followers,
        "following": influencer_trust.stats.following,
        "posts_count": influencer_trust.stats.posts_count,
        "is_verified": influencer_trust.stats.is_verified,
    }

    trust_data = {
        "trust_score": influencer_trust.trust_score,
        "label": influencer_trust.label,
        "message_history_score": influencer_trust.message_history_score,
        "followers_score": influencer_trust.followers_score,
        "web_reputation_score": influencer_trust.web_reputation_score,
        "disclosure_score": influencer_trust.disclosure_score,
        "notes": influencer_trust.notes,
        "issues": [],  # You can extract issues from notes if needed
    }

    # Add to marketplace
    record = add_influencer_to_marketplace(
        handle=handle,
        platform=req.platform,
        profile_data=profile_data,
        trust_data=trust_data,
        admin_notes=req.admin_notes,
        is_featured=req.is_featured,
    )

    if not record:
        raise HTTPException(
            status_code=500,
            detail="Failed to add influencer to marketplace.",
        )

    return MarketplaceInfluencer(
        id=str(record["id"]),
        handle=record["handle"],
        platform=record["platform"],
        display_name=record.get("display_name"),
        bio=record.get("bio"),
        profile_url=record.get("profile_url"),
        followers_count=record.get("followers_count"),
        following_count=record.get("following_count"),
        posts_count=record.get("posts_count"),
        is_verified=record.get("is_verified", False),
        overall_trust_score=float(record["overall_trust_score"]),
        trust_label=record["trust_label"],
        message_history_score=float(record["message_history_score"]) if record.get("message_history_score") else None,
        followers_score=float(record["followers_score"]) if record.get("followers_score") else None,
        web_reputation_score=float(record["web_reputation_score"]) if record.get("web_reputation_score") else None,
        disclosure_score=float(record["disclosure_score"]) if record.get("disclosure_score") else None,
        analysis_summary=record.get("analysis_summary"),
        issues=record.get("issues", []),
        last_analyzed_at=record["last_analyzed_at"],
        added_to_marketplace_at=record["added_to_marketplace_at"],
        is_featured=record.get("is_featured", False),
        admin_notes=record.get("admin_notes"),
    )


@router.delete("/marketplace/influencers/{handle}")
def remove_influencer_from_marketplace(
    handle: str,
    request: Request,
    platform: str = "instagram",
    authorization: Optional[str] = Header(None)
):
    """
    Remove an influencer from the marketplace.

    SECURITY: Admin authentication required via Authorization header.
    Usage: Authorization: Bearer YOUR_API_KEY
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_cache_available():
        raise HTTPException(
            status_code=503,
            detail="Marketplace is not available. Supabase must be configured to use marketplace features.",
        )

    success = remove_from_marketplace(handle, platform)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to remove influencer from marketplace.",
        )

    return {"message": f"Influencer @{handle} removed from marketplace successfully."}


# User feedback endpoint
@router.post("/feedback", response_model=UserFeedbackResponse)
async def submit_feedback(req: UserFeedbackRequest, request: Request):
    """
    Submit user feedback after analysis.
    Includes rate limiting and security measures to prevent spam and abuse.
    """
    # SECURITY: Use actual client IP, do not trust X-Forwarded-For
    # X-Forwarded-For can be spoofed by the client
    # In production behind a trusted proxy, configure the proxy to set a signed header
    ip_address = request.client.host if request.client else "unknown"

    # SECURITY: Do not trust client-supplied session IDs for rate limiting
    # Generate server-side session ID based on IP + User-Agent
    user_agent = request.headers.get("User-Agent", "unknown")
    session_id = f"{ip_address}:{user_agent}"

    # SECURITY: Check rate limits (fail closed - blocks on error)
    try:
        if not check_feedback_rate_limit(ip_address, session_id):
            raise HTTPException(
                status_code=429,
                detail="Too many feedback submissions. Please try again later.",
            )
    except HTTPException:
        # Re-raise HTTP exceptions (429)
        raise
    except Exception as e:
        # SECURITY: Fail closed - if rate limiting fails, block the request
        print(f"[Feedback] Rate limiting system error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Feedback system temporarily unavailable. Please try again later.",
        )

    # Submit feedback to database
    result = submit_user_feedback(
        analysis_type=req.analysis_type,
        experience_rating=req.experience_rating,
        ip_address=ip_address,
        session_id=session_id,
        analyzed_entity=req.analyzed_entity,
        review_text=req.review_text,
        email=req.email,
        email_consented=req.email_consented,
        user_agent=user_agent,
    )

    if not result:
        # If Supabase is not configured, still return success
        # This ensures the feature doesn't break the app
        return UserFeedbackResponse(
            id="temp",
            message="Thank you for your feedback!",
            email_subscribed=False,
        )

    return UserFeedbackResponse(
        id=str(result.get("id", "")),
        message="Thank you for your feedback!",
        email_subscribed=bool(req.email and req.email_consented),
    )


# Admin endpoint to export newsletter subscribers
@router.get("/admin/newsletter/subscribers")
def get_subscribers(request: Request, authorization: Optional[str] = Header(None)):
    """
    Get newsletter subscribers list (Admin only).
    Requires API key authentication via Authorization header.

    SECURITY: API key must be sent in Authorization header, not query string.
    Usage: Authorization: Bearer YOUR_API_KEY

    Set ADMIN_API_KEY in your .env file for authentication.
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints too
    check_rate_limit(request, endpoint_group="admin")

    if not is_cache_available():
        raise HTTPException(
            status_code=503,
            detail="Newsletter feature not available. Supabase must be configured.",
        )

    subscribers = get_newsletter_subscribers()

    return {
        "total": len(subscribers),
        "subscribers": subscribers,
    }

