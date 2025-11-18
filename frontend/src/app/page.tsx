'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from './context/ThemeContext';
import { getThemeColors, theme, animations } from './lib/theme';
import { Card } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { Textarea } from './components/ui/Textarea';
import { Input } from './components/ui/Input';
import FeedbackForm from './components/FeedbackForm';
import { storage } from './lib/storage';
import type { FullAnalysisResponse } from './lib/types';

const ANALYZE_ENDPOINT = '/api/analyze/full';
const MAX_CHARACTERS = 1200;
const INSTAGRAM_URL_PATTERN = /^(?:https?:\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)\/[^\s]+$/i;
const TIKTOK_URL_PATTERN = /^(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com)\/[^\s]+$/i;

const sampleMessages = [
  { text: '🚨 URGENT: Your bank account has been compromised. Click here immediately to verify your identity and prevent suspension.' },
  { text: 'Hey! 💎 I just made $5,000 in 24 hours with this crypto airdrop! Limited spots available, DM me for the link!' },
  { text: 'Use code SAVE20 for 20% off your first purchase! I love their skincare line. #ad #sponsored' },
];

export default function Home() {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);

  const [text, setText] = useState('');
  const [instagramUrl, setInstagramUrl] = useState('');
  const [tiktokUrl, setTiktokUrl] = useState('');
  const [influencerHandle, setInfluencerHandle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [productName, setProductName] = useState('');
  const [showOptionalFields, setShowOptionalFields] = useState(false);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FullAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedCard, setExpandedCard] = useState<'influencer' | 'company' | 'product' | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const canSubmit = !loading && (Boolean(text.trim()) || Boolean(instagramUrl.trim()) || Boolean(tiktokUrl.trim()));

  const normalizeUrl = (value: string): string => {
    const cleaned = value.trim().replace(/^\/\//, '');
    return /^https?:\/\//i.test(cleaned) ? cleaned : `https://${cleaned}`;
  };

  const extractInstagramUrl = (value: string): string | null => {
    const trimmed = value.trim();
    if (!trimmed || !INSTAGRAM_URL_PATTERN.test(trimmed)) return null;
    return normalizeUrl(trimmed);
  };

  const extractTiktokUrl = (value: string): string | null => {
    const trimmed = value.trim();
    if (!trimmed || !TIKTOK_URL_PATTERN.test(trimmed)) return null;
    return normalizeUrl(trimmed);
  };

  const handleAnalyze = async () => {
    const trimmedText = text.trim();
    const trimmedInstagramUrl = instagramUrl.trim();
    const trimmedTiktokUrl = tiktokUrl.trim();

    if (trimmedInstagramUrl && trimmedTiktokUrl) {
      setError('Provide either an Instagram URL or a TikTok URL, not both.');
      return;
    }

    const autoInstagramUrl = !trimmedInstagramUrl && trimmedText ? extractInstagramUrl(trimmedText) : null;
    const autoTiktokUrl = !trimmedTiktokUrl && trimmedText ? extractTiktokUrl(trimmedText) : null;
    const payloadText = autoInstagramUrl || autoTiktokUrl ? '' : trimmedText;
    const payloadInstagramUrl = trimmedInstagramUrl || autoInstagramUrl || '';
    const payloadTiktokUrl = trimmedTiktokUrl || autoTiktokUrl || '';

    if (!payloadText && !payloadInstagramUrl && !payloadTiktokUrl) {
      setError('Paste message text or provide an Instagram or TikTok URL to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(ANALYZE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: payloadText || undefined,
          instagram_url: payloadInstagramUrl || undefined,
          tiktok_url: payloadTiktokUrl || undefined,
          influencer_handle: influencerHandle.trim() || undefined,
          company_name: companyName.trim() || undefined,
          product_name: productName.trim() || undefined,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => null);
        throw new Error(errBody?.detail ?? 'Backend error');
      }

      const data: FullAnalysisResponse = await response.json();
      setResult(data);

      // Save to storage
      storage.saveAnalysis(
        {
          text: payloadText || undefined,
          instagramUrl: payloadInstagramUrl || undefined,
          tiktokUrl: payloadTiktokUrl || undefined,
          influencerHandle: influencerHandle.trim() || undefined,
          companyName: companyName.trim() || undefined,
          productName: productName.trim() || undefined,
        },
        data
      );
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setResult(null);
      const fallbackMessage = "We couldn't analyze this. Try again soon.";
      if (err instanceof Error) {
        setError(err.message || fallbackMessage);
      } else {
        setError(fallbackMessage);
      }
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }
      setLoading(false);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter' && canSubmit) {
      event.preventDefault();
      handleAnalyze();
    }
  };

  const handleClear = () => {
    setText('');
    setInstagramUrl('');
    setTiktokUrl('');
    setInfluencerHandle('');
    setCompanyName('');
    setProductName('');
    setResult(null);
    setError(null);
    setShowOptionalFields(false);
  };

  const handleExample = () => {
    const sample = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
    setText(sample.text);
    setResult(null);
    setError(null);
  };

  const getLabelColor = (label: string) => {
    switch (label) {
      case 'scam':
        return colors.accent.danger;
      case 'not_scam':
        return colors.accent.success;
      case 'uncertain':
        return colors.accent.warning;
      default:
        return colors.accent.info;
    }
  };

  const getLabelIcon = (label: string) => {
    switch (label) {
      case 'scam':
        return '⚠️';
      case 'not_scam':
        return '✅';
      case 'uncertain':
        return '❓';
      default:
        return '📄';
    }
  };

  return (
    <div
      className="min-h-screen p-8"
      style={{ backgroundColor: colors.background.secondary }}
    >
      <motion.div
        initial="initial"
        animate="animate"
        variants={animations.staggerContainer}
        className="max-w-5xl mx-auto"
      >
        {/* Hero Section */}
        <motion.div variants={animations.slideDown} className="text-center mb-12">
          <h1 className="text-6xl font-bold mb-4">
            <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Perseval
            </span>
          </h1>
          <p className="text-xl mb-2" style={{ color: colors.text.secondary }}>
            AI-Powered Scam Detection & Trust Analysis
          </p>
          <p className="text-sm" style={{ color: colors.text.tertiary }}>
            Analyze messages, social media posts, and influencer credibility in seconds
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {!result ? (
            /* Input Form */
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <Card padding="lg" hover={false}>
                <div className="space-y-6">
                  {/* Main Textarea */}
                  <Textarea
                    label="Message or Post Text"
                    placeholder="Paste the message, caption, or text you want to analyze..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={6}
                    maxCount={MAX_CHARACTERS}
                    showCount
                    error={error || undefined}
                  />

                  {/* Quick Actions */}
                  <div className="flex gap-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleExample}
                      icon={
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                          <path d="M15.98 1.804a1 1 0 00-1.96 0l-.24 1.192a1 1 0 01-.784.785l-1.192.238a1 1 0 000 1.962l1.192.238a1 1 0 01.785.785l.238 1.192a1 1 0 001.962 0l.238-1.192a1 1 0 01.785-.785l1.192-.238a1 1 0 000-1.962l-1.192-.238a1 1 0 01-.785-.785l-.238-1.192zM6.949 5.684a1 1 0 00-1.898 0l-.683 2.051a1 1 0 01-.633.633l-2.051.683a1 1 0 000 1.898l2.051.684a1 1 0 01.633.632l.683 2.051a1 1 0 001.898 0l.683-2.051a1 1 0 01.633-.633l2.051-.683a1 1 0 000-1.898l-2.051-.683a1 1 0 01-.633-.633L6.95 5.684zM13.949 13.684a1 1 0 00-1.898 0l-.184.551a1 1 0 01-.632.633l-.551.183a1 1 0 000 1.898l.551.183a1 1 0 01.633.633l.183.551a1 1 0 001.898 0l.184-.551a1 1 0 01.632-.633l.551-.183a1 1 0 000-1.898l-.551-.184a1 1 0 01-.633-.632l-.183-.551z" />
                        </svg>
                      }
                    >
                      Try Example
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowOptionalFields(!showOptionalFields)}
                      icon={
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                          <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                        </svg>
                      }
                    >
                      {showOptionalFields ? 'Hide' : 'Show'} Optional Fields
                    </Button>
                  </div>

                  {/* Optional Fields */}
                  <AnimatePresence>
                    {showOptionalFields && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-4 overflow-hidden"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <Input
                            label="Instagram URL"
                            placeholder="https://instagram.com/p/..."
                            value={instagramUrl}
                            onChange={(e) => setInstagramUrl(e.target.value)}
                          />
                          <Input
                            label="TikTok URL"
                            placeholder="https://tiktok.com/@..."
                            value={tiktokUrl}
                            onChange={(e) => setTiktokUrl(e.target.value)}
                          />
                          <Input
                            label="Influencer Handle"
                            placeholder="@username"
                            value={influencerHandle}
                            onChange={(e) => setInfluencerHandle(e.target.value)}
                          />
                          <Input
                            label="Company Name"
                            placeholder="Brand or company name"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                          />
                        </div>
                        <Input
                          label="Product Name"
                          placeholder="Product or service name"
                          value={productName}
                          onChange={(e) => setProductName(e.target.value)}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Submit Button */}
                  <Button
                    fullWidth
                    gradient
                    size="lg"
                    disabled={!canSubmit}
                    loading={loading}
                    onClick={handleAnalyze}
                    icon={
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                        <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                      </svg>
                    }
                    iconPosition="left"
                  >
                    {loading ? 'Analyzing...' : 'Analyze for Scams'}
                  </Button>

                  <p className="text-xs text-center" style={{ color: colors.text.tertiary }}>
                    Press <kbd className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 font-mono">⌘+Enter</kbd> or <kbd className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 font-mono">Ctrl+Enter</kbd> to analyze
                  </p>
                </div>
              </Card>
            </motion.div>
          ) : (
            /* Results */
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              {/* Main Result Card */}
              <Card padding="lg" hover={false}>
                <div className="flex items-start gap-6">
                  {/* Icon and Label */}
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                    className="flex-shrink-0"
                  >
                    <div
                      className="w-20 h-20 rounded-3xl flex items-center justify-center text-4xl"
                      style={{
                        background: `linear-gradient(135deg, ${getLabelColor(result.message_prediction.label)}20, ${getLabelColor(result.message_prediction.label)}40)`,
                        border: `3px solid ${getLabelColor(result.message_prediction.label)}`,
                      }}
                    >
                      {getLabelIcon(result.message_prediction.label)}
                    </div>
                  </motion.div>

                  {/* Content */}
                  <div className="flex-1">
                    <h2
                      className="text-3xl font-bold mb-2 capitalize"
                      style={{ color: colors.text.primary }}
                    >
                      {result.message_prediction.label.replace('_', ' ')}
                    </h2>
                    <p className="text-lg mb-4" style={{ color: colors.text.secondary }}>
                      {result.message_prediction.label === 'scam'
                        ? 'This message shows strong signs of being a scam'
                        : result.message_prediction.label === 'not_scam'
                        ? 'This message appears to be legitimate'
                        : 'This message requires further review'}
                    </p>

                    {/* Score Bar */}
                    <div className="mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium" style={{ color: colors.text.secondary }}>
                          Confidence Score
                        </span>
                        <span className="text-lg font-bold" style={{ color: colors.text.primary }}>
                          {(result.message_prediction.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div
                        className="h-3 rounded-full overflow-hidden"
                        style={{ backgroundColor: colors.border.default }}
                      >
                        <motion.div
                          className="h-full rounded-full"
                          style={{
                            background: `linear-gradient(90deg, ${getLabelColor(result.message_prediction.label)}, ${getLabelColor(result.message_prediction.label)}BB)`,
                          }}
                          initial={{ width: 0 }}
                          animate={{ width: `${result.message_prediction.score * 100}%` }}
                          transition={{ duration: 1, ease: 'easeOut' }}
                        />
                      </div>
                    </div>

                    {/* Reason */}
                    {result.message_prediction.reason && (
                      <div
                        className="p-4 rounded-xl"
                        style={{
                          backgroundColor: colors.background.secondary,
                          border: `1px solid ${colors.border.default}`,
                        }}
                      >
                        <p style={{ color: colors.text.primary }}>
                          {result.message_prediction.reason}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6">
                  <Button variant="primary" onClick={handleClear} fullWidth>
                    Check Another
                  </Button>
                </div>
              </Card>

              {/* Additional Trust Cards */}
              {(result.influencer_trust || result.company_trust || result.product_trust) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {result.influencer_trust && (
                    <motion.div
                      onClick={() => setExpandedCard(expandedCard === 'influencer' ? null : 'influencer')}
                      className="cursor-pointer"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card padding="md" hover>
                        <h3 className="text-sm font-semibold mb-2" style={{ color: colors.text.secondary }}>
                          Influencer Trust
                        </h3>
                        <p className="text-2xl font-bold mb-2" style={{ color: colors.text.primary }}>
                          {(result.influencer_trust.trust_score * 100).toFixed(0)}%
                        </p>
                        <div
                          className="h-2 rounded-full overflow-hidden mb-2"
                          style={{ backgroundColor: colors.border.default }}
                        >
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.info }}
                            initial={{ width: 0 }}
                            animate={{ width: `${result.influencer_trust.trust_score * 100}%` }}
                          />
                        </div>
                        <p className="text-xs text-center" style={{ color: colors.text.tertiary }}>
                          Click for details
                        </p>
                      </Card>
                    </motion.div>
                  )}
                  {result.company_trust && (
                    <motion.div
                      onClick={() => setExpandedCard(expandedCard === 'company' ? null : 'company')}
                      className="cursor-pointer"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card padding="md" hover>
                        <h3 className="text-sm font-semibold mb-2" style={{ color: colors.text.secondary }}>
                          Company Reputation
                        </h3>
                        <p className="text-2xl font-bold mb-2" style={{ color: colors.text.primary }}>
                          {(result.company_trust.trust_score * 100).toFixed(0)}%
                        </p>
                        <div
                          className="h-2 rounded-full overflow-hidden mb-2"
                          style={{ backgroundColor: colors.border.default }}
                        >
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.success }}
                            initial={{ width: 0 }}
                            animate={{ width: `${result.company_trust.trust_score * 100}%` }}
                          />
                        </div>
                        <p className="text-xs text-center" style={{ color: colors.text.tertiary }}>
                          Click for details
                        </p>
                      </Card>
                    </motion.div>
                  )}
                  {result.product_trust && (
                    <motion.div
                      onClick={() => setExpandedCard(expandedCard === 'product' ? null : 'product')}
                      className="cursor-pointer"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Card padding="md" hover>
                        <h3 className="text-sm font-semibold mb-2" style={{ color: colors.text.secondary }}>
                          Product Reliability
                        </h3>
                        <p className="text-2xl font-bold mb-2" style={{ color: colors.text.primary }}>
                          {(result.product_trust.trust_score * 100).toFixed(0)}%
                        </p>
                        <div
                          className="h-2 rounded-full overflow-hidden mb-2"
                          style={{ backgroundColor: colors.border.default }}
                        >
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.warning }}
                            initial={{ width: 0 }}
                            animate={{ width: `${result.product_trust.trust_score * 100}%` }}
                          />
                        </div>
                        <p className="text-xs text-center" style={{ color: colors.text.tertiary }}>
                          Click for details
                        </p>
                      </Card>
                    </motion.div>
                  )}
                </div>
              )}

              {/* Expanded Details */}
              <AnimatePresence>
                {expandedCard === 'influencer' && result.influencer_trust && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <Card padding="lg">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-xl font-bold" style={{ color: colors.text.primary }}>
                          Influencer Analysis: {result.influencer_trust.stats.handle}
                        </h3>
                        <button
                          onClick={() => setExpandedCard(null)}
                          className="text-2xl hover:opacity-70 transition-opacity"
                          style={{ color: colors.text.tertiary }}
                        >
                          ×
                        </button>
                      </div>

                      {/* Influencer Stats */}
                      {result.influencer_trust.stats && (
                        <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: colors.background.secondary }}>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {result.influencer_trust.stats.followers !== null && (
                              <div>
                                <p className="text-xs" style={{ color: colors.text.tertiary }}>Followers</p>
                                <p className="text-lg font-bold" style={{ color: colors.text.primary }}>
                                  {result.influencer_trust.stats.followers?.toLocaleString()}
                                </p>
                              </div>
                            )}
                            {result.influencer_trust.stats.following !== null && (
                              <div>
                                <p className="text-xs" style={{ color: colors.text.tertiary }}>Following</p>
                                <p className="text-lg font-bold" style={{ color: colors.text.primary }}>
                                  {result.influencer_trust.stats.following?.toLocaleString()}
                                </p>
                              </div>
                            )}
                            {result.influencer_trust.stats.posts_count !== null && (
                              <div>
                                <p className="text-xs" style={{ color: colors.text.tertiary }}>Posts</p>
                                <p className="text-lg font-bold" style={{ color: colors.text.primary }}>
                                  {result.influencer_trust.stats.posts_count?.toLocaleString()}
                                </p>
                              </div>
                            )}
                            {result.influencer_trust.stats.is_verified !== null && (
                              <div>
                                <p className="text-xs" style={{ color: colors.text.tertiary }}>Verified</p>
                                <p className="text-lg font-bold" style={{ color: colors.text.primary }}>
                                  {result.influencer_trust.stats.is_verified ? '✓ Yes' : '✗ No'}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Score Breakdown */}
                      <div className="space-y-3 mb-6">
                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: colors.text.secondary }}>Message History</span>
                            <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                              {(result.influencer_trust.message_history_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ backgroundColor: colors.accent.info }}
                              initial={{ width: 0 }}
                              animate={{ width: `${result.influencer_trust.message_history_score * 100}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: colors.text.secondary }}>Followers Score</span>
                            <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                              {(result.influencer_trust.followers_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ backgroundColor: colors.accent.info }}
                              initial={{ width: 0 }}
                              animate={{ width: `${result.influencer_trust.followers_score * 100}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: colors.text.secondary }}>Web Reputation</span>
                            <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                              {(result.influencer_trust.web_reputation_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ backgroundColor: colors.accent.info }}
                              initial={{ width: 0 }}
                              animate={{ width: `${result.influencer_trust.web_reputation_score * 100}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm" style={{ color: colors.text.secondary }}>Disclosure Score</span>
                            <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                              {(result.influencer_trust.disclosure_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                            <motion.div
                              className="h-full rounded-full"
                              style={{ backgroundColor: colors.accent.info }}
                              initial={{ width: 0 }}
                              animate={{ width: `${result.influencer_trust.disclosure_score * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Notes */}
                      {result.influencer_trust.notes && (
                        <div
                          className="p-4 rounded-xl"
                          style={{
                            backgroundColor: colors.background.secondary,
                            border: `1px solid ${colors.border.default}`,
                          }}
                        >
                          <h4 className="font-semibold mb-2" style={{ color: colors.text.secondary }}>
                            Analysis Notes
                          </h4>
                          <p style={{ color: colors.text.primary }}>{result.influencer_trust.notes}</p>
                        </div>
                      )}
                    </Card>
                  </motion.div>
                )}

                {expandedCard === 'company' && result.company_trust && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <Card padding="lg">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-xl font-bold" style={{ color: colors.text.primary }}>
                          Company Analysis: {result.company_trust.name}
                        </h3>
                        <button
                          onClick={() => setExpandedCard(null)}
                          className="text-2xl hover:opacity-70 transition-opacity"
                          style={{ color: colors.text.tertiary }}
                        >
                          ×
                        </button>
                      </div>

                      {/* Summary */}
                      <div
                        className="p-4 rounded-xl mb-4"
                        style={{
                          backgroundColor: colors.background.secondary,
                          border: `1px solid ${colors.border.default}`,
                        }}
                      >
                        <h4 className="font-semibold mb-2" style={{ color: colors.text.secondary }}>Summary</h4>
                        <p style={{ color: colors.text.primary }}>{result.company_trust.summary}</p>
                      </div>

                      {/* Issues */}
                      {result.company_trust.issues && result.company_trust.issues.length > 0 && (
                        <div
                          className="p-4 rounded-xl"
                          style={{
                            backgroundColor: colors.background.secondary,
                            border: `1px solid ${colors.border.default}`,
                          }}
                        >
                          <h4 className="font-semibold mb-3" style={{ color: colors.text.secondary }}>
                            Identified Issues
                          </h4>
                          <ul className="space-y-2">
                            {result.company_trust.issues.map((issue, idx) => (
                              <li key={idx} className="flex gap-2">
                                <span style={{ color: colors.accent.warning }}>•</span>
                                <span style={{ color: colors.text.primary }}>{issue}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Card>
                  </motion.div>
                )}

                {expandedCard === 'product' && result.product_trust && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                  >
                    <Card padding="lg">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-xl font-bold" style={{ color: colors.text.primary }}>
                          Product Analysis: {result.product_trust.name}
                        </h3>
                        <button
                          onClick={() => setExpandedCard(null)}
                          className="text-2xl hover:opacity-70 transition-opacity"
                          style={{ color: colors.text.tertiary }}
                        >
                          ×
                        </button>
                      </div>

                      {/* Summary */}
                      <div
                        className="p-4 rounded-xl mb-4"
                        style={{
                          backgroundColor: colors.background.secondary,
                          border: `1px solid ${colors.border.default}`,
                        }}
                      >
                        <h4 className="font-semibold mb-2" style={{ color: colors.text.secondary }}>Summary</h4>
                        <p style={{ color: colors.text.primary }}>{result.product_trust.summary}</p>
                      </div>

                      {/* Issues */}
                      {result.product_trust.issues && result.product_trust.issues.length > 0 && (
                        <div
                          className="p-4 rounded-xl"
                          style={{
                            backgroundColor: colors.background.secondary,
                            border: `1px solid ${colors.border.default}`,
                          }}
                        >
                          <h4 className="font-semibold mb-3" style={{ color: colors.text.secondary }}>
                            Identified Issues
                          </h4>
                          <ul className="space-y-2">
                            {result.product_trust.issues.map((issue, idx) => (
                              <li key={idx} className="flex gap-2">
                                <span style={{ color: colors.accent.warning }}>•</span>
                                <span style={{ color: colors.text.primary }}>{issue}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Card>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Final Summary */}
              {result.final_summary && (
                <Card padding="lg">
                  <h3 className="text-lg font-bold mb-3" style={{ color: colors.text.primary }}>
                    Summary
                  </h3>
                  <p style={{ color: colors.text.secondary }}>{result.final_summary}</p>
                </Card>
              )}

              {/* Feedback Form */}
              <FeedbackForm
                analysisType="full"
                analyzedEntity={
                  result.influencer_trust?.stats?.handle ||
                  result.source_details?.inferred_company_name ||
                  result.source_details?.inferred_product_name
                }
                onSubmitSuccess={() => {
                  console.log('Feedback submitted successfully');
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Disclaimer */}
        <motion.p
          variants={animations.fadeIn}
          className="text-xs text-center mt-8"
          style={{ color: colors.text.tertiary }}
        >
          This analysis is provided for informational purposes only. Always use your own judgment when evaluating
          messages and offers. Results are based on AI analysis and may not be 100% accurate.
        </motion.p>
      </motion.div>
    </div>
  );
}
