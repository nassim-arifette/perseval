"use client";

import type { ThemeTokens } from "../../lib/constants";

type AnalyzingStateProps = {
  previewSnippet: string;
  themeTokens: ThemeTokens;
  onEdit: () => void;
};

export function AnalyzingState({ previewSnippet, themeTokens, onEdit }: AnalyzingStateProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Analyzing risk...</p>
          <h2 className={`text-2xl font-semibold ${themeTokens.heading}`}>Hold tight</h2>
          <p className={`text-sm ${themeTokens.muted}`}>We are checking urgency, links, and claims.</p>
        </div>
        <button
          type="button"
          onClick={onEdit}
          className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-700 underline-offset-4 hover:underline"
        >
          Edit
        </button>
      </div>

      <div className={`rounded-2xl border ${themeTokens.inputBorder} ${themeTokens.inputBg} px-4 py-3`}>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Message preview</p>
        <p className="mt-2 truncate text-sm text-slate-700">{previewSnippet}</p>
      </div>

      <div className="space-y-3">
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
          <div className="h-full w-1/2 animate-pulse bg-gradient-to-r from-[#F97316]/20 via-[#F97316]/60 to-[#F97316]/20" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-3/4 rounded-full bg-slate-200 animate-pulse" />
          <div className="h-20 rounded-2xl bg-slate-100 animate-pulse" />
          <div className="h-4 w-1/2 rounded-full bg-slate-200 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
