// Local storage utilities for Perseval

import { FullAnalysisResponse } from './types';

export interface SavedAnalysis {
  id: string;
  timestamp: number;
  input: {
    text?: string;
    instagramUrl?: string;
    tiktokUrl?: string;
    influencerHandle?: string;
    companyName?: string;
    productName?: string;
  };
  result: FullAnalysisResponse;
}

const STORAGE_KEY = 'perseval-analyses';
const MAX_SAVED = 50; // Keep last 50 analyses

export const storage = {
  // Get all saved analyses
  getAnalyses(): SavedAnalysis[] {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return [];
      return JSON.parse(data);
    } catch (error) {
      console.error('Error reading analyses from localStorage:', error);
      return [];
    }
  },

  // Save a new analysis
  saveAnalysis(
    input: SavedAnalysis['input'],
    result: FullAnalysisResponse
  ): SavedAnalysis {
    try {
      const analyses = this.getAnalyses();
      const newAnalysis: SavedAnalysis = {
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        input,
        result,
      };

      // Add to beginning and limit to MAX_SAVED
      const updated = [newAnalysis, ...analyses].slice(0, MAX_SAVED);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return newAnalysis;
    } catch (error) {
      console.error('Error saving analysis to localStorage:', error);
      throw error;
    }
  },

  // Get a specific analysis by ID
  getAnalysisById(id: string): SavedAnalysis | undefined {
    return this.getAnalyses().find((a) => a.id === id);
  },

  // Delete an analysis by ID
  deleteAnalysis(id: string): void {
    try {
      const analyses = this.getAnalyses();
      const filtered = analyses.filter((a) => a.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error deleting analysis from localStorage:', error);
    }
  },

  // Clear all analyses
  clearAll(): void {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing analyses from localStorage:', error);
    }
  },

  // Get statistics for dashboard
  getStats() {
    const analyses = this.getAnalyses();
    const scamCount = analyses.filter(
      (a) => a.result.message_prediction.label === 'scam'
    ).length;
    const safeCount = analyses.filter(
      (a) => a.result.message_prediction.label === 'not_scam'
    ).length;
    const uncertainCount = analyses.filter(
      (a) => a.result.message_prediction.label === 'uncertain'
    ).length;

    return {
      total: analyses.length,
      scam: scamCount,
      safe: safeCount,
      uncertain: uncertainCount,
      scamPercentage: analyses.length > 0 ? (scamCount / analyses.length) * 100 : 0,
    };
  },

  // Get recent analyses (last N)
  getRecent(count: number = 5): SavedAnalysis[] {
    return this.getAnalyses().slice(0, count);
  },
};
