"""FastAPI routes for the Perseval backend."""

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Request

from backend.app.core.rate_limiter import check_rate_limit
from backend.app.core.security import verify_admin_auth
from backend.app.integrations.supabase import is_supabase_available
from backend.app.models.schemas import (
    AddToMarketplaceRequest,
    CompanyTrustRequest,
    CompanyTrustResponse,
    FullAnalysisRequest,
    FullAnalysisResponse,
    FullAnalysisSource,
    InfluencerStatsRequest,
    InfluencerStatsResponse,
    InfluencerSubmission,
    InfluencerSubmissionRequest,
    InfluencerSubmissionResponse,
    InfluencerTrustResponse,
    InstagramPostAnalyzeRequest,
    MarketplaceInfluencer,
    MarketplaceListRequest,
    MarketplaceListResponse,
    ProductTrustRequest,
    ProductTrustResponse,
    ReviewSubmissionRequest,
    ReviewSubmissionResponse,
    ScamPrediction,
    SubmissionListResponse,
    TextAnalyzeRequest,
    UserFeedbackRequest,
    UserFeedbackResponse,
    UserVoteStatus,
    VoteRequest,
    VoteResponse,
    VoteStats,
)
from backend.app.repositories.feedback import (
    check_feedback_rate_limit,
    get_newsletter_subscribers,
    submit_user_feedback,
)
from backend.app.repositories.marketplace import (
    add_influencer_to_marketplace,
    get_marketplace_influencer,
    list_marketplace_influencers,
    remove_from_marketplace,
)
from backend.app.repositories.submissions import (
    check_duplicate_submission,
    check_submission_rate_limit,
    create_influencer_submission,
    get_submission_by_id,
    get_user_submissions,
    list_submissions,
    review_submission,
    update_submission_status,
)
from backend.app.repositories.submissions import hash_ip_address as hash_ip_submissions
from backend.app.repositories.votes import (
    check_vote_rate_limit,
    delete_vote,
    get_user_vote,
    get_vote_stats,
    hash_ip_address,
    submit_vote,
    update_marketplace_user_score,
)
from backend.app.services.influencer_probe import (
    get_instagram_post_from_url,
    get_instagram_stats,
)
from backend.app.services.mistral import (
    detect_company_and_product_from_text,
    mistral_scam_check,
)
from backend.app.services.tiktok import get_tiktok_video_info
from backend.app.services.trust import (
    build_company_trust_response,
    build_influencer_trust_response,
    build_product_trust_response,
)
router = APIRouter()


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
            if influencer_trust and is_supabase_available():
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
    if not is_supabase_available():
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
            user_trust_score=float(record.get("user_trust_score", 0.50)),
            total_votes=record.get("total_votes", 0),
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
    if not is_supabase_available():
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
        user_trust_score=float(record.get("user_trust_score", 0.50)),
        total_votes=record.get("total_votes", 0),
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

    if not is_supabase_available():
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

    if not is_supabase_available():
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

    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Newsletter feature not available. Supabase must be configured.",
        )

    subscribers = get_newsletter_subscribers()

    return {
        "total": len(subscribers),
        "subscribers": subscribers,
    }


# Influencer submission endpoints
@router.post("/submissions/influencers", response_model=InfluencerSubmissionResponse)
def submit_influencer(req: InfluencerSubmissionRequest, request: Request):
    """
    Submit an influencer for marketplace consideration.

    User-facing endpoint that allows anyone to suggest influencers for the marketplace.
    Submissions are rate limited and go through admin review before being added.

    Rate limits:
    - 3 submissions per IP per 24 hours
    - Duplicates rejected (same handle/platform within 7 days)
    """
    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    # Get client IP and hash it for privacy
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_submissions(client_ip)

    # Check rate limit (3 submissions per 24 hours per IP)
    if not check_submission_rate_limit(ip_hash):
        raise HTTPException(
            status_code=429,
            detail="You have reached the maximum number of submissions (3 per day). Please try again tomorrow.",
        )

    # Check for duplicate submissions
    if not check_duplicate_submission(req.handle, req.platform):
        raise HTTPException(
            status_code=409,
            detail=f"This influencer (@{req.handle}) has already been submitted recently. Please check back later.",
        )

    # Create submission
    submission = create_influencer_submission(
        handle=req.handle,
        platform=req.platform,
        submitter_ip_hash=ip_hash,
        reason=req.reason,
    )

    if not submission:
        raise HTTPException(
            status_code=500,
            detail="Failed to create submission. Please try again later.",
        )

    return InfluencerSubmissionResponse(
        id=str(submission["id"]),
        handle=submission["handle"],
        platform=submission["platform"],
        status=submission["status"],
        message="Thank you for your submission! We'll review it and add the influencer to the marketplace if approved.",
        created_at=submission["created_at"],
    )


