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
