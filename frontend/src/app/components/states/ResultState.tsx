"use client";

import { useState } from "react";

import type { HighlightSegment, ReasonBullet } from "../../lib/types";
import { severityStyles, type RiskStyle, type ThemeTokens } from "../../lib/constants";

type ResultStateProps = {
  previewSnippet: string;
  reasonBullets: ReasonBullet[];
  highlightedMessage: HighlightSegment[];
  activeRisk: RiskStyle;
  scorePercent: number | null;
  themeTokens: ThemeTokens;
  onClear: () => void;
};

export function ResultState({
  previewSnippet,
  reasonBullets,
  highlightedMessage,
  activeRisk,
  scorePercent,
  themeTokens,
  onClear,
}: ResultStateProps) {
  const [showHighlights, setShowHighlights] = useState(false);

  return (
    <div className="space-y-6">
      <div className="text-center">
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Result</p>
        {scorePercent !== null && (
          <p className="mt-1 text-xs text-slate-500">Confidence {scorePercent}%</p>
        )}
        <div className={`badge-pop mx-auto mt-4 inline-flex flex-col items-center rounded-full px-6 py-6 ${activeRisk.badgeBg}`}>
          <span className="text-xs uppercase tracking-[0.35em] text-[#B45309]">{activeRisk.badgeText}</span>
          <p className="mt-2 text-3xl font-semibold uppercase tracking-wide text-slate-900">{activeRisk.label}</p>
        </div>
        <p className="mt-4 text-base text-slate-700">{activeRisk.summary}</p>
      </div>

      <div className={`rounded-2xl border ${themeTokens.inputBorder} ${themeTokens.inputBg} px-4 py-3 text-sm`}>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Message preview</p>
        <p className="mt-2 leading-relaxed text-slate-700">{previewSnippet}</p>
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
                  className={`bullet-rise flex items-start gap-3 rounded-2xl border ${themeTokens.surfaceBorder} px-4 py-3 text-sm`}
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