@router.get("/submissions/influencers/my", response_model=SubmissionListResponse)
def get_my_submissions(request: Request, limit: int = 10):
    """
    Get submissions from the current user (by IP).

    Allows users to check the status of their submissions.
    Limited to 10 most recent submissions.
    """
    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    # Get client IP and hash it
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_submissions(client_ip)

    # Get user's submissions
    submissions_data = get_user_submissions(ip_hash, limit=min(limit, 10))

    submissions = [
        InfluencerSubmission(
            id=str(sub["id"]),
            handle=sub["handle"],
            platform=sub["platform"],
            reason=sub.get("reason"),
            status=sub["status"],
            analysis_data=sub.get("analysis_data"),
            trust_score=float(sub["trust_score"]) if sub.get("trust_score") else None,
            analysis_completed_at=sub.get("analysis_completed_at"),
            analysis_error=sub.get("analysis_error"),
            reviewed_by=sub.get("reviewed_by"),
            reviewed_at=sub.get("reviewed_at"),
            admin_notes=sub.get("admin_notes"),
            rejection_reason=sub.get("rejection_reason"),
            created_at=sub["created_at"],
            updated_at=sub["updated_at"],
        )
        for sub in submissions_data
    ]

    return SubmissionListResponse(
        submissions=submissions,
        total=len(submissions),
        limit=limit,
        offset=0,
    )


# Admin endpoints for managing submissions
@router.get("/admin/submissions/influencers", response_model=SubmissionListResponse)
def list_influencer_submissions(
    request: Request,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    List all influencer submissions (Admin only).

    SECURITY: Admin authentication required via Authorization header.
    Usage: Authorization: Bearer YOUR_API_KEY
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    # Get submissions
    result = list_submissions(status=status, limit=limit, offset=offset)

    submissions = [
        InfluencerSubmission(
            id=str(sub["id"]),
            handle=sub["handle"],
            platform=sub["platform"],
            reason=sub.get("reason"),
            status=sub["status"],
            analysis_data=sub.get("analysis_data"),
            trust_score=float(sub["trust_score"]) if sub.get("trust_score") else None,
            analysis_completed_at=sub.get("analysis_completed_at"),
            analysis_error=sub.get("analysis_error"),
            reviewed_by=sub.get("reviewed_by"),
            reviewed_at=sub.get("reviewed_at"),
            admin_notes=sub.get("admin_notes"),
            rejection_reason=sub.get("rejection_reason"),
            created_at=sub["created_at"],
            updated_at=sub["updated_at"],
        )
        for sub in result["data"]
    ]

    return SubmissionListResponse(
        submissions=submissions,
        total=result["total"],
        limit=limit,
        offset=offset,
    )


@router.get("/admin/submissions/influencers/{submission_id}", response_model=InfluencerSubmission)
def get_submission_detail(
    submission_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Get detailed information for a specific submission (Admin only).

    SECURITY: Admin authentication required via Authorization header.
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    submission = get_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} not found.",
        )

    return InfluencerSubmission(
        id=str(submission["id"]),
        handle=submission["handle"],
        platform=submission["platform"],
        reason=submission.get("reason"),
        status=submission["status"],
        analysis_data=submission.get("analysis_data"),
        trust_score=float(submission["trust_score"]) if submission.get("trust_score") else None,
        analysis_completed_at=submission.get("analysis_completed_at"),
        analysis_error=submission.get("analysis_error"),
        reviewed_by=submission.get("reviewed_by"),
        reviewed_at=submission.get("reviewed_at"),
        admin_notes=submission.get("admin_notes"),
        rejection_reason=submission.get("rejection_reason"),
        created_at=submission["created_at"],
        updated_at=submission["updated_at"],
    )


