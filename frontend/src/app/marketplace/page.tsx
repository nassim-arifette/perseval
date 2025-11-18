'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, theme, animations } from '../lib/theme';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import type { MarketplaceInfluencer } from '../lib/types';

const API_BASE = '/api';

export default function MarketplacePage() {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);

  const [influencers, setInfluencers] = useState<MarketplaceInfluencer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [trustFilter, setTrustFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [sortBy, setSortBy] = useState<'trust_score' | 'followers' | 'last_analyzed'>('trust_score');
  const [selectedInfluencer, setSelectedInfluencer] = useState<MarketplaceInfluencer | null>(null);

  useEffect(() => {
    fetchInfluencers();
  }, [searchTerm, trustFilter, sortBy]);

  const fetchInfluencers = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        sort_by: sortBy,
        sort_order: 'desc',
        limit: '50',
      });

      if (searchTerm) params.append('search', searchTerm);
      if (trustFilter !== 'all') params.append('trust_level', trustFilter);

      const response = await fetch(`${API_BASE}/marketplace/influencers?${params}`);

      if (!response.ok) {
        if (response.status === 503) {
          throw new Error('Marketplace is not available. Supabase configuration required.');
        }
        throw new Error('Failed to fetch marketplace data');
      }

      const data = await response.json();
      setInfluencers(data.influencers || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setInfluencers([]);
    } finally {
      setLoading(false);
    }
  };

  const getTrustColor = (label: string) => {
    switch (label) {
      case 'high':
        return colors.accent.success;
      case 'medium':
        return colors.accent.warning;
      case 'low':
        return colors.accent.danger;
      default:
        return colors.accent.info;
    }
  };

  const getTrustIcon = (label: string) => {
    switch (label) {
      case 'high':
        return '✓';
      case 'medium':
        return '~';
      case 'low':
        return '!';
      default:
        return '?';
    }
  };

  const formatNumber = (num: number | null | undefined) => {
    if (!num) return 'N/A';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
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
        className="max-w-7xl mx-auto"
      >
        {/* Header */}
        <motion.div variants={animations.slideUp} className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            Influencer Marketplace
          </h1>
          <p style={{ color: colors.text.secondary }}>
            Discover vetted influencers with verified trust scores
          </p>
        </motion.div>

        {/* Filters and Search */}
        <motion.div variants={animations.slideUp} className="mb-6">
          <Card padding="lg">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <Input
                  placeholder="Search by handle or name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                      <path fillRule="evenodd" d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z" clipRule="evenodd" />
                    </svg>
                  }
                />
              </div>

              {/* Trust Filter */}
              <div>
                <select
                  value={trustFilter}
                  onChange={(e) => setTrustFilter(e.target.value as any)}
                  className="w-full px-4 py-3 rounded-xl border outline-none transition-all"
                  style={{
                    backgroundColor: colors.background.input,
                    borderColor: colors.border.default,
                    color: colors.text.primary,
                  }}
                >
                  <option value="all">All Trust Levels</option>
                  <option value="high">High Trust</option>
                  <option value="medium">Medium Trust</option>
                  <option value="low">Low Trust</option>
                </select>
              </div>

              {/* Sort By */}
              <div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full px-4 py-3 rounded-xl border outline-none transition-all"
                  style={{
                    backgroundColor: colors.background.input,
                    borderColor: colors.border.default,
                    color: colors.text.primary,
                  }}
                >
                  <option value="trust_score">Sort by Trust</option>
                  <option value="followers">Sort by Followers</option>
                  <option value="last_analyzed">Sort by Recent</option>
                </select>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="inline-block w-12 h-12 border-4 border-t-transparent rounded-full"
              style={{ borderColor: `${colors.accent.primary} transparent transparent transparent` }}
            />
            <p className="mt-4" style={{ color: colors.text.secondary }}>
              Loading marketplace...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <Card padding="lg">
            <div className="text-center py-12">
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl"
                style={{ backgroundColor: `${colors.accent.danger}20` }}
              >
                ⚠️
              </div>
              <h3 className="text-xl font-bold mb-2" style={{ color: colors.text.primary }}>
                {error}
              </h3>
              <p style={{ color: colors.text.secondary }} className="mb-4">
                The marketplace requires Supabase to be configured. Check the README for setup instructions.
              </p>
              <Button onClick={fetchInfluencers}>Try Again</Button>
            </div>
          </Card>
        )}

        {/* Influencer Grid */}
        {!loading && !error && (
          <AnimatePresence mode="wait">
            {influencers.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Card padding="lg">
                  <div className="text-center py-12">
                    <div
                      className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl"
                      style={{ backgroundColor: `${colors.accent.info}20` }}
                    >
                      🔍
                    </div>
                    <h3 className="text-xl font-bold mb-2" style={{ color: colors.text.primary }}>
                      No Influencers Found
                    </h3>
                    <p style={{ color: colors.text.secondary }}>
                      {searchTerm || trustFilter !== 'all'
                        ? 'Try adjusting your filters'
                        : 'The marketplace is empty. Add influencers to get started.'}
                    </p>
                  </div>
                </Card>
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {influencers.map((influencer, index) => (
                  <motion.div
                    key={influencer.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.3 }}
                    whileHover={{ y: -4 }}
                    onClick={() => setSelectedInfluencer(influencer)}
                    className="cursor-pointer"
                  >
                    <Card padding="lg" hover>
                      {/* Featured Badge */}
                      {influencer.is_featured && (
                        <div className="absolute top-4 right-4">
                          <div
                            className="px-3 py-1 rounded-full text-xs font-bold"
                            style={{
                              background: theme.gradients.primary,
                              color: 'white',
                            }}
                          >
                            ⭐ Featured
                          </div>
                        </div>
                      )}

                      {/* Trust Badge */}
                      <div className="flex items-start gap-4 mb-4">
                        <div
                          className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold"
                          style={{
                            background: `linear-gradient(135deg, ${getTrustColor(influencer.trust_label)}20, ${getTrustColor(influencer.trust_label)}40)`,
                            color: getTrustColor(influencer.trust_label),
                            border: `2px solid ${getTrustColor(influencer.trust_label)}`,
                          }}
                        >
                          {getTrustIcon(influencer.trust_label)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-bold" style={{ color: colors.text.primary }}>
                              @{influencer.handle}
                            </h3>
                            {influencer.is_verified && (
                              <svg className="w-5 h-5" viewBox="0 0 20 20" fill={colors.accent.info}>
                                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                          {influencer.display_name && (
                            <p className="text-sm" style={{ color: colors.text.secondary }}>
                              {influencer.display_name}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Bio */}
                      {influencer.bio && (
                        <p
                          className="text-sm mb-4 line-clamp-2"
                          style={{ color: colors.text.secondary }}
                        >
                          {influencer.bio}
                        </p>
                      )}

                      {/* Stats */}
                      <div className="grid grid-cols-3 gap-2 mb-4">
                        <div className="text-center p-2 rounded-lg" style={{ backgroundColor: colors.background.hover }}>
                          <p className="text-xs" style={{ color: colors.text.tertiary }}>
                            Followers
                          </p>
                          <p className="font-bold" style={{ color: colors.text.primary }}>
                            {formatNumber(influencer.followers_count)}
                          </p>
                        </div>
                        <div className="text-center p-2 rounded-lg" style={{ backgroundColor: colors.background.hover }}>
                          <p className="text-xs" style={{ color: colors.text.tertiary }}>
                            Posts
                          </p>
                          <p className="font-bold" style={{ color: colors.text.primary }}>
                            {formatNumber(influencer.posts_count)}
                          </p>
                        </div>
                        <div className="text-center p-2 rounded-lg" style={{ backgroundColor: colors.background.hover }}>
                          <p className="text-xs" style={{ color: colors.text.tertiary }}>
                            Trust
                          </p>
                          <p className="font-bold" style={{ color: getTrustColor(influencer.trust_label) }}>
                            {(influencer.overall_trust_score * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>

                      {/* Trust Label */}
                      <div
                        className="w-full py-2 rounded-lg text-center font-semibold text-sm capitalize"
                        style={{
                          backgroundColor: `${getTrustColor(influencer.trust_label)}15`,
                          color: getTrustColor(influencer.trust_label),
                        }}
                      >
                        {influencer.trust_label} Trust
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </AnimatePresence>
        )}
      </motion.div>

      {/* Influencer Detail Modal */}
      <AnimatePresence>
        {selectedInfluencer && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.6)' }}
            onClick={() => setSelectedInfluencer(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="max-w-3xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <Card padding="lg">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-4">
                    <div
                      className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold"
                      style={{
                        background: `linear-gradient(135deg, ${getTrustColor(selectedInfluencer.trust_label)}20, ${getTrustColor(selectedInfluencer.trust_label)}40)`,
                        color: getTrustColor(selectedInfluencer.trust_label),
                        border: `3px solid ${getTrustColor(selectedInfluencer.trust_label)}`,
                      }}
                    >
                      {getTrustIcon(selectedInfluencer.trust_label)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h2 className="text-2xl font-bold" style={{ color: colors.text.primary }}>
                          @{selectedInfluencer.handle}
                        </h2>
                        {selectedInfluencer.is_verified && (
                          <svg className="w-6 h-6" viewBox="0 0 20 20" fill={colors.accent.info}>
                            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      {selectedInfluencer.display_name && (
                        <p style={{ color: colors.text.secondary }}>
                          {selectedInfluencer.display_name}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedInfluencer(null)}
                    className="text-3xl hover:opacity-70 transition-opacity"
                    style={{ color: colors.text.tertiary }}
                  >
                    ×
                  </button>
                </div>

                {/* Bio */}
                {selectedInfluencer.bio && (
                  <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: colors.background.secondary }}>
                    <p style={{ color: colors.text.primary }}>{selectedInfluencer.bio}</p>
                  </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 rounded-xl" style={{ backgroundColor: colors.background.hover }}>
                    <p className="text-sm mb-1" style={{ color: colors.text.tertiary }}>
                      Followers
                    </p>
                    <p className="text-2xl font-bold" style={{ color: colors.text.primary }}>
                      {formatNumber(selectedInfluencer.followers_count)}
                    </p>
                  </div>
                  <div className="text-center p-4 rounded-xl" style={{ backgroundColor: colors.background.hover }}>
                    <p className="text-sm mb-1" style={{ color: colors.text.tertiary }}>
                      Following
                    </p>
                    <p className="text-2xl font-bold" style={{ color: colors.text.primary }}>
                      {formatNumber(selectedInfluencer.following_count)}
                    </p>
                  </div>
                  <div className="text-center p-4 rounded-xl" style={{ backgroundColor: colors.background.hover }}>
                    <p className="text-sm mb-1" style={{ color: colors.text.tertiary }}>
                      Posts
                    </p>
                    <p className="text-2xl font-bold" style={{ color: colors.text.primary }}>
                      {formatNumber(selectedInfluencer.posts_count)}
                    </p>
                  </div>
                  <div className="text-center p-4 rounded-xl" style={{ backgroundColor: colors.background.hover }}>
                    <p className="text-sm mb-1" style={{ color: colors.text.tertiary }}>
                      Overall Trust
                    </p>
                    <p className="text-2xl font-bold" style={{ color: getTrustColor(selectedInfluencer.trust_label) }}>
                      {(selectedInfluencer.overall_trust_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Trust Breakdown */}
                <div className="mb-6">
                  <h3 className="text-lg font-bold mb-4" style={{ color: colors.text.primary }}>
                    Trust Score Breakdown
                  </h3>
                  <div className="space-y-3">
                    {selectedInfluencer.message_history_score !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm" style={{ color: colors.text.secondary }}>Message History</span>
                          <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                            {(selectedInfluencer.message_history_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.info }}
                            initial={{ width: 0 }}
                            animate={{ width: `${selectedInfluencer.message_history_score * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {selectedInfluencer.followers_score !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm" style={{ color: colors.text.secondary }}>Followers Score</span>
                          <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                            {(selectedInfluencer.followers_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.info }}
                            initial={{ width: 0 }}
                            animate={{ width: `${selectedInfluencer.followers_score * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {selectedInfluencer.web_reputation_score !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm" style={{ color: colors.text.secondary }}>Web Reputation</span>
                          <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                            {(selectedInfluencer.web_reputation_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.info }}
                            initial={{ width: 0 }}
                            animate={{ width: `${selectedInfluencer.web_reputation_score * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {selectedInfluencer.disclosure_score !== null && (
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm" style={{ color: colors.text.secondary }}>Disclosure Score</span>
                          <span className="text-sm font-bold" style={{ color: colors.text.primary }}>
                            {(selectedInfluencer.disclosure_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full" style={{ backgroundColor: colors.border.default }}>
                          <motion.div
                            className="h-full rounded-full"
                            style={{ backgroundColor: colors.accent.info }}
                            initial={{ width: 0 }}
                            animate={{ width: `${selectedInfluencer.disclosure_score * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Analysis Summary */}
                {selectedInfluencer.analysis_summary && (
                  <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: colors.background.secondary, border: `1px solid ${colors.border.default}` }}>
                    <h4 className="font-semibold mb-2" style={{ color: colors.text.secondary }}>
                      Analysis Summary
                    </h4>
                    <p style={{ color: colors.text.primary }}>{selectedInfluencer.analysis_summary}</p>
                  </div>
                )}

                {/* Issues */}
                {selectedInfluencer.issues && selectedInfluencer.issues.length > 0 && (
                  <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: colors.background.secondary, border: `1px solid ${colors.border.default}` }}>
                    <h4 className="font-semibold mb-3" style={{ color: colors.text.secondary }}>
                      Identified Issues
                    </h4>
                    <ul className="space-y-2">
                      {selectedInfluencer.issues.map((issue, idx) => (
                        <li key={idx} className="flex gap-2">
                          <span style={{ color: colors.accent.warning }}>•</span>
                          <span style={{ color: colors.text.primary }}>{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Footer Info */}
                <div className="flex justify-between items-center text-sm" style={{ color: colors.text.tertiary }}>
                  <span>
                    Last analyzed: {new Date(selectedInfluencer.last_analyzed_at).toLocaleDateString()}
                  </span>
                  {selectedInfluencer.profile_url && (
                    <a
                      href={selectedInfluencer.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline"
                      style={{ color: colors.accent.primary }}
                    >
                      View Profile →
                    </a>
                  )}
                </div>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
