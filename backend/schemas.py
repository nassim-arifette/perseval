"""Pydantic request/response schemas shared across the API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="Raw text to evaluate for scam risk")


class ScamPrediction(BaseModel):
    label: Literal["scam", "not_scam", "uncertain"]
    score: float  # 0-1 confidence
    reason: str  # short explanation
    raw_post_text: str


class InfluencerStatsRequest(BaseModel):
    platform: Literal["instagram"] = Field(
        "instagram",
        description="Target platform (Instagram only while Twitter/X support is paused).",
    )
    handle: str = Field(..., description="Target username / handle (with or without @).")
    max_posts: int = Field(5, ge=1, le=20, description="How many recent posts to inspect.")


class InfluencerStatsResponse(BaseModel):
    platform: Literal["instagram"]
    handle: str
    full_name: Optional[str] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    posts_count: Optional[int] = None
    is_verified: Optional[bool] = None
    bio: Optional[str] = None
    url: Optional[str] = None
    sample_posts: Optional[List[str]] = None


class InstagramPostAnalyzeRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="Instagram post / reel URL whose caption should be analyzed.",
    )


class InfluencerTrustResponse(BaseModel):
    stats: InfluencerStatsResponse
    trust_score: float = Field(..., ge=0.0, le=1.0)
    label: Literal["high", "medium", "low"]
    message_history_score: float = Field(..., ge=0.0, le=1.0)
    followers_score: float = Field(..., ge=0.0, le=1.0)
    web_reputation_score: float = Field(..., ge=0.0, le=1.0)
    disclosure_score: float = Field(..., ge=0.0, le=1.0)
    notes: str


class CompanyTrustRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Company / brand name to investigate.")
    max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper search snippets to consider.",
    )


class CompanyTrustResponse(BaseModel):
    name: str
    trust_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    issues: List[str] = Field(default_factory=list)


class ProductTrustRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Product name to investigate.")
    max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many Serper search snippets to consider.",
    )


class ProductTrustResponse(BaseModel):
    name: str
    trust_score: float = Field(..., ge=0.0, le=1.0)
    summary: str
    issues: List[str] = Field(default_factory=list)


class FullAnalysisSource(BaseModel):
    text_origin: Literal["input", "instagram", "tiktok"]
    instagram_url: Optional[str] = None
    instagram_owner: Optional[str] = None
    tiktok_url: Optional[str] = None
    tiktok_author: Optional[str] = None
    inferred_company_name: Optional[str] = None
    inferred_product_name: Optional[str] = None


class FullAnalysisRequest(BaseModel):
    text: Optional[str] = Field(
        None,
        description="Raw text to analyze if you aren't providing a social post URL.",
    )
    instagram_url: Optional[HttpUrl] = Field(
        None, description="Instagram post URL to fetch caption from."
    )
    tiktok_url: Optional[HttpUrl] = Field(
        None,
        description="TikTok video URL to fetch caption from.",
    )
    influencer_handle: Optional[str] = Field(
        None,
        description="Influencer handle to enrich trust analysis. Auto-detected from Instagram URLs if omitted.",
    )
    company_name: Optional[str] = Field(
        None,
        description="Company or brand name explicitly provided by the user.",
    )
    product_name: Optional[str] = Field(
        None,
        description="Product / service name explicitly provided by the user.",
    )
    max_posts: int = Field(
        5,
        ge=1,
        le=20,
        description="How many of the influencer's recent posts to scan for message history.",
    )
    company_max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many web snippets to inspect for company reputation.",
    )
    product_max_results: int = Field(
        8,
        ge=1,
        le=20,
        description="How many web snippets to inspect for product reputation.",
    )


class FullAnalysisResponse(BaseModel):
    message_prediction: ScamPrediction
    influencer_trust: Optional[InfluencerTrustResponse]
    company_trust: Optional[CompanyTrustResponse]
    product_trust: Optional[ProductTrustResponse]
    source_details: FullAnalysisSource
    final_summary: str

