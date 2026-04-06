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

// ────────────────────────────────────────────────────────────────
// Conversation Flow Analytics Types (Story 11.12b)
// ────────────────────────────────────────────────────────────────

export interface ConversationFlowEnvelope<T> {
  has_data: boolean;
  data?: T;
  message?: string;
  period_days?: number;
}

export interface ConversationFlowOverviewData {
  total_conversations: number;
  average_turns: number;
  completion_rate: number | null;
  by_mode: ConversationFlowModeEntry[];
  daily_trend: ConversationFlowDailyTrend[];
}

export interface ConversationFlowLengthDistributionData {
  avg_turns: number;
  median_turns: number;
  p90_turns: number;
  total_conversations: number;
  length_distribution: { turn_count: number; conversation_count: number }[];
  by_mode: ConversationFlowModeEntry[];
  daily_trend: ConversationFlowDailyTrend[];
}

export interface ConversationFlowModeEntry {
  mode: string;
  avg_turns: number;
  conversation_count: number;
}

export interface ConversationFlowDailyTrend {
  date: string;
  total_turns: number;
  total_conversations: number;
  avg_turns: number;
}

export interface ConversationFlowClarificationData {
  top_sequences: { sequence: string; count: number }[];
  avg_clarification_depth: number;
  clarification_success_rate: number;
  total_clarifying_conversations: number;
}

export interface ConversationFlowFrictionData {
  friction_points: ConversationFlowFrictionPoint[];
  drop_off_intents: { intent: string; count: number }[];
  repeated_intents: { intent: string; count: number }[];
  processing_time_p90_ms: number;
  slow_turns_count: number;
  total_conversations_analyzed: number;
}

export interface ConversationFlowFrictionPoint {
  type: 'drop_off' | 'repeated_intent';
  intent: string;
  frequency: number;
}

export interface ConversationFlowSentimentData {
  stages: Record<string, Record<string, number>>;
  negative_shifts: ConversationFlowNegativeShift[];
  total_negative_shifts: number;
}

export interface ConversationFlowNegativeShift {
  conversation_id: number;
  early_negative_rate: number;
  late_negative_rate: number;
  intent_at_shift: string;
}

export interface ConversationFlowHandoffData {
  top_triggers: { intent: string; count: number }[];
  avg_handoff_length: number;
  avg_resolved_length: number;
  handoff_rate_per_intent: ConversationFlowHandoffRate[];
  anonymized_excerpts: ConversationFlowAnonymizedExcerpt[];
  privacy_note: string;
  total_handoff_conversations: number;
}

export interface ConversationFlowHandoffRate {
  intent: string;
  handoff_count: number;
  total_count: number;
  handoff_rate: number;
}

export interface ConversationFlowAnonymizedExcerpt {
  anonymized_message: string;
  intent_detected: string;
}

export interface ConversationFlowContextData {
  utilization_rate: number;
  total_turns: number;
  turns_with_context: number;
  by_mode: ConversationFlowContextModeEntry[];
  low_utilization_conversations: ConversationFlowLowUtilization[];
  improvement_opportunities: number;
}

export interface ConversationFlowContextModeEntry {
  mode: string;
  total_turns: number;
  turns_with_context: number;
  utilization_rate: number;
}

export interface ConversationFlowLowUtilization {
  conversation_id: number;
  total_turns: number;
  context_turns: number;
  utilization_rate: number;
}

export type ConversationFlowOverviewResponse =
  ConversationFlowEnvelope<ConversationFlowOverviewData>;
export type ConversationFlowLengthDistributionResponse =
  ConversationFlowEnvelope<ConversationFlowLengthDistributionData>;
export type ConversationFlowClarificationResponse =
  ConversationFlowEnvelope<ConversationFlowClarificationData>;
export type ConversationFlowFrictionResponse =
  ConversationFlowEnvelope<ConversationFlowFrictionData>;
export type ConversationFlowSentimentResponse =
  ConversationFlowEnvelope<ConversationFlowSentimentData>;
export type ConversationFlowHandoffResponse = ConversationFlowEnvelope<ConversationFlowHandoffData>;
export type ConversationFlowContextResponse = ConversationFlowEnvelope<ConversationFlowContextData>;
