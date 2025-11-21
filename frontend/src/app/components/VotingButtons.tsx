'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors } from '../lib/theme';

interface VoteStats {
  trust_votes: number;
  distrust_votes: number;
  total_votes: number;
  user_trust_score: number;
}

interface VotingButtonsProps {
  handle: string;
  platform: string;
  className?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export function VotingButtons({ handle, platform, className = '' }: VotingButtonsProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const [userVote, setUserVote] = useState<'trust' | 'distrust' | null>(null);
  const [voteStats, setVoteStats] = useState<VoteStats>({
    trust_votes: 0,
    distrust_votes: 0,
    total_votes: 0,
    user_trust_score: 0.50,
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // Fetch initial vote status
  useEffect(() => {
    fetchVoteStatus();
  }, [handle, platform]);

  const fetchVoteStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/votes/influencers/${handle}?platform=${platform}`);

      if (response.ok) {
        const data = await response.json();
        setUserVote(data.user_vote);
        setVoteStats(data.vote_stats);
      }
    } catch (err) {
      console.error('Failed to fetch vote status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (voteType: 'trust' | 'distrust') => {
    // If clicking the same vote, remove it
    if (userVote === voteType) {
      await removeVote();
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/votes/influencers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          handle,
          platform,
          vote_type: voteType,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        if (response.status === 429) {
          throw new Error('You have exceeded the voting rate limit (20 votes per hour). Please try again later.');
        }
        throw new Error(data.detail || 'Failed to submit vote');
      }

      const data = await response.json();
      setUserVote(voteType);
      setVoteStats(data.vote_stats);

      // Show success message briefly
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const removeVote = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/votes/influencers/${handle}?platform=${platform}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove vote');
      }

      setUserVote(null);
      // Refresh stats
      await fetchVoteStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const getTrustScoreColor = (score: number) => {
    if (score >= 0.75) return colors.accent.success;
    if (score >= 0.5) return colors.accent.warning;
    return colors.accent.danger;
  };

  if (loading) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin"
          style={{ borderColor: `${colors.accent.primary} transparent transparent transparent` }}
        />
        <span className="text-sm" style={{ color: colors.text.secondary }}>Loading...</span>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Voting Buttons */}
      <div className="flex gap-2 mb-2">
        <button
          onClick={() => handleVote('trust')}
          disabled={submitting}
          className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50"
          style={{
            backgroundColor: userVote === 'trust' ? colors.accent.success : colors.background.secondary,
            color: userVote === 'trust' ? 'white' : colors.text.primary,
            border: `2px solid ${userVote === 'trust' ? colors.accent.success : colors.border.default}`,
          }}
        >
          <span className="text-lg">👍</span>
          <span>Trust</span>
          <span className="text-sm opacity-75">({voteStats.trust_votes})</span>
        </button>

        <button
          onClick={() => handleVote('distrust')}
          disabled={submitting}
          className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all disabled:opacity-50"
          style={{
            backgroundColor: userVote === 'distrust' ? colors.accent.danger : colors.background.secondary,
            color: userVote === 'distrust' ? 'white' : colors.text.primary,
            border: `2px solid ${userVote === 'distrust' ? colors.accent.danger : colors.border.default}`,
          }}
        >
          <span className="text-lg">👎</span>
          <span>Distrust</span>
          <span className="text-sm opacity-75">({voteStats.distrust_votes})</span>
        </button>
      </div>

      {/* Vote Statistics */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm" style={{ color: colors.text.secondary }}>
            Community Score:
          </span>
          <span
            className="text-sm font-bold"
            style={{ color: getTrustScoreColor(voteStats.user_trust_score) }}
          >
            {(voteStats.user_trust_score * 100).toFixed(0)}%
          </span>
        </div>
        <span className="text-xs" style={{ color: colors.text.tertiary }}>
          ({voteStats.total_votes} vote{voteStats.total_votes !== 1 ? 's' : ''})
        </span>
      </div>

      {/* User's Vote Indicator */}
      {userVote && (
        <p className="text-xs mt-1" style={{ color: colors.text.tertiary }}>
          You voted: {userVote === 'trust' ? '👍 Trust' : '👎 Distrust'}
          <button
            onClick={removeVote}
            disabled={submitting}
            className="ml-2 underline hover:no-underline"
          >
            (remove vote)
          </button>
        </p>
      )}

      {/* Success Message */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-2 p-2 rounded-lg text-sm flex items-center gap-2"
            style={{
              backgroundColor: colors.accent.success + '20',
              color: colors.accent.success,
            }}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Vote recorded! Thank you for your feedback.
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 p-2 rounded-lg text-sm flex items-start gap-2"
          style={{
            backgroundColor: colors.accent.danger + '20',
            color: colors.accent.danger,
          }}
        >
          <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </motion.div>
      )}
    </div>
  );
}
