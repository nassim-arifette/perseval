"""Pydantic request/response schemas shared across the API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


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


# Marketplace schemas
MarketplacePlatform = Literal[
    "instagram",
    "tiktok",
    "youtube",
    "twitch",
    "x",
    "facebook",
    "podcast",
]


class MarketplaceInfluencer(BaseModel):
    """Marketplace influencer with full profile and trust data."""
    id: str
    handle: str
    platform: MarketplacePlatform

    # Profile data
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_url: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None
    is_verified: bool = False

    # Trust scores
    overall_trust_score: float = Field(..., ge=0.0, le=1.0)
    trust_label: Literal["high", "medium", "low"]

    # Component scores
    message_history_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    followers_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    web_reputation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    disclosure_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Additional metadata
    analysis_summary: Optional[str] = None
    issues: List[str] = Field(default_factory=list)
    last_analyzed_at: str

    # Marketplace metadata
    added_to_marketplace_at: str
    is_featured: bool = False
    admin_notes: Optional[str] = None


class AddToMarketplaceRequest(BaseModel):
    """Request to add an influencer to the marketplace."""
    handle: str = Field(..., description="Instagram handle to analyze and add to marketplace")
    platform: Literal["instagram"] = "instagram"
    admin_notes: Optional[str] = Field(None, description="Optional notes for admin reference")
    is_featured: bool = Field(False, description="Mark as featured influencer")


class MarketplaceListRequest(BaseModel):
    """Request to list marketplace influencers with filters."""
    search: Optional[str] = Field(None, description="Search by handle or display name")
    trust_level: Optional[Literal["high", "medium", "low"]] = Field(None, description="Filter by trust level")
    sort_by: Literal["trust_score", "followers", "last_analyzed"] = Field("trust_score", description="Sort field")
    sort_order: Literal["asc", "desc"] = Field("desc", description="Sort order")
    limit: int = Field(20, ge=1, le=100, description="Number of results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class MarketplaceListResponse(BaseModel):
    """Response with paginated marketplace influencers."""
    influencers: List[MarketplaceInfluencer]
    total: int
    limit: int
    offset: int


# User feedback schemas
class UserFeedbackRequest(BaseModel):
    """Request to submit user feedback after analysis."""
    analysis_type: Literal["full", "influencer", "company", "product", "text"] = Field(
        ...,
        description="Type of analysis that was performed"
    )
    analyzed_entity: Optional[str] = Field(
        None,
        max_length=200,
        description="Handle, company name, or product name that was analyzed"
    )
    experience_rating: Literal["good", "medium", "bad"] = Field(
        ...,
        description="User's experience rating: good, medium, or bad"
    )
    review_text: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional user review or additional feedback"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Optional email for newsletter signup"
    )
    email_consented: bool = Field(
        False,
        description="User explicitly consents to receive emails"
    )

    @field_validator('review_text')
    @classmethod
    def sanitize_review_text(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize review text to prevent XSS and other injection attacks."""
        if v is None:
            return v
        # Strip whitespace
        v = v.strip()
        if not v:
            return None
        # Remove any potential HTML/script tags (basic sanitization)
        # Note: More robust sanitization can be done with bleach library
        dangerous_patterns = ['<script', '</script', 'javascript:', 'onerror=', 'onclick=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("Review text contains potentially dangerous content")
        return v

    @field_validator('analyzed_entity')
    @classmethod
    def sanitize_entity(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize analyzed entity field."""
        if v is None:
            return v
        # Strip whitespace and limit length
        return v.strip()[:200]


class UserFeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    id: str
    message: str = "Thank you for your feedback!"
    email_subscribed: bool = False


# Influencer submission schemas
class InfluencerSubmissionRequest(BaseModel):
    """Request to submit an influencer for marketplace review."""
    handle: str = Field(..., min_length=1, max_length=100, description="Influencer handle (with or without @ prefix)")
    platform: MarketplacePlatform = Field("instagram", description="Social media platform")
    reason: Optional[str] = Field(None, max_length=500, description="Why you think this influencer should be added")

    @field_validator('handle')
    @classmethod
    def normalize_handle(cls, v: str) -> str:
        """Normalize handle by removing @ prefix and extra whitespace."""
        return v.strip().lstrip("@")

    @field_validator('reason')
    @classmethod
    def sanitize_reason(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize reason field to prevent XSS."""
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        # Basic XSS prevention
        dangerous_patterns = ['<script', '</script', 'javascript:', 'onerror=', 'onclick=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError("Reason contains potentially dangerous content")
        return v


class InfluencerSubmissionResponse(BaseModel):
    """Response after submitting an influencer."""
    id: str
    handle: str
    platform: str
    status: Literal["pending", "analyzing", "approved", "rejected"]
    message: str
    created_at: str


class InfluencerSubmission(BaseModel):
    """Full influencer submission with analysis and admin review data."""
    id: str
    handle: str
    platform: str
    reason: Optional[str] = None

    # Submission status
    status: Literal["pending", "analyzing", "approved", "rejected"]

    # Analysis results
    analysis_data: Optional[dict] = None
    trust_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    analysis_completed_at: Optional[str] = None
    analysis_error: Optional[str] = None

    # Admin review
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Metadata
    created_at: str
    updated_at: str


class SubmissionListResponse(BaseModel):
    """Response with paginated submissions list."""
    submissions: List[InfluencerSubmission]
    total: int
    limit: int
    offset: int


class ReviewSubmissionRequest(BaseModel):
    """Request to review a submission (admin only)."""
    status: Literal["approved", "rejected"] = Field(..., description="Approval decision")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Admin's review notes")
    rejection_reason: Optional[str] = Field(None, max_length=500, description="Reason for rejection")
    add_to_marketplace: bool = Field(True, description="Automatically add to marketplace if approved")

    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure rejection reason is provided when status is rejected."""
        # Access the status from the values dict
        if 'status' in info.data and info.data['status'] == 'rejected' and not v:
            raise ValueError("Rejection reason is required when rejecting a submission")
        return v


class ReviewSubmissionResponse(BaseModel):
    """Response after reviewing a submission."""
    submission: InfluencerSubmission
    message: str
    marketplace_influencer_id: Optional[str] = None
