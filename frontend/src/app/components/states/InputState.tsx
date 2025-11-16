"use client";

import type { KeyboardEvent } from "react";

import { MAX_CHARACTERS, type ThemeTokens } from "../../lib/constants";

type InputStateProps = {
  text: string;
  charCountCopy: string;
  canSubmit: boolean;
  loading: boolean;
  instagramUrl: string;
  influencerHandle: string;
  onTextChange: (value: string) => void;
  onInstagramUrlChange: (value: string) => void;
  onInfluencerHandleChange: (value: string) => void;
  onKeyDown: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  onExample: () => void;
  buttonLabel: string;
  themeTokens: ThemeTokens;
};

export function InputState({
  text,
  charCountCopy,
  canSubmit,
  loading,
  instagramUrl,
  influencerHandle,
  onTextChange,
  onInstagramUrlChange,
  onInfluencerHandleChange,
  onKeyDown,
  onSubmit,
  onExample,
  buttonLabel,
  themeTokens,
}: InputStateProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Input</p>
        <h1 className={`text-2xl font-semibold ${themeTokens.heading}`}>
          Paste the message or caption you're unsure about
        </h1>
        <p className={`text-sm ${themeTokens.muted}`}>We only analyze it for this session.</p>
      </div>

      <div>
        <textarea
          maxLength={MAX_CHARACTERS}
          value={text}
          disabled={loading}
          onChange={(event) => onTextChange(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Paste the message, DM or caption..."
          className={`w-full rounded-2xl border px-4 py-4 text-base leading-relaxed outline-none transition focus:ring-2 focus:ring-[#F97316]/40 ${themeTokens.inputBg} ${themeTokens.inputBorder} ${themeTokens.placeholder}`}
        />
        <div className={`mt-2 flex items-center justify-between text-xs ${themeTokens.muted}`}>
          <span>{charCountCopy}</span>
          <span>Cmd/Ctrl + Enter</span>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Instagram URL (optional)</p>
          <input
            type="url"
            placeholder="https://www.instagram.com/p/..."
            value={instagramUrl}
            disabled={loading}
            onChange={(event) => onInstagramUrlChange(event.target.value)}
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#F97316]/40 ${themeTokens.inputBg} ${themeTokens.inputBorder}`}
          />
        </div>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Influencer handle (optional)</p>
          <input
            type="text"
            placeholder="@handle"
            value={influencerHandle}
            disabled={loading}
            onChange={(event) => onInfluencerHandleChange(event.target.value)}
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#F97316]/40 ${themeTokens.inputBg} ${themeTokens.inputBorder}`}
          />
          <p className={`text-[0.7rem] ${themeTokens.muted}`}>
            Leave blank to auto-use the owner of the Instagram URL (when provided).
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit}
          className="w-full rounded-2xl bg-[#F97316] px-4 py-3 text-base font-semibold text-white transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#F97316] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {buttonLabel}
        </button>
        <button
          type="button"
          onClick={onExample}
          className="text-xs font-semibold text-[#F97316] underline-offset-4 hover:underline"
        >
          Try an example
        </button>
      </div>
    </div>
  );
}
