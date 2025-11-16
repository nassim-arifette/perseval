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
  companyName: string;
  productName: string;
  onTextChange: (value: string) => void;
  onInstagramUrlChange: (value: string) => void;
  onInfluencerHandleChange: (value: string) => void;
  onCompanyNameChange: (value: string) => void;
  onProductNameChange: (value: string) => void;
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
  companyName,
  productName,
  onTextChange,
  onInstagramUrlChange,
  onInfluencerHandleChange,
  onCompanyNameChange,
  onProductNameChange,
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
          Paste the message or caption you&apos;re unsure about
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
        <p className={`mt-1 text-[0.7rem] ${themeTokens.muted}`}>
          Drop only an Instagram link here and we&apos;ll auto-detect it.
        </p>
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

      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Company name (optional)</p>
          <input
            type="text"
            placeholder="Brand or organization..."
            value={companyName}
            disabled={loading}
            onChange={(event) => onCompanyNameChange(event.target.value)}
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#F97316]/40 ${themeTokens.inputBg} ${themeTokens.inputBorder}`}
          />
          <p className={`text-[0.7rem] ${themeTokens.muted}`}>
            Pinpointing the brand improves the company reputation lookup.
          </p>
        </div>
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.35em] text-[#94A3B8]">Product name (optional)</p>
          <input
            type="text"
            placeholder="Product or offer mentioned..."
            value={productName}
            disabled={loading}
            onChange={(event) => onProductNameChange(event.target.value)}
            className={`w-full rounded-2xl border px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[#F97316]/40 ${themeTokens.inputBg} ${themeTokens.inputBorder}`}
          />
          <p className={`text-[0.7rem] ${themeTokens.muted}`}>
            This helps the product reliability check find exact results.
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