@router.post("/admin/submissions/influencers/{submission_id}/analyze")
async def analyze_submission(
    submission_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Trigger automated analysis for a submission (Admin only).

    Analyzes the influencer using Perplexity + Mistral and stores results.

    SECURITY: Admin authentication required via Authorization header.
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    # Get submission
    submission = get_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} not found.",
        )

    if submission["status"] not in ["pending", "analyzing"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot analyze submission with status '{submission['status']}'. Only pending submissions can be analyzed.",
        )

    # Update status to analyzing
    update_submission_status(submission_id, "analyzing")

    # Perform analysis
    try:
        influencer_trust = await build_influencer_trust_response(
            submission["handle"],
            max_posts=5
        )

        # Store analysis results
        analysis_data = {
            "stats": {
                "full_name": influencer_trust.stats.full_name,
                "bio": influencer_trust.stats.bio,
                "followers": influencer_trust.stats.followers,
                "following": influencer_trust.stats.following,
                "posts_count": influencer_trust.stats.posts_count,
                "is_verified": influencer_trust.stats.is_verified,
            },
            "trust": {
                "trust_score": influencer_trust.trust_score,
                "label": influencer_trust.label,
                "message_history_score": influencer_trust.message_history_score,
                "followers_score": influencer_trust.followers_score,
                "web_reputation_score": influencer_trust.web_reputation_score,
                "disclosure_score": influencer_trust.disclosure_score,
                "notes": influencer_trust.notes,
            }
        }

        # Update submission with analysis results
        updated = update_submission_status(
            submission_id,
            "pending",  # Back to pending for admin review
            analysis_data=analysis_data,
            trust_score=influencer_trust.trust_score,
        )

        if not updated:
            raise HTTPException(
                status_code=500,
                detail="Failed to store analysis results.",
            )

        return {
            "message": "Analysis completed successfully.",
            "submission_id": submission_id,
            "trust_score": influencer_trust.trust_score,
            "trust_label": influencer_trust.label,
        }

    except HTTPException:
        # Update submission with error
        update_submission_status(
            submission_id,
            "pending",
            analysis_error="Analysis failed - HTTP error",
        )
        raise
    except Exception as e:
        # Update submission with error
        update_submission_status(
            submission_id,
            "pending",
            analysis_error=str(e)[:500],  # Limit error message length
        )
        raise HTTPException(
            status_code=502,
            detail=f"Failed to analyze influencer: {str(e)}",
        ) from e


