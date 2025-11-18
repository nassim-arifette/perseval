'use client';

import { useState } from 'react';
import { Button } from './ui/Button';
import { Textarea } from './ui/Textarea';
import { Input } from './ui/Input';

interface FeedbackFormProps {
  analysisType: 'full' | 'influencer' | 'company' | 'product' | 'text';
  analyzedEntity?: string;
  onSubmitSuccess?: () => void;
}

type ExperienceRating = 'good' | 'medium' | 'bad';

export default function FeedbackForm({
  analysisType,
  analyzedEntity,
  onSubmitSuccess,
}: FeedbackFormProps) {
  const [experienceRating, setExperienceRating] = useState<ExperienceRating | null>(null);
  const [reviewText, setReviewText] = useState('');
  const [email, setEmail] = useState('');
  const [emailConsented, setEmailConsented] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  // Generate a session ID and store in localStorage
  const getSessionId = () => {
    let sessionId = localStorage.getItem('perseval-session-id');
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('perseval-session-id', sessionId);
    }
    return sessionId;
  };

  const handleSubmit = async () => {
    // Validation
    if (!experienceRating) {
      setError('Please select your experience rating');
      return;
    }

    if (reviewText.length > 1000) {
      setError('Review text must be less than 1000 characters');
      return;
    }

    if (email && emailConsented && !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': getSessionId(),
        },
        body: JSON.stringify({
          analysis_type: analysisType,
          analyzed_entity: analyzedEntity,
          experience_rating: experienceRating,
          review_text: reviewText || undefined,
          email: email || undefined,
          email_consented: emailConsented && email ? true : false,
        }),
      });

      if (response.status === 429) {
        throw new Error('Too many feedback submissions. Please try again later.');
      }

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      const data = await response.json();
      setIsSubmitted(true);

      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-6 dark:border-green-800 dark:bg-green-950">
        <div className="flex items-center gap-3">
          <svg
            className="h-6 w-6 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <div>
            <h3 className="font-semibold text-green-900 dark:text-green-100">
              Thank you for your feedback!
            </h3>
            {emailConsented && email && (
              <p className="mt-1 text-sm text-green-700 dark:text-green-300">
                You've been subscribed to our newsletter at {email}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
        How was your experience?
      </h3>

      {/* Three Emoji Rating Buttons */}
      <div className="mb-6">
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setExperienceRating('good')}
            className={`flex flex-col items-center gap-2 rounded-xl p-6 transition-all ${
              experienceRating === 'good'
                ? 'bg-green-100 ring-2 ring-green-500 dark:bg-green-900/30 dark:ring-green-400'
                : 'bg-gray-50 hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600'
            }`}
          >
            <span className="text-5xl">😊</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Good</span>
          </button>

          <button
            onClick={() => setExperienceRating('medium')}
            className={`flex flex-col items-center gap-2 rounded-xl p-6 transition-all ${
              experienceRating === 'medium'
                ? 'bg-yellow-100 ring-2 ring-yellow-500 dark:bg-yellow-900/30 dark:ring-yellow-400'
                : 'bg-gray-50 hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600'
            }`}
          >
            <span className="text-5xl">😐</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Medium</span>
          </button>

          <button
            onClick={() => setExperienceRating('bad')}
            className={`flex flex-col items-center gap-2 rounded-xl p-6 transition-all ${
              experienceRating === 'bad'
                ? 'bg-red-100 ring-2 ring-red-500 dark:bg-red-900/30 dark:ring-red-400'
                : 'bg-gray-50 hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600'
            }`}
          >
            <span className="text-5xl">😞</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Bad</span>
          </button>
        </div>
      </div>

      {/* Review Text */}
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Share your thoughts (optional)
        </label>
        <Textarea
          value={reviewText}
          onChange={(e) => setReviewText(e.target.value)}
          placeholder="Tell us more about your experience..."
          maxLength={1000}
          rows={4}
          className="w-full"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          {reviewText.length}/1000 characters
        </p>
      </div>

      {/* Email Newsletter */}
      <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-950/50">
        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-blue-900 dark:text-blue-100">
          <span>📧</span>
          <span>Get updates and news</span>
        </label>
        <Input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="your@email.com"
          className="mb-3"
        />
        <label className="flex items-start gap-2 text-sm text-blue-800 dark:text-blue-200">
          <input
            type="checkbox"
            checked={emailConsented}
            onChange={(e) => setEmailConsented(e.target.checked)}
            className="mt-0.5 rounded"
          />
          <span>I consent to receive emails about Perseval updates and news</span>
        </label>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
          {error}
        </div>
      )}

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || !experienceRating}
        className="w-full"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
      </Button>
    </div>
  );
}
