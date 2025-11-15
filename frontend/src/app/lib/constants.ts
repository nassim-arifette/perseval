import type { RiskTier, Severity, ThemeKey } from "./types";

export const ANALYZE_ENDPOINT = "/api/analyze";
export const MAX_CHARACTERS = 1200;

export const sampleMessages = [
  {
    title: "Crypto airdrop promise",
    text: "You've been selected for our exclusive crypto airdrop. Send 0.05 BTC to 1FDB4... and we'll double it back instantly. Offer closes tonight.",
  },
  {
    title: "Urgent bank verification SMS",
    text: "FRAUD ALERT: Your bank account is locked. Verify your debit card within 15 minutes at https://secure-fix.bank-check.com or all transfers pause.",
  },
  {
    title: "Influencer discount code",
    text: "Final drop! I'm partnering with NeoFit to give you 80% off. Tap https://neofit-deals.store/?ref=insta-now and use code QUICK80 before it expires today.",
  },
];

export const disclaimerCopy =
  "This tool helps you assess risk but can't guarantee safety. When in doubt, do not send money or sensitive information.";

export const riskStyles: Record<
  RiskTier,
  {
    label: string;
    badgeText: string;
    chip: string;
    badgeBg: string;
    cardTone: string;
    gradient: string;
    summary: string;
    meterCopy: string;
  }
> = {
  high: {
    label: "High-risk signal",
    badgeText: "scam alert",
    chip: "bg-[#2D0F11] text-[#FECACA] border border-[#F87171]/60",
    badgeBg: "bg-[#FEE2E2]",
    cardTone: "bg-[#FFF1F2] border-[#FECACA]",
    gradient: "from-[#F97373] via-[#F97316] to-[#EF4444]",
    summary:
      "Multiple scam markers detected. Treat the content as untrusted until you verify through official channels.",
    meterCopy:
      "Multiple scam markers detected. Treat this as untrusted and verify via official channels.",
  },
  caution: {
    label: "Suspicious - caution advised",
    badgeText: "warning",
    chip: "bg-[#31240C] text-[#FDE68A] border border-[#FBBF24]/60",
    badgeBg: "bg-[#FEF3C7]",
    cardTone: "bg-[#FFFBEB] border-[#FCD34D]",
    gradient: "from-[#FBBF24] via-[#F59E0B] to-[#F97316]",
    summary:
      "Some warning signs were spotted. Double-check sender identity and URLs before you act.",
    meterCopy: "Some risk markers found. Double-check sender and URL before acting.",
  },
  low: {
    label: "Likely low risk",
    badgeText: "low risk",
    chip: "bg-[#102814] text-[#A7F3D0] border border-[#16A34A]/60",
    badgeBg: "bg-[#D1FAE5]",
    cardTone: "bg-[#ECFDF5] border-[#6EE7B7]",
    gradient: "from-[#34D399] via-[#10B981] to-[#059669]",
    summary:
      "No strong scam markers detected. Still follow normal caution and never share sensitive codes.",
    meterCopy:
      "No strong scam markers detected, but keep normal caution on any financial request.",
  },
};

export type RiskStyle = (typeof riskStyles)[RiskTier];

export const themeConfig: Record<
  ThemeKey,
  {
    body: string;
    panelBg: string;
    panelBorder: string;
    helperBg: string;
    helperBorder: string;
    inputBg: string;
    inputBorder: string;
    placeholder: string;
    muted: string;
    helperText: string;
    track: string;
    exampleBorder: string;
    exampleBg: string;
    exampleHover: string;
    heading: string;
    subheading: string;
    chipBg: string;
    surfaceBg: string;
    surfaceBorder: string;
    cardShadow: string;
    headerBorder: string;
  }
> = {
  dark: {
    body: "bg-[#05070A] text-slate-100",
    panelBg: "bg-[#0B111C]/90",
    panelBorder: "border-[#1C2536]",
    helperBg: "bg-[#090F18]/90",
    helperBorder: "border-[#111A2A]",
    inputBg: "bg-[#0F1624]",
    inputBorder: "border-[#1E2737]",
    placeholder: "placeholder:text-slate-500",
    muted: "text-[#94A3B8]",
    helperText: "text-slate-300",
    track: "bg-white/10",
    exampleBorder: "border-[#1F2737]",
    exampleBg: "bg-[#111A2A]",
    exampleHover: "hover:border-[#F97316] hover:text-white",
    heading: "text-white",
    subheading: "text-slate-200",
    chipBg: "bg-[#111A2A]",
    surfaceBg: "bg-white/5",
    surfaceBorder: "border-white/10",
    cardShadow: "shadow-[0_45px_120px_rgba(0,0,0,0.55)]",
    headerBorder: "border-white/10",
  },
  light: {
    body: "bg-[#F7FAFF] text-slate-900",
    panelBg: "bg-white/95",
    panelBorder: "border-[#E2E8F0]",
    helperBg: "bg-white",
    helperBorder: "border-[#E2E8F0]",
    inputBg: "bg-white",
    inputBorder: "border-[#CBD5F5]",
    placeholder: "placeholder:text-slate-400",
    muted: "text-slate-500",
    helperText: "text-slate-600",
    track: "bg-slate-200",
    exampleBorder: "border-[#E2E8F0]",
    exampleBg: "bg-slate-50",
    exampleHover: "hover:border-[#F97316] hover:text-[#EA580C]",
    heading: "text-slate-900",
    subheading: "text-slate-600",
    chipBg: "bg-slate-100",
    surfaceBg: "bg-white",
    surfaceBorder: "border-slate-200",
    cardShadow: "shadow-[0_45px_120px_rgba(15,23,42,0.08)]",
    headerBorder: "border-slate-200",
  },
};

export type ThemeTokens = (typeof themeConfig)[ThemeKey];

export const severityStyles: Record<
  Severity,
  { icon: string; text: string; accent: string }
> = {
  high: { icon: "!", text: "text-[#FECACA]", accent: "before:bg-[#F87171]/60" },
  medium: { icon: "~", text: "text-[#FDE68A]", accent: "before:bg-[#FBBF24]/50" },
  info: { icon: "*", text: "text-slate-200", accent: "before:bg-slate-300/50" },
};

export const riskBackdrop: Record<RiskTier, string> = {
  high: "from-[#FEE2E2] via-[#FECACA] to-[#FEE2E2]",
  caution: "from-[#FEF3C7] via-[#FDE68A] to-[#FFF7E0]",
  low: "from-[#DCFCE7] via-[#BBF7D0] to-[#ECFDF5]",
};
