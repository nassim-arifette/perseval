'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors } from '../lib/theme';
import { Input } from './ui/Input';
import { Button } from './ui/Button';

interface SubmitInfluencerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export function SubmitInfluencerModal({ isOpen, onClose, onSuccess }: SubmitInfluencerModalProps) {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const [handle, setHandle] = useState('');
  const [platform, setPlatform] = useState<'instagram' | 'tiktok' | 'youtube'>('instagram');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submissionId, setSubmissionId] = useState<string | null>(null);

  // Validation states
  const [handleError, setHandleError] = useState<string>('');

  const validateHandle = (value: string): boolean => {
    if (!value.trim()) {
      setHandleError('Handle is required');
      return false;
    }
    if (value.length > 100) {
      setHandleError('Handle is too long (max 100 characters)');
      return false;
    }
    setHandleError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate
    if (!validateHandle(handle)) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/submissions/influencers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          handle: handle.trim(),
          platform,
          reason: reason.trim() || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();

        if (response.status === 429) {
          throw new Error('You have reached the maximum number of submissions (3 per day). Please try again tomorrow.');
        } else if (response.status === 409) {
          throw new Error('This influencer has already been submitted recently. Please check back later.');
        } else if (response.status === 503) {
          throw new Error('Submission system is temporarily unavailable. Please try again later.');
        } else {
          throw new Error(data.detail || 'Failed to submit influencer');
        }
      }

      const data = await response.json();
      setSubmissionId(data.id);
      setSuccess(true);

      // Call onSuccess callback after a delay
      setTimeout(() => {
        if (onSuccess) onSuccess();
        handleClose();
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form
    setHandle('');
    setPlatform('instagram');
    setReason('');
    setError(null);
    setSuccess(false);
    setSubmissionId(null);
    setHandleError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={handleClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden"
          style={{ backgroundColor: colors.background.card }}
        >
          {/* Header */}
          <div className="p-6 border-b" style={{ borderColor: colors.border.default }}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold" style={{ color: colors.text.primary }}>
                  Submit an Influencer
                </h2>
                <p className="text-sm mt-1" style={{ color: colors.text.secondary }}>
                  Suggest an influencer for marketplace review
                </p>
              </div>
              <button
                onClick={handleClose}
                className="p-2 rounded-lg hover:bg-opacity-10 transition-all"
                style={{ backgroundColor: colors.border.default }}
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-6">
            {success ? (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: colors.accent.success + '20' }}
                >
                  <svg className="w-8 h-8" style={{ color: colors.accent.success }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-2" style={{ color: colors.text.primary }}>
                  Submission Received!
                </h3>
                <p className="text-sm mb-4" style={{ color: colors.text.secondary }}>
                  Thank you for suggesting @{handle}. We'll analyze them and add to the marketplace if approved.
                </p>
                <p className="text-xs" style={{ color: colors.text.tertiary }}>
                  Submission ID: {submissionId?.slice(0, 8)}...
                </p>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Handle Input */}
                <Input
                  label="Influencer Handle *"
                  placeholder="username (with or without @)"
                  value={handle}
                  onChange={(e) => {
                    setHandle(e.target.value);
                    validateHandle(e.target.value);
                  }}
                  onBlur={(e) => validateHandle(e.target.value)}
                  error={handleError}
                  helperText="Enter the influencer's username or handle"
                  required
                />

                {/* Platform Select */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
                    Platform *
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['instagram', 'tiktok', 'youtube'] as const).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPlatform(p)}
                        className="px-4 py-2.5 rounded-xl font-medium transition-all capitalize"
                        style={{
                          backgroundColor: platform === p ? colors.accent.info : colors.background.secondary,
                          color: platform === p ? 'white' : colors.text.primary,
                          border: `2px solid ${platform === p ? colors.accent.info : colors.border.default}`,
                        }}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Reason Textarea */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
                    Why should we add this influencer? (Optional)
                  </label>
                  <textarea
                    placeholder="Tell us why this influencer would be valuable to the marketplace..."
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    maxLength={500}
                    rows={4}
                    className="w-full px-4 py-2.5 rounded-xl resize-none"
                    style={{
                      backgroundColor: colors.background.card,
                      color: colors.text.primary,
                      border: `2px solid ${colors.border.default}`,
                    }}
                  />
                  <p className="text-xs mt-1" style={{ color: colors.text.tertiary }}>
                    {reason.length}/500 characters
                  </p>
                </div>

                {/* Info Box */}
                <div className="p-4 rounded-xl" style={{ backgroundColor: colors.accent.info + '10', borderLeft: `4px solid ${colors.accent.info}` }}>
                  <p className="text-sm" style={{ color: colors.text.secondary }}>
                    <strong>Note:</strong> Submissions are limited to 3 per day. We'll analyze the influencer using AI and add them to the marketplace if approved.
                  </p>
                </div>

                {/* Error Message */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-xl flex items-start gap-2"
                    style={{ backgroundColor: colors.accent.danger + '10', borderLeft: `4px solid ${colors.accent.danger}` }}
                  >
                    <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: colors.accent.danger }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm" style={{ color: colors.accent.danger }}>{error}</p>
                  </motion.div>
                )}

                {/* Submit Button */}
                <div className="flex gap-3 pt-2">
                  <Button
                    type="button"
                    onClick={handleClose}
                    disabled={isSubmitting}
                    variant="secondary"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    disabled={isSubmitting || !handle.trim()}
                    variant="primary"
                    className="flex-1"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Submitting...
                      </span>
                    ) : (
                      'Submit for Review'
                    )}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
