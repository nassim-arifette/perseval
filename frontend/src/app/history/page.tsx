'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { getThemeColors, theme, animations } from '../lib/theme';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { storage, SavedAnalysis } from '../lib/storage';
import { useEffect, useState } from 'react';

export default function HistoryPage() {
  const { theme: currentTheme } = useTheme();
  const colors = getThemeColors(currentTheme);
  const [analyses, setAnalyses] = useState<SavedAnalysis[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<SavedAnalysis | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterLabel, setFilterLabel] = useState<'all' | 'scam' | 'not_scam' | 'uncertain'>('all');

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = () => {
    const allAnalyses = storage.getAnalyses();
    setAnalyses(allAnalyses);
  };

  const deleteAnalysis = (id: string) => {
    storage.deleteAnalysis(id);
    loadAnalyses();
    if (selectedAnalysis?.id === id) {
      setSelectedAnalysis(null);
    }
  };

  const clearAllAnalyses = () => {
    if (confirm('Are you sure you want to delete all saved analyses? This cannot be undone.')) {
      storage.clearAll();
      loadAnalyses();
      setSelectedAnalysis(null);
    }
  };

  // Filter analyses
  const filteredAnalyses = analyses.filter((analysis) => {
    const matchesSearch =
      !searchTerm ||
      analysis.input.text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      analysis.input.influencerHandle?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterLabel === 'all' || analysis.result.message_prediction.label === filterLabel;

    return matchesSearch && matchesFilter;
  });

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
            Analysis History
          </h1>
          <p style={{ color: colors.text.secondary }}>
            View and manage your saved scam detection analyses
          </p>
        </motion.div>

        {/* Search and Filters */}
        <motion.div variants={animations.slideUp} className="mb-6">
          <Card padding="md">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search analyses..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 rounded-xl"
                  style={{
                    backgroundColor: colors.background.secondary,
                    border: `2px solid ${colors.border.default}`,
                    color: colors.text.primary,
                  }}
                />
              </div>

              {/* Filter buttons */}
              <div className="flex gap-2">
                {(['all', 'scam', 'not_scam', 'uncertain'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setFilterLabel(filter)}
                    className="px-4 py-2 rounded-xl font-medium capitalize transition-all"
                    style={{
                      backgroundColor:
                        filterLabel === filter
                          ? colors.accent.primary
                          : colors.background.secondary,
                      color:
                        filterLabel === filter
                          ? colors.text.inverse
                          : colors.text.secondary,
                      border: `2px solid ${
                        filterLabel === filter ? colors.accent.primary : colors.border.default
                      }`,
                    }}
                  >
                    {filter.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Clear all button */}
              {analyses.length > 0 && (
                <Button variant="danger" size="md" onClick={clearAllAnalyses}>
                  Clear All
                </Button>
              )}
            </div>
          </Card>
        </motion.div>

        {/* Analysis List */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* List */}
          <motion.div variants={animations.slideUp}>
            <Card padding="md" className="h-[calc(100vh-350px)] overflow-y-auto">
              {filteredAnalyses.length > 0 ? (
                <div className="space-y-3">
                  <AnimatePresence>
                    {filteredAnalyses.map((analysis, index) => (
                      <motion.div
                        key={analysis.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => setSelectedAnalysis(analysis)}
                        className="p-4 rounded-xl cursor-pointer transition-all"
                        style={{
                          backgroundColor:
                            selectedAnalysis?.id === analysis.id
                              ? `${colors.accent.primary}15`
                              : colors.background.secondary,
                          border: `2px solid ${
                            selectedAnalysis?.id === analysis.id
                              ? colors.accent.primary
                              : colors.border.default
                          }`,
                        }}
                        whileHover={{ scale: 1.02 }}
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className="w-10 h-10 rounded-full flex items-center justify-center text-xl flex-shrink-0"
                            style={{
                              backgroundColor: `${getLabelColor(
                                analysis.result.message_prediction.label
                              )}20`,
                            }}
                          >
                            {getLabelIcon(analysis.result.message_prediction.label)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p
                              className="font-medium line-clamp-2 mb-1"
                              style={{ color: colors.text.primary }}
                            >
                              {analysis.input.text || 'No message text'}
                            </p>
                            <div className="flex items-center gap-2 text-xs">
                              <span style={{ color: colors.text.tertiary }}>
                                {new Date(analysis.timestamp).toLocaleDateString()}
                              </span>
                              <span
                                className="px-2 py-0.5 rounded-full font-medium capitalize"
                                style={{
                                  backgroundColor: getLabelColor(
                                    analysis.result.message_prediction.label
                                  ),
                                  color: colors.text.inverse,
                                }}
                              >
                                {analysis.result.message_prediction.label.replace('_', ' ')}
                              </span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-6xl mb-4">📝</p>
                    <p className="text-lg font-medium" style={{ color: colors.text.primary }}>
                      No analyses found
                    </p>
                    <p className="text-sm" style={{ color: colors.text.tertiary }}>
                      {analyses.length === 0
                        ? 'Start checking messages to see them here'
                        : 'Try adjusting your search or filters'}
                    </p>
                  </div>
                </div>
              )}
            </Card>
          </motion.div>

          {/* Detail View */}
          <motion.div variants={animations.slideUp}>
            <Card padding="lg" className="h-[calc(100vh-350px)] overflow-y-auto">
              {selectedAnalysis ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="space-y-6"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                        style={{
                          backgroundColor: `${getLabelColor(
                            selectedAnalysis.result.message_prediction.label
                          )}20`,
                        }}
                      >
                        {getLabelIcon(selectedAnalysis.result.message_prediction.label)}
                      </div>
                      <div>
                        <h3
                          className="text-lg font-bold capitalize"
                          style={{ color: colors.text.primary }}
                        >
                          {selectedAnalysis.result.message_prediction.label.replace('_', ' ')}
                        </h3>
                        <p className="text-sm" style={{ color: colors.text.tertiary }}>
                          {new Date(selectedAnalysis.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => deleteAnalysis(selectedAnalysis.id)}
                    >
                      Delete
                    </Button>
                  </div>

                  {/* Message */}
                  <div>
                    <h4
                      className="text-sm font-semibold mb-2"
                      style={{ color: colors.text.secondary }}
                    >
                      Message
                    </h4>
                    <div
                      className="p-4 rounded-xl"
                      style={{
                        backgroundColor: colors.background.secondary,
                        border: `1px solid ${colors.border.default}`,
                      }}
                    >
                      <p style={{ color: colors.text.primary }}>
                        {selectedAnalysis.input.text || 'No message text'}
                      </p>
                    </div>
                  </div>

                  {/* Score */}
                  <div>
                    <h4
                      className="text-sm font-semibold mb-2"
                      style={{ color: colors.text.secondary }}
                    >
                      Confidence Score
                    </h4>
                    <div className="flex items-center gap-3">
                      <div
                        className="flex-1 h-2 rounded-full overflow-hidden"
                        style={{ backgroundColor: colors.border.default }}
                      >
                        <motion.div
                          className="h-full rounded-full"
                          style={{
                            backgroundColor: getLabelColor(
                              selectedAnalysis.result.message_prediction.label
                            ),
                          }}
                          initial={{ width: 0 }}
                          animate={{
                            width: `${selectedAnalysis.result.message_prediction.score * 100}%`,
                          }}
                          transition={{ duration: 0.5, ease: 'easeOut' }}
                        />
                      </div>
                      <span
                        className="text-lg font-bold"
                        style={{ color: colors.text.primary }}
                      >
                        {(selectedAnalysis.result.message_prediction.score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Reason */}
                  {selectedAnalysis.result.message_prediction.reason && (
                    <div>
                      <h4
                        className="text-sm font-semibold mb-2"
                        style={{ color: colors.text.secondary }}
                      >
                        Analysis Reason
                      </h4>
                      <div
                        className="p-4 rounded-xl"
                        style={{
                          backgroundColor: colors.background.secondary,
                          border: `1px solid ${colors.border.default}`,
                        }}
                      >
                        <p style={{ color: colors.text.primary }}>
                          {selectedAnalysis.result.message_prediction.reason}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {selectedAnalysis.result.final_summary && (
                    <div>
                      <h4
                        className="text-sm font-semibold mb-2"
                        style={{ color: colors.text.secondary }}
                      >
                        Final Summary
                      </h4>
                      <div
                        className="p-4 rounded-xl"
                        style={{
                          backgroundColor: colors.background.secondary,
                          border: `1px solid ${colors.border.default}`,
                        }}
                      >
                        <p style={{ color: colors.text.primary }}>
                          {selectedAnalysis.result.final_summary}
                        </p>
                      </div>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-6xl mb-4">👈</p>
                    <p className="text-lg font-medium" style={{ color: colors.text.primary }}>
                      Select an analysis
                    </p>
                    <p className="text-sm" style={{ color: colors.text.tertiary }}>
                      Click on any analysis to view details
                    </p>
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
