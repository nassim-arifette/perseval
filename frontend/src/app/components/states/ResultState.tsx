"use client";

import { useState } from "react";

import type {
  FullAnalysisResponse,
  HighlightSegment,
  ReasonBullet,
} from "../../lib/types";
import { severityStyles, type RiskStyle, type ThemeTokens } from "../../lib/constants";

type ResultStateProps = {
  fullResult: FullAnalysisResponse;
  previewSnippet: string;
  reasonBullets: ReasonBullet[];
  highlightedMessage: HighlightSegment[];
  activeRisk: RiskStyle;
  scorePercent: number | null;
  themeTokens: ThemeTokens;
  onClear: () => void;
};

export function ResultState({
  fullResult,
  previewSnippet,
  reasonBullets,
  highlightedMessage,
  activeRisk,
  scorePercent,
  themeTokens,
  onClear,
}: ResultStateProps) {
  const [showHighlights, setShowHighlights] = useState(false);

  const overallPercent = scorePercent;
  const messageLabel = fullResult.message_prediction.label;
  const overallTone =
    messageLabel === "scam"
      ? "border-rose-400 bg-rose-50 text-rose-700"
      : messageLabel === "uncertain"
      ? "border-amber-400 bg-amber-50 text-amber-700"
      : "border-emerald-400 bg-emerald-50 text-emerald-700";

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Overall assessment</p>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center">
            <div
              className={`relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-4 text-lg font-semibold ${overallTone}`}
            >
              {overallPercent !== null ? `${overallPercent}%` : "–"}
            </div>
            <div className="min-w-0">
              <span
                className={`badge-pop inline-flex items-center rounded-full px-3 py-1 text-[0.6rem] font-semibold uppercase tracking-[0.25em] ${activeRisk.chip}`}
              >
                {activeRisk.badgeText}
              </span>
              <p className="mt-2 text-xl font-semibold text-slate-900">{activeRisk.label}</p>
              <p className="mt-2 max-w-md text-sm text-slate-700">{activeRisk.summary}</p>
            </div>
          </div>
          {overallPercent !== null && (
            <div className="w-full max-w-[200px] space-y-2 text-xs text-slate-600">
              <p className="font-semibold uppercase tracking-[0.25em] text-slate-500">Confidence</p>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${activeRisk.gradient}`}
                  style={{ width: `${overallPercent}%` }}
                />
              </div>
              <p className="text-[0.7rem] leading-relaxed">{activeRisk.meterCopy}</p>
            </div>
          )}
        </div>
      </section>

      <div className={`rounded-2xl border ${themeTokens.inputBorder} ${themeTokens.inputBg} px-4 py-3 text-sm`}>
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.35em] text-slate-500">
          <span>Message we analyzed</span>
          {fullResult.source_details.text_origin === "instagram" && (
            <span className="text-[0.55rem] uppercase tracking-[0.35em] text-[#F97316]">
              Instagram caption
            </span>
          )}
        </div>
        <p className="mt-2 leading-relaxed text-slate-700">{previewSnippet}</p>
        {fullResult.source_details.instagram_url && (
          <a
            href={fullResult.source_details.instagram_url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block text-xs font-semibold text-[#EA580C] underline-offset-4 hover:underline"
          >
            View original post
          </a>
        )}
      </div>

      <div className="space-y-2">
        <p className="text-sm font-semibold">Why we said this</p>
        {reasonBullets.length > 0 ? (
          <ul className="space-y-2">
            {reasonBullets.map((bullet, index) => {
              const severity = severityStyles[bullet.severity];
              return (
                <li
                  key={bullet.text}
                  className={`bullet-rise relative flex items-start gap-3 rounded-2xl border ${themeTokens.surfaceBorder} px-4 py-3 text-sm before:absolute before:left-0 before:top-2 before:bottom-2 before:w-1 before:rounded-full before:content-[''] ${severity.accent}`}
                  style={{ animationDelay: `${index * 80}ms` }}
                >
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${severity.text}`}
                  >
                    {severity.icon}
                  </span>
                  <span className="text-slate-700">{bullet.text}</span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className={`text-sm ${themeTokens.muted}`}>The model didn't provide detailed reasons for this run.</p>
        )}
      </div>

      <div className="space-y-2">
        <button
          type="button"
          onClick={() => setShowHighlights((prev) => !prev)}
          className="flex w-full items-center justify-between rounded-2xl border border-slate-200 px-4 py-3 text-left text-sm font-semibold text-[#EA580C]"
        >
          Show message with highlights
          <span>{showHighlights ? "-" : "+"}</span>
        </button>
        {showHighlights && (
          <div
            className={`rounded-2xl border px-4 py-4 text-sm leading-relaxed ${themeTokens.inputBorder} ${themeTokens.inputBg}`}
          >
            {highlightedMessage.length > 0 ? (
              highlightedMessage.map((segment) =>
                segment.tone ? (
                  <span
                    key={segment.key}
                    className={`rounded px-1 ${
                      segment.tone === "high" ? "bg-[#7F1D1D]/40 text-[#FECACA]" : "bg-[#713F12]/40 text-[#FDE68A]"
                    }`}
                  >
                    {segment.content}
                  </span>
                ) : (
                  <span key={segment.key}>{segment.content}</span>
                )
              )
            ) : (
              <p className="text-sm text-slate-500">No risky words to highlight.</p>
            )}
          </div>
        )}
      </div>

      {(fullResult.influencer_trust ||
        fullResult.company_trust ||
        fullResult.product_trust ||
        fullResult.source_details.inferred_company_name ||
        fullResult.source_details.inferred_product_name) && (
        <div className="grid gap-3 md:grid-cols-2">
          {fullResult.influencer_trust && (
            <div className="space-y-3 rounded-2xl border border-[#E2E8F0] bg-white px-4 py-4 text-sm shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Influencer trust</p>
                <p className="text-lg font-semibold text-slate-900">
                  {(fullResult.influencer_trust.trust_score * 100).toFixed(0)}%{" "}
                  <span className="text-sm uppercase text-slate-500">({fullResult.influencer_trust.label})</span>
                </p>
              </div>
              <p className="text-sm text-slate-700">{fullResult.influencer_trust.notes}</p>
              <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
                <TrustStat label="Message history" value={fullResult.influencer_trust.message_history_score} />
                <TrustStat label="Followers" value={fullResult.influencer_trust.followers_score} />
                <TrustStat label="Web reputation" value={fullResult.influencer_trust.web_reputation_score} />
              </div>
              <DisclosureGauge score={fullResult.influencer_trust.disclosure_score} />
              <div className="space-y-1 text-xs text-slate-500">
                <p>
                  Followers:{" "}
                  <span className="font-semibold text-slate-800">
                    {fullResult.influencer_trust.stats.followers?.toLocaleString() ?? "–"}
                  </span>
                </p>
                {fullResult.influencer_trust.stats.url && (
                  <a
                    href={fullResult.influencer_trust.stats.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[#EA580C] underline-offset-4 hover:underline"
                  >
                    View Instagram profile
                  </a>
                )}
              </div>
            </div>
          )}

          <div className="space-y-3 rounded-2xl border border-[#E2E8F0] bg-white px-4 py-4 text-sm shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Company reputation</p>
              {fullResult.company_trust && (
                <p className="text-lg font-semibold text-slate-900">
                  {(fullResult.company_trust.trust_score * 100).toFixed(0)}%
                </p>
              )}
            </div>
            {fullResult.company_trust ? (
              <>
                <p className="text-sm font-semibold text-slate-800">{fullResult.company_trust.name}</p>
                <p className="text-sm text-slate-700">{fullResult.company_trust.summary}</p>
                {fullResult.company_trust.issues.length > 0 && (
                  <ul className="list-disc space-y-1 pl-5 text-xs text-[#7F1D1D]">
                    {fullResult.company_trust.issues.map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-600">
                {fullResult.source_details.inferred_company_name
                  ? `We detected "${fullResult.source_details.inferred_company_name}" in the message, but there was not enough data to build a reputation snapshot.`
                  : "No clear company or product was detected in this message, so the reputation step was skipped."}
              </p>
            )}
          </div>

          <div className="space-y-3 rounded-2xl border border-[#E2E8F0] bg-white px-4 py-4 text-sm shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Product reliability</p>
              {fullResult.product_trust && (
                <p className="text-lg font-semibold text-slate-900">
                  {(fullResult.product_trust.trust_score * 100).toFixed(0)}%
                </p>
              )}
            </div>
            {fullResult.product_trust ? (
              <>
                <p className="text-sm font-semibold text-slate-800">{fullResult.product_trust.name}</p>
                <p className="text-sm text-slate-700">{fullResult.product_trust.summary}</p>
                {fullResult.product_trust.issues.length > 0 && (
                  <ul className="list-disc space-y-1 pl-5 text-xs text-[#7F1D1D]">
                    {fullResult.product_trust.issues.map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-600">
                {fullResult.source_details.inferred_product_name
                  ? `We detected "${fullResult.source_details.inferred_product_name}" but there was not enough data to build a product reliability snapshot.`
                  : "No clear product was detected in this message, so the reliability step was skipped."}
              </p>
            )}
          </div>
        </div>
      )}

      <p className="text-xs text-slate-600">{fullResult.final_summary}</p>
      <p className="text-xs text-slate-600">Never send money to strangers promising returns.</p>

      <button
        type="button"
        onClick={onClear}
        className="text-sm font-semibold text-[#EA580C] underline-offset-4 hover:underline"
      >
        Analyze another message
      </button>
    </div>
  );
}

function TrustStat({ label, value }: { label: string; value: number }) {
  const pct = value * 100;
  const tone =
    pct >= 75 ? "bg-emerald-100 text-emerald-800 border-emerald-200" :
    pct >= 40 ? "bg-amber-100 text-amber-800 border-amber-200" :
    "bg-rose-100 text-rose-800 border-rose-200";

  return (
    <div className="flex flex-col items-center gap-2 rounded-xl bg-slate-50 px-3 py-3 text-center">
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-full border text-xs font-semibold ${tone}`}
      >
        {pct.toFixed(0)}%
      </div>
      <p className="uppercase tracking-widest text-[0.6rem] text-slate-500 leading-tight">
        {label}
      </p>
    </div>
  );
}

function DisclosureGauge({ score }: { score: number }) {
  const pct = Math.round(Math.min(Math.max(score, 0), 1) * 100);
  const tone =
    pct >= 90 ? "bg-emerald-400" :
    pct >= 60 ? "bg-amber-400" :
    "bg-rose-400";
  const copy =
    pct >= 90
      ? "Ads look transparently disclosed."
      : pct >= 60
      ? "Disclosures appear occasionally."
      : "No disclosure markers spotted recently.";

  return (
    <div className="rounded-2xl border border-slate-200 px-4 py-3 text-xs text-slate-600">
      <div className="flex items-center justify-between text-[0.65rem] uppercase tracking-[0.3em] text-slate-500">
        <span>Ad disclosure</span>
        <span className="font-semibold text-slate-900">{pct}%</span>
      </div>
      <div className="mt-2 h-2 w-full rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-[0.7rem] leading-relaxed text-slate-500">{copy}</p>
    </div>
  );
}
