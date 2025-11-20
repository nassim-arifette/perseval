"use client";

import { useState, useEffect } from "react";
import type { ThemeTokens } from "../../lib/constants";

type AnalyzingStateProps = {
  previewSnippet: string;
  themeTokens: ThemeTokens;
  onEdit: () => void;
};

type AnalysisStep = {
  id: string;
  label: string;
  description: string;
  icon: string;
};

const ANALYSIS_STEPS: AnalysisStep[] = [
  {
    id: "extracting",
    label: "Extracting Content",
    description: "Fetching message text and scanning for links",
    icon: "🔍"
  },
  {
    id: "analyzing",
    label: "Analyzing Message",
    description: "Checking for scam indicators and urgency",
    icon: "🤖"
  },
  {
    id: "reputation",
    label: "Checking Reputation",
    description: "Researching influencer, company & product trust",
    icon: "🌐"
  },
  {
    id: "finalizing",
    label: "Finalizing Report",
    description: "Compiling comprehensive analysis",
    icon: "✨"
  }
];

export function AnalyzingState({ previewSnippet, themeTokens, onEdit }: AnalyzingStateProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Progress through steps with realistic timing
    const stepDuration = 2500; // 2.5s per step
    const progressInterval = 50; // Update progress every 50ms

    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + (100 / (ANALYSIS_STEPS.length * (stepDuration / progressInterval)));
        return Math.min(newProgress, 100);
      });
    }, progressInterval);

    const stepTimer = setInterval(() => {
      setCurrentStep((prev) => Math.min(prev + 1, ANALYSIS_STEPS.length - 1));
    }, stepDuration);

    return () => {
      clearInterval(progressTimer);
      clearInterval(stepTimer);
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Analysis in progress...</p>
          <h2 className={`text-2xl sm:text-3xl font-semibold ${themeTokens.heading}`}>
            {ANALYSIS_STEPS[currentStep].label}
          </h2>
          <p className={`text-sm ${themeTokens.muted} mt-1`}>
            {ANALYSIS_STEPS[currentStep].description}
          </p>
        </div>
        <button
          type="button"
          onClick={onEdit}
          className="text-xs font-semibold uppercase tracking-[0.35em] text-slate-700 underline-offset-4 hover:underline shrink-0"
        >
          Edit
        </button>
      </div>

      {/* Message Preview */}
      <div className={`rounded-2xl border ${themeTokens.inputBorder} ${themeTokens.inputBg} px-4 py-3`}>
        <p className="text-xs uppercase tracking-[0.35em] text-slate-500">Message preview</p>
        <p className="mt-2 text-sm text-slate-700 line-clamp-3">{previewSnippet}</p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-3">
        <div className="flex justify-between items-center text-sm">
          <span className={`font-medium ${themeTokens.muted}`}>
            Step {currentStep + 1} of {ANALYSIS_STEPS.length}
          </span>
          <span className="font-bold text-[#F97316]">
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200 shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-[#F97316] via-[#F97316] to-[#FB923C] transition-all duration-300 ease-out rounded-full shadow-sm"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps Checklist */}
      <div className="space-y-2">
        {ANALYSIS_STEPS.map((step, index) => {
          const isComplete = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <div
              key={step.id}
              className={`flex items-start gap-3 p-3 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? 'border-[#F97316] bg-orange-50 shadow-sm'
                  : isComplete
                  ? 'border-emerald-200 bg-emerald-50'
                  : 'border-slate-200 bg-slate-50 opacity-60'
              }`}
            >
              {/* Icon/Status */}
              <div
                className={`flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-full text-lg sm:text-xl shrink-0 transition-all ${
                  isCurrent
                    ? 'bg-[#F97316] text-white animate-pulse'
                    : isComplete
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-200 text-slate-400'
                }`}
              >
                {isComplete ? '✓' : isCurrent ? step.icon : '○'}
              </div>

              {/* Label */}
              <div className="flex-1 min-w-0">
                <p
                  className={`font-semibold text-sm sm:text-base transition-colors ${
                    isCurrent
                      ? 'text-[#F97316]'
                      : isComplete
                      ? 'text-emerald-700'
                      : 'text-slate-500'
                  }`}
                >
                  {step.label}
                </p>
                <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
                  {step.description}
                </p>
              </div>

              {/* Loading Spinner for Current Step */}
              {isCurrent && (
                <div className="shrink-0">
                  <svg className="animate-spin h-5 w-5 text-[#F97316]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm">
        <p className="font-semibold text-blue-900 mb-1">💡 Did you know?</p>
        <p className="text-blue-800 text-xs sm:text-sm">
          We use Perplexity AI to research web reputation data, giving you comprehensive trust scores based on real-time information from across the internet.
        </p>
      </div>
    </div>
  );
}
