'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../context/ThemeContext';
import { getThemeColors, animations } from '../../lib/theme';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

interface InfluencerSubmission {
  id: string;
  handle: string;
  platform: string;
  reason?: string;
  status: 'pending' | 'analyzing' | 'approved' | 'rejected';
  trust_score?: number;
  analysis_data?: any;
  analysis_completed_at?: string;
  analysis_error?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  admin_notes?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export default function AdminSubmissionsPage() {
  const { theme } = useTheme();
  const colors = getThemeColors(theme);

  const [submissions, setSubmissions] = useState<InfluencerSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [apiKey, setApiKey] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<InfluencerSubmission | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Check for API key in localStorage
    const storedKey = localStorage.getItem('admin_api_key');
    if (storedKey) {
      setApiKey(storedKey);
      setIsAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchSubmissions();
    }
  }, [isAuthenticated, statusFilter]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey.trim()) {
      localStorage.setItem('admin_api_key', apiKey);
      setIsAuthenticated(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_api_key');
    setApiKey('');
    setIsAuthenticated(false);
  };

  const fetchSubmissions = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: '50',
      });

      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      const response = await fetch(`${API_BASE}/admin/submissions/influencers?${params}`, {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error('Invalid API key. Please check your credentials.');
        }
        throw new Error('Failed to fetch submissions');
      }

      const data = await response.json();
      setSubmissions(data.submissions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  const analyzeSubmission = async (submissionId: string) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/submissions/influencers/${submissionId}/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to analyze submission');
      }

      // Refresh submissions
      await fetchSubmissions();
      alert('Analysis completed successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const reviewSubmission = async (submissionId: string, status: 'approved' | 'rejected') => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/admin/submissions/influencers/${submissionId}/review`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status,
          admin_notes: reviewNotes || undefined,
          rejection_reason: status === 'rejected' ? rejectionReason : undefined,
          add_to_marketplace: status === 'approved',
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to review submission');
      }

      // Reset form and close modal
      setSelectedSubmission(null);
      setReviewNotes('');
      setRejectionReason('');

      // Refresh submissions
      await fetchSubmissions();
      alert(`Submission ${status} successfully!`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return colors.accent.success;
      case 'rejected':
        return colors.accent.danger;
      case 'analyzing':
        return colors.accent.info;
      default:
        return colors.accent.warning;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return '✓';
      case 'rejected':
        return '✗';
      case 'analyzing':
        return '⟳';
      default:
        return '⏱';
    }
  };

  // Login screen
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8" style={{ backgroundColor: colors.background.secondary }}>
        <Card className="w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold mb-2" style={{ color: colors.text.primary }}>
              Admin Login
            </h1>
            <p style={{ color: colors.text.secondary }}>
              Enter your API key to access the admin panel
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your admin API key"
                className="w-full px-4 py-2.5 rounded-xl"
                style={{
                  backgroundColor: colors.background.card,
                  color: colors.text.primary,
                  border: `2px solid ${colors.border.default}`,
                }}
                required
              />
            </div>

            <Button type="submit" variant="primary" className="w-full">
              Login
            </Button>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: colors.background.secondary }}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Influencer Submissions
            </h1>
            <p style={{ color: colors.text.secondary }}>
              Review and approve user-submitted influencers
            </p>
          </div>
          <Button onClick={handleLogout} variant="secondary">
            Logout
          </Button>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <div className="flex gap-2 overflow-x-auto">
            {['all', 'pending', 'analyzing', 'approved', 'rejected'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className="px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-all capitalize"
                style={{
                  backgroundColor: statusFilter === status ? colors.accent.primary : colors.background.secondary,
                  color: statusFilter === status ? 'white' : colors.text.primary,
                }}
              >
                {status}
              </button>
            ))}
          </div>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="mb-6">
            <div className="flex items-start gap-2" style={{ color: colors.accent.danger }}>
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>{error}</p>
            </div>
          </Card>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-block w-12 h-12 border-4 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: `${colors.accent.primary} transparent transparent transparent` }}
            />
            <p className="mt-4" style={{ color: colors.text.secondary }}>
              Loading submissions...
            </p>
          </div>
        )}

        {/* Submissions List */}
        {!loading && submissions.length === 0 && (
          <Card>
            <div className="text-center py-12">
              <p style={{ color: colors.text.secondary }}>
                No {statusFilter !== 'all' ? statusFilter : ''} submissions found.
              </p>
            </div>
          </Card>
        )}

        {!loading && submissions.length > 0 && (
          <div className="grid gap-4">
            {submissions.map((submission) => (
              <Card key={submission.id}>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  {/* Left Side - Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">@{submission.handle}</span>
                      <span className="px-2 py-1 rounded-lg text-xs font-bold uppercase" style={{
                        backgroundColor: getStatusColor(submission.status) + '20',
                        color: getStatusColor(submission.status),
                      }}>
                        {getStatusIcon(submission.status)} {submission.status}
                      </span>
                      <span className="text-sm px-2 py-1 rounded bg-gray-100 text-gray-700 capitalize">
                        {submission.platform}
                      </span>
                    </div>

                    {submission.reason && (
                      <p className="text-sm mb-2" style={{ color: colors.text.secondary }}>
                        Reason: {submission.reason}
                      </p>
                    )}

                    {submission.trust_score !== undefined && (
                      <p className="text-sm mb-2" style={{ color: colors.text.secondary }}>
                        Trust Score: <strong>{(submission.trust_score * 100).toFixed(0)}%</strong>
                      </p>
                    )}

                    <p className="text-xs" style={{ color: colors.text.tertiary }}>
                      Submitted {new Date(submission.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Right Side - Actions */}
                  <div className="flex flex-col gap-2">
                    {submission.status === 'pending' && (
                      <>
                        <Button
                          onClick={() => analyzeSubmission(submission.id)}
                          disabled={isSubmitting}
                          variant="secondary"
                        >
                          {isSubmitting ? 'Analyzing...' : 'Analyze'}
                        </Button>
                        <Button
                          onClick={() => setSelectedSubmission(submission)}
                          variant="primary"
                        >
                          Review
                        </Button>
                      </>
                    )}

                    {submission.status === 'approved' && submission.reviewed_at && (
                      <p className="text-xs text-center" style={{ color: colors.text.tertiary }}>
                        Approved {new Date(submission.reviewed_at).toLocaleDateString()}
                      </p>
                    )}

                    {submission.status === 'rejected' && submission.rejection_reason && (
                      <p className="text-xs" style={{ color: colors.accent.danger }}>
                        {submission.rejection_reason}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Review Modal */}
        {selectedSubmission && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setSelectedSubmission(null)} />
            <Card className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2" style={{ color: colors.text.primary }}>
                  Review Submission
                </h2>
                <p className="text-lg" style={{ color: colors.text.secondary }}>
                  @{selectedSubmission.handle} on {selectedSubmission.platform}
                </p>
              </div>

              {selectedSubmission.analysis_data && (
                <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: colors.background.secondary }}>
                  <h3 className="font-bold mb-2" style={{ color: colors.text.primary }}>Analysis Results</h3>
                  <pre className="text-sm overflow-auto" style={{ color: colors.text.secondary }}>
                    {JSON.stringify(selectedSubmission.analysis_data, null, 2)}
                  </pre>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
                    Admin Notes (Optional)
                  </label>
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    rows={3}
                    className="w-full px-4 py-2.5 rounded-xl"
                    style={{
                      backgroundColor: colors.background.card,
                      color: colors.text.primary,
                      border: `2px solid ${colors.border.default}`,
                    }}
                    placeholder="Add internal notes about this review..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: colors.text.secondary }}>
                    Rejection Reason (Required if rejecting)
                  </label>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    rows={2}
                    className="w-full px-4 py-2.5 rounded-xl"
                    style={{
                      backgroundColor: colors.background.card,
                      color: colors.text.primary,
                      border: `2px solid ${colors.border.default}`,
                    }}
                    placeholder="Explain why this submission is being rejected..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => setSelectedSubmission(null)}
                    variant="secondary"
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => reviewSubmission(selectedSubmission.id, 'rejected')}
                    disabled={isSubmitting || !rejectionReason.trim()}
                    variant="secondary"
                    className="flex-1"
                    style={{ backgroundColor: colors.accent.danger, color: 'white' }}
                  >
                    {isSubmitting ? 'Processing...' : 'Reject'}
                  </Button>
                  <Button
                    onClick={() => reviewSubmission(selectedSubmission.id, 'approved')}
                    disabled={isSubmitting}
                    variant="primary"
                    className="flex-1"
                  >
                    {isSubmitting ? 'Processing...' : 'Approve & Add'}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