@router.post("/admin/submissions/influencers/{submission_id}/review", response_model=ReviewSubmissionResponse)
async def review_influencer_submission(
    submission_id: str,
    req: ReviewSubmissionRequest,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Review a submission - approve or reject (Admin only).

    If approved and add_to_marketplace=True, automatically adds to marketplace.

    SECURITY: Admin authentication required via Authorization header.
    Usage: Authorization: Bearer YOUR_API_KEY
    """
    # SECURITY: Verify admin authentication
    verify_admin_auth(authorization)

    # SECURITY: Rate limit admin endpoints
    check_rate_limit(request, endpoint_group="admin")

    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Submissions are not available. Supabase must be configured.",
        )

    # Get submission
    submission = get_submission_by_id(submission_id)
    if not submission:
        raise HTTPException(
            status_code=404,
            detail=f"Submission {submission_id} not found.",
        )

    if submission["status"] in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail=f"Submission has already been {submission['status']}.",
        )

    # Review submission
    reviewed = review_submission(
        submission_id=submission_id,
        status=req.status,
        reviewed_by="admin",  # Could be extracted from auth token
        admin_notes=req.admin_notes,
        rejection_reason=req.rejection_reason,
    )

    if not reviewed:
        raise HTTPException(
            status_code=500,
            detail="Failed to review submission.",
        )

    marketplace_influencer_id = None

    # If approved and should add to marketplace
    if req.status == "approved" and req.add_to_marketplace:
        # Check if analysis exists
        if not submission.get("analysis_data"):
            raise HTTPException(
                status_code=400,
                detail="Cannot add to marketplace: submission has not been analyzed yet. Please run analysis first.",
            )

        try:
            analysis = submission["analysis_data"]
            stats = analysis.get("stats", {})
            trust = analysis.get("trust", {})

            profile_data = {
                "full_name": stats.get("full_name"),
                "bio": stats.get("bio"),
                "url": f"https://instagram.com/{submission['handle']}",
                "followers": stats.get("followers"),
                "following": stats.get("following"),
                "posts_count": stats.get("posts_count"),
                "is_verified": stats.get("is_verified", False),
            }

            trust_data = {
                "trust_score": trust.get("trust_score"),
                "label": trust.get("label"),
                "message_history_score": trust.get("message_history_score"),
                "followers_score": trust.get("followers_score"),
                "web_reputation_score": trust.get("web_reputation_score"),
                "disclosure_score": trust.get("disclosure_score"),
                "notes": trust.get("notes"),
                "issues": [],
            }

            # Add to marketplace
            marketplace_record = add_influencer_to_marketplace(
                handle=submission["handle"],
                platform=submission["platform"],
                profile_data=profile_data,
                trust_data=trust_data,
                admin_notes=req.admin_notes,
                is_featured=False,
            )

            if marketplace_record:
                marketplace_influencer_id = str(marketplace_record["id"])

        except Exception as e:
            print(f"[Submissions] Failed to add to marketplace: {e}")
            # Don't fail the review if marketplace addition fails
            pass

    # Convert reviewed submission to response model
    submission_response = InfluencerSubmission(
        id=str(reviewed["id"]),
        handle=reviewed["handle"],
        platform=reviewed["platform"],
        reason=reviewed.get("reason"),
        status=reviewed["status"],
        analysis_data=reviewed.get("analysis_data"),
        trust_score=float(reviewed["trust_score"]) if reviewed.get("trust_score") else None,
        analysis_completed_at=reviewed.get("analysis_completed_at"),
        analysis_error=reviewed.get("analysis_error"),
        reviewed_by=reviewed.get("reviewed_by"),
        reviewed_at=reviewed.get("reviewed_at"),
        admin_notes=reviewed.get("admin_notes"),
        rejection_reason=reviewed.get("rejection_reason"),
        created_at=reviewed["created_at"],
        updated_at=reviewed["updated_at"],
    )

    message = f"Submission {req.status}."
    if marketplace_influencer_id:
        message += f" Influencer added to marketplace."

    return ReviewSubmissionResponse(
        submission=submission_response,
        message=message,
        marketplace_influencer_id=marketplace_influencer_id,
    )


# Voting endpoints (crowdsourcing)
@router.post("/votes/influencers", response_model=VoteResponse)
def vote_on_influencer(req: VoteRequest, request: Request):
    """
    Vote on an influencer (trust or distrust).

    Users can vote once per influencer. Subsequent votes update their existing vote.
    Rate limited to 20 votes per hour to prevent spam.

    Vote types:
    - 'trust': Thumbs up - you trust this influencer
    - 'distrust': Thumbs down - you don't trust this influencer
    """
    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Voting system is not available. Supabase must be configured.",
        )

    # Get client IP and hash it for privacy
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_address(client_ip)

    # Check rate limit (20 votes per hour)
    if not check_vote_rate_limit(ip_hash):
        raise HTTPException(
            status_code=429,
            detail="You have exceeded the voting rate limit (20 votes per hour). Please try again later.",
        )

    # Submit vote (will upsert if user already voted)
    vote = submit_vote(
        handle=req.handle,
        platform=req.platform,
        vote_type=req.vote_type,
        voter_ip_hash=ip_hash,
        comment=req.comment,
    )

    if not vote:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit vote. Please try again later.",
        )

    # Get updated vote statistics
    stats = get_vote_stats(req.handle, req.platform)

    # Update marketplace influencer's user score (if exists)
    update_marketplace_user_score(req.handle, req.platform)

    return VoteResponse(
        handle=req.handle,
        platform=req.platform,
        vote_type=req.vote_type,
        message="Thank you for your vote! Your feedback helps others make informed decisions.",
        vote_stats=VoteStats(**stats),
    )


@router.get("/votes/influencers/{handle}", response_model=UserVoteStatus)
def get_influencer_vote_status(
    handle: str,
    request: Request,
    platform: str = "instagram"
):
    """
    Get voting statistics and current user's vote for an influencer.

    Returns:
    - Vote statistics (trust/distrust counts, total votes, user trust score)
    - Current user's vote (if any)
    """
    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Voting system is not available. Supabase must be configured.",
        )

    # Get client IP and hash it
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_address(client_ip)

    # Get user's current vote
    user_vote = get_user_vote(handle, platform, ip_hash)

    # Get vote statistics
    stats = get_vote_stats(handle, platform)

    return UserVoteStatus(
        handle=handle,
        platform=platform,
        user_vote=user_vote,
        vote_stats=VoteStats(**stats),
    )


@router.delete("/votes/influencers/{handle}")
def remove_vote(
    handle: str,
    request: Request,
    platform: str = "instagram"
):
    """
    Remove your vote for an influencer.

    This allows users to retract their vote if they change their mind.
    """
    if not is_supabase_available():
        raise HTTPException(
            status_code=503,
            detail="Voting system is not available. Supabase must be configured.",
        )

    # Get client IP and hash it
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_address(client_ip)

    # Delete vote
    success = delete_vote(handle, platform, ip_hash)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="No vote found to remove.",
        )

    # Update marketplace influencer's user score
    update_marketplace_user_score(handle, platform)

    return {
        "message": "Vote removed successfully.",
        "handle": handle,
        "platform": platform,
    }
