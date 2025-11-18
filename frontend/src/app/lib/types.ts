export type ScamLabel = "scam" | "not_scam" | "uncertain";

export type ScamPrediction = {
  label: ScamLabel;
  score: number;
  reason: string;
  raw_post_text: string;
};

export type RiskTier = "high" | "caution" | "low";
export type ThemeKey = "dark" | "light";
export type Severity = "high" | "medium" | "info";
export type HighlightTone = "high" | "medium" | null;

export type ReasonBullet = { text: string; severity: Severity };
export type HighlightSegment = { key: string; content: string; tone: HighlightTone };

export type InfluencerStats = {
  platform: "instagram";
  handle: string;
  full_name?: string | null;
  followers?: number | null;
  following?: number | null;
  posts_count?: number | null;
  is_verified?: boolean | null;
  bio?: string | null;
  url?: string | null;
  sample_posts?: string[] | null;
};

export type InfluencerTrustResponse = {
  stats: InfluencerStats;
  trust_score: number;
  label: "high" | "medium" | "low";
  message_history_score: number;
  followers_score: number;
  web_reputation_score: number;
  disclosure_score: number;
  notes: string;
};

export type CompanyTrustResponse = {
  name: string;
  trust_score: number;
  summary: string;
  issues: string[];
};

export type ProductTrustResponse = {
  name: string;
  trust_score: number;
  summary: string;
  issues: string[];
};

export type FullAnalysisSourceDetails = {
  text_origin: "input" | "instagram" | "tiktok";
  instagram_url?: string | null;
  instagram_owner?: string | null;
  tiktok_url?: string | null;
  tiktok_author?: string | null;
  inferred_company_name?: string | null;
  inferred_product_name?: string | null;
};

export type FullAnalysisResponse = {
  message_prediction: ScamPrediction;
  influencer_trust?: InfluencerTrustResponse | null;
  company_trust?: CompanyTrustResponse | null;
  product_trust?: ProductTrustResponse | null;
  source_details: FullAnalysisSourceDetails;
  final_summary: string;
};

// Marketplace types
export type MarketplacePlatform =
  | "instagram"
  | "tiktok"
  | "youtube"
  | "twitch"
  | "x"
  | "facebook"
  | "podcast";

export type MarketplaceInfluencer = {
  id: string;
  handle: string;
  platform: MarketplacePlatform;
  display_name?: string | null;
  bio?: string | null;
  profile_url?: string | null;
  followers_count?: number | null;
  following_count?: number | null;
  posts_count?: number | null;
  is_verified: boolean;
  overall_trust_score: number;
  trust_label: "high" | "medium" | "low";
  message_history_score?: number | null;
  followers_score?: number | null;
  web_reputation_score?: number | null;
  disclosure_score?: number | null;
  analysis_summary?: string | null;
  issues: string[];
  last_analyzed_at: string;
  added_to_marketplace_at: string;
  is_featured: boolean;
  admin_notes?: string | null;
};

export type MarketplaceListResponse = {
  influencers: MarketplaceInfluencer[];
  total: number;
  limit: number;
  offset: number;
};
