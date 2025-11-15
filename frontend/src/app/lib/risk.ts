import type {
  HighlightSegment,
  ReasonBullet,
  RiskTier,
  ScamLabel,
  Severity,
} from "./types";

const highRiskWords = new Set([
  "wallet",
  "btc",
  "bitcoin",
  "crypto",
  "wire",
  "transfer",
  "routing",
  "password",
  "passcode",
  "otp",
  "token",
  "refund",
  "double",
  "guaranteed",
  "ssn",
  "account",
  "prize",
  "airdrop",
  "bank",
  "tax",
  "deposit",
]);

const mediumRiskWords = new Set([
  "urgent",
  "expires",
  "tonight",
  "today",
  "immediately",
  "click",
  "link",
  "verify",
  "confirm",
  "act",
  "selected",
  "winner",
  "limited",
  "discount",
  "code",
  "deal",
  "gift",
  "promo",
  "security",
  "alert",
  "suspend",
]);

const severityKeywords: Record<"high" | "medium", string[]> = {
  high: [
    "wallet",
    "bitcoin",
    "crypto",
    "wire",
    "transfer",
    "password",
    "otp",
    "payment",
    "bank",
  ],
  medium: ["urgent", "expires", "link", "verify", "confirm", "discount", "winner", "promo"],
};

export function deriveRiskTier(label?: ScamLabel | null): RiskTier {
  if (label === "scam") {
    return "high";
  }
  if (label === "uncertain") {
    return "caution";
  }
  return "low";
}

export function clampPercent(score?: number): number {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return 0;
  }
  return Math.round(Math.min(Math.max(score, 0), 1) * 100);
}

export function buildReasonBullets(reason: string, label: ScamLabel | null): ReasonBullet[] {
  if (!reason.trim()) {
    return [];
  }

  const segments = reason
    .replace(/\r/g, "")
    .split(/\n+/)
    .flatMap((line) =>
      line
        .split(/(?<=[.!?])\s+(?=[A-Z])/)
        .map((part) => part.replace(/^[\-\u2022]+\s*/, "").trim())
    )
    .filter(Boolean);

  return segments.slice(0, 3).map((text) => ({
    text,
    severity: detectSeverity(text, label),
  }));
}

export function highlightText(text: string): HighlightSegment[] {
  if (!text.trim()) {
    return [];
  }

  const tokens = text.split(/(\s+)/);
  return tokens.map((token, index) => {
    if (!token.trim()) {
      return { key: `space-${index}`, content: token, tone: null };
    }
    const normalized = token.toLowerCase().replace(/[^a-z0-9]/g, "");
    if (!normalized) {
      return { key: `punct-${index}`, content: token, tone: null };
    }
    if (highRiskWords.has(normalized)) {
      return { key: `high-${index}`, content: token, tone: "high" };
    }
    if (mediumRiskWords.has(normalized)) {
      return { key: `med-${index}`, content: token, tone: "medium" };
    }
    return { key: `text-${index}`, content: token, tone: null };
  });
}

function detectSeverity(text: string, label: ScamLabel | null): Severity {
  const normalized = text.toLowerCase();
  if (severityKeywords.high.some((keyword) => normalized.includes(keyword))) {
    return "high";
  }
  if (severityKeywords.medium.some((keyword) => normalized.includes(keyword))) {
    return "medium";
  }
  if (label === "scam") {
    return "high";
  }
  if (label === "uncertain") {
    return "medium";
  }
  return "info";
}
