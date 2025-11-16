"use client";

import { KeyboardEvent, ReactNode, useMemo, useRef, useState } from "react";

import { HeaderBar } from "./components/HeaderBar";
import { AnalyzingState } from "./components/states/AnalyzingState";
import { InputState } from "./components/states/InputState";
import { ResultState } from "./components/states/ResultState";
import {
  ANALYZE_ENDPOINT,
  MAX_CHARACTERS,
  disclaimerCopy,
  riskBackdrop,
  riskStyles,
  sampleMessages,
  themeConfig,
} from "./lib/constants";
import type {
  FullAnalysisResponse,
  HighlightSegment,
  ReasonBullet,
  ScamPrediction,
} from "./lib/types";
import { buildReasonBullets, clampPercent, deriveRiskTier, highlightText } from "./lib/risk";

type CardState = "input" | "analyzing" | "result";

export default function Home() {
  const [text, setText] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  const [influencerHandle, setInfluencerHandle] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FullAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const themeTokens = themeConfig.light;
  const charactersUsed = text.length;
  const charCountCopy = `${charactersUsed} / ${MAX_CHARACTERS}`;
  const cardState: CardState = loading ? "analyzing" : result ? "result" : "input";
  const messagePrediction: ScamPrediction | null = result?.message_prediction ?? null;
  const canSubmit =
    !loading && (Boolean(text.trim()) || Boolean(instagramUrl.trim()));
  const riskTier = deriveRiskTier(messagePrediction?.label);
  const activeRisk = riskStyles[riskTier];
  const previewSource = (messagePrediction?.raw_post_text ?? text).trim();
  const previewSnippet = previewSource
    ? previewSource.length > 200
      ? `${previewSource.slice(0, 200)}...`
      : previewSource
    : "No message has been provided yet.";
  const scorePercent = messagePrediction ? clampPercent(messagePrediction.score) : null;
  const cardSurfaceClass =
    cardState === "result"
      ? activeRisk.cardTone
      : `${themeTokens.surfaceBorder} ${themeTokens.surfaceBg}`;

  const reasonBullets = useMemo<ReasonBullet[]>(
    () => buildReasonBullets(messagePrediction?.reason ?? "", messagePrediction?.label ?? null),
    [messagePrediction?.label, messagePrediction?.reason]
  );

  const highlightedMessage = useMemo<HighlightSegment[]>(
    () => (messagePrediction?.raw_post_text ? highlightText(messagePrediction.raw_post_text) : []),
    [messagePrediction?.raw_post_text]
  );

  async function handleAnalyze() {
    if (!text.trim() && !instagramUrl.trim()) {
      setError("Paste message text or provide an Instagram URL to analyze.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(ANALYZE_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text.trim() || undefined,
          instagram_url: instagramUrl.trim() || undefined,
          influencer_handle: influencerHandle.trim() || undefined,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => null);
        throw new Error(errBody?.detail ?? "Backend error");
      }

      const data: FullAnalysisResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      if (err?.name === "AbortError") {
        return;
      }
      setResult(null);
      setError(err?.message ?? "We couldn't analyze this. Try again soon.");
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      setLoading(false);
    }
  }

  function handleTextareaKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && canSubmit) {
      event.preventDefault();
      handleAnalyze();
    }
  }

  function handleClear() {
    setText("");
    setInstagramUrl("");
    setInfluencerHandle("");
    setResult(null);
    setError(null);
  }

  function handleExampleInsert() {
    const sample = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
    setText(sample.text);
    setResult(null);
    setError(null);
  }

  function handleEditDuringAnalysis() {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
    setError(null);
    setResult(null);
  }

  const buttonLabel = loading ? "Analyzing..." : "Analyze";

  const backgroundClass =
    cardState === "result" ? `bg-gradient-to-br ${riskBackdrop[riskTier]}` : themeTokens.body;

  let cardContent: ReactNode = null;
  if (cardState === "input") {
    cardContent = (
      <InputState
        text={text}
        instagramUrl={instagramUrl}
        influencerHandle={influencerHandle}
        charCountCopy={charCountCopy}
        canSubmit={canSubmit}
        loading={loading}
        onTextChange={setText}
        onInstagramUrlChange={setInstagramUrl}
        onInfluencerHandleChange={setInfluencerHandle}
        onKeyDown={handleTextareaKeyDown}
        onSubmit={handleAnalyze}
        onExample={handleExampleInsert}
        buttonLabel={buttonLabel}
        themeTokens={themeTokens}
      />
    );
  } else if (cardState === "analyzing") {
    cardContent = (
      <AnalyzingState
        previewSnippet={previewSnippet}
        themeTokens={themeTokens}
        onEdit={handleEditDuringAnalysis}
      />
    );
  } else if (cardState === "result" && result && messagePrediction) {
    cardContent = (
      <ResultState
        fullResult={result}
        previewSnippet={previewSnippet}
        reasonBullets={reasonBullets}
        highlightedMessage={highlightedMessage}
        activeRisk={activeRisk}
        scorePercent={scorePercent}
        themeTokens={themeTokens}
        onClear={handleClear}
      />
    );
  }

  return (
    <div className={`min-h-screen ${backgroundClass}`}>
      <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 py-8">
        <HeaderBar headerBorderClass={themeTokens.headerBorder} />

        <main className="flex flex-1 items-center justify-center py-8">
          <div className={`w-full max-w-3xl rounded-[32px] border ${cardSurfaceClass} ${themeTokens.cardShadow} p-8`}>
            <div key={cardState} className="fade-card">
              {cardContent}
            </div>

            {error && cardState !== "analyzing" && (
              <p className="mt-4 rounded-2xl border border-[#FECACA] bg-[#FEF2F2] px-4 py-3 text-sm text-[#991B1B]">
                {error}
              </p>
            )}

            <p className={`mt-6 text-[0.7rem] leading-relaxed ${themeTokens.muted}`}>{disclaimerCopy}</p>
          </div>
        </main>
      </div>
    </div>
  );
}
