"""FastAPI routes for the Perseval backend."""

from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from backend.influencer_probe import (
    get_instagram_post_from_url,
    get_instagram_stats,
)
from backend.schemas import (
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
)
from backend.services.mistral import (
    detect_company_and_product_from_text,
    mistral_scam_check,
)
from backend.services.tiktok import get_tiktok_video_info
from backend.services.trust import (
    build_company_trust_response,
    build_influencer_trust_response,
    build_product_trust_response,
)

router = APIRouter()


@router.post("/analyze/text", response_model=ScamPrediction)
def analyze_text(req: TextAnalyzeRequest):
    """
    Accept pasted text directly and evaluate whether it looks like a scam or not.
    """
    cleaned_text = req.text.strip()
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="Text to analyze cannot be empty.")

    prediction = mistral_scam_check(cleaned_text)
    return prediction


@router.post("/influencer/stats", response_model=InfluencerStatsResponse)
async def influencer_stats(req: InfluencerStatsRequest):
    """
    Fetch influencer metadata + sample posts via Instaloader (Instagram only for now).
    """
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
async def influencer_trust(req: InfluencerStatsRequest):
    """
    Return influencer stats plus a composite trust score.
    """
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
def company_trust(req: CompanyTrustRequest):
    """
    Use Serper + Mistral to estimate overall company reputation.
    """
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")

    return build_company_trust_response(name, max_results=req.max_results)


@router.post("/product/trust", response_model=ProductTrustResponse)
def product_trust(req: ProductTrustRequest):
    """
    Use Serper + Mistral to estimate product-level reliability.
    """
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name cannot be empty.")

    return build_product_trust_response(name, max_results=req.max_results)


@router.get("/")
def root():
    return {"status": "ok", "message": "Scam checker API running"}


@router.post("/analyze/full", response_model=FullAnalysisResponse)
async def analyze_full(req: FullAnalysisRequest):
    """
    Unified endpoint: accept raw text and/or Instagram URL, optionally enrich with influencer + company trust.
    """
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

