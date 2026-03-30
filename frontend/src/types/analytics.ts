/**
 * FAQ Usage Types (Story 10-10)
 *
 * TypeScript interfaces for FAQ Usage Widget API responses.
 */

export interface FaqUsageItem {
  id: number;
  question: string;
  clickCount: number;
  conversionRate: number;
  followupCount: number;
  isUnused: boolean;
  previousPeriod: {
    clickCount: number;
    conversionRate: number;
  };
  change: {
    clickChange: number | null;
    conversionChange: number | null;
  };
}

export interface FaqUsageSummary {
  totalFaqs: number;
  totalClicks: number;
  avgConversionRate: number;
  unusedCount: number;
}

export interface FaqUsageData {
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  faqs: FaqUsageItem[];
  summary: FaqUsageSummary;
  lastUpdated: string;
}

// ────────────────────────────────────────────────────────────────
// Answer Performance Dashboard Types
// ────────────────────────────────────────────────────────────────

/**
 * Answer Quality Score - Aggregate metric for RAG performance
 */
export interface AnswerQualityScore {
  score: number; // 0-100
  status: 'excellent' | 'good' | 'fair' | 'poor';
  trend: number[];
  lastUpdated: string;
}

/**
 * Top Customer Questions with performance metrics
 */
export interface TopQuestion {
  question: string;
  frequency: number;
  matchRate: number;
  avgConfidence: number;
  category: string;
  trend: 'rising' | 'falling' | 'stable';
}

export interface TopQuestionsResponse {
  questions: TopQuestion[];
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  lastUpdated: string;
}

/**
 * Customer Feedback Metrics for RAG answers
 */
export interface CustomerFeedbackMetrics {
  totalFeedback: number;
  positiveRate: number;
  negativeRate: number;
  themes: {
    theme: string;
    count: number;
    sentiment: 'positive' | 'negative';
  }[];
  lastUpdated: string;
}

/**
 * Document Performance and Usage Analytics
 */
export interface DocumentPerformance {
  documentId: number;
  filename: string;
  referenceCount: number;
  avgConfidence: number;
  lastReferenced: string;
  status: 'active' | 'unused' | 'outdated';
}

export interface DocumentPerformanceResponse {
  documents: DocumentPerformance[];
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  lastUpdated: string;
}

/**
 * High-Impact Improvements - Prioritized action items
 */
export interface ImprovementAction {
  id: string;
  question: string;
  frequency: number;
  matchRate: number;
  estimatedHandoffReduction: number;
  suggestedAction: 'add_faq' | 'upload_document' | 'update_document';
  priority: 'high' | 'medium' | 'low';
}

export interface HighImpactImprovementsResponse {
  actions: ImprovementAction[];
  totalEstimatedImpact: number;
  lastUpdated: string;
}

/**
 * Enhanced Query Performance with Response Times
 */
export interface QueryPerformanceMetrics {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  responseTime: {
    p50: number | null;
    p95: number | null;
    p99: number | null;
  };
  trend: number[];
  lastUpdated: string;
}
