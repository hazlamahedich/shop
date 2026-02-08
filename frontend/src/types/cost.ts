/**
 * Cost Tracking Types
 *
 * Types for LLM cost tracking with real-time updates
 * Story 3-5: Real-Time Cost Tracking
 */

/**
 * Individual LLM cost record
 */
export interface CostRecord {
  id: number;
  requestTimestamp: string;
  provider: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  inputCostUsd: number;
  outputCostUsd: number;
  totalCostUsd: number;
  processingTimeMs?: number;
}

/**
 * Conversation cost detail response
 */
export interface ConversationCost {
  conversationId: string;
  totalCostUsd: number;
  totalTokens: number;
  requestCount: number;
  avgCostPerRequest: number;
  provider: string;
  model: string;
  requests: CostRecord[];
}

/**
 * Top conversation by cost
 */
export interface TopConversation {
  conversationId: string;
  totalCostUsd: number;
  requestCount: number;
}

/**
 * Cost summary for a provider
 */
export interface ProviderCostSummary {
  costUsd: number;
  requests: number;
}

/**
 * Daily cost summary
 */
export interface DailyCostBreakdown {
  date: string;
  totalCostUsd: number;
  requestCount: number;
}

/**
 * Cost summary response with period aggregates
 */
export interface CostSummary {
  totalCostUsd: number;
  totalTokens: number;
  requestCount: number;
  avgCostPerRequest: number;
  topConversations: TopConversation[];
  costsByProvider: Record<string, ProviderCostSummary>;
  dailyBreakdown: DailyCostBreakdown[];
  previousPeriodSummary?: CostSummary;
}

/**
 * API response envelope
 */
export interface ApiEnvelope<T> {
  data: T;
  meta: {
    requestId: string;
  };
}

/**
 * Cost summary query parameters
 */
export interface CostSummaryParams {
  dateFrom?: string; // ISO 8601 date string
  dateTo?: string; // ISO 8601 date string
}

/**
 * Cost tracking store state
 */
export interface CostTrackingState {
  // Conversation costs
  conversationCosts: Record<string, ConversationCost>;
  conversationCostsLoading: Record<string, boolean>;
  conversationCostsError: Record<string, string | null>;

  // Cost summary
  costSummary: CostSummary | null;
  previousPeriodSummary: CostSummary | null;
  costSummaryLoading: boolean;
  costSummaryError: string | null;
  costSummaryParams: CostSummaryParams;

  // Merchant settings
  merchantSettings: { budgetCap?: number; config: Record<string, unknown> } | null;
  merchantSettingsLoading: boolean;
  merchantSettingsError: string | null;

  // Real-time polling
  isPolling: boolean;
  pollingInterval: number; // in milliseconds
  lastUpdate: string | null;

  // Actions - Conversation Costs
  fetchConversationCost: (conversationId: string) => Promise<void>;
  clearConversationCost: (conversationId: string) => void;

  // Actions - Cost Summary
  fetchCostSummary: (params?: CostSummaryParams) => Promise<void>;
  setCostSummaryParams: (params: CostSummaryParams) => void;

  // Actions - Merchant Settings
  updateMerchantSettings: (budgetCap?: number) => Promise<void>;
  getMerchantSettings: () => Promise<void>;

  // Actions - Real-time Polling
  startPolling: (conversationId?: string, interval?: number) => void;
  stopPolling: () => void;
  setPollingInterval: (interval: number) => void;

  // Actions - Utility
  clearErrors: () => void;
  reset: () => void;
}

/**
 * Cost display utilities
 */
export const COST_THRESHOLDS = {
  LOW: 0.01, // $0.01 and below - green
  MEDIUM: 0.1, // $0.01 - $0.10 - yellow
  HIGH: Infinity, // $0.10+ - red
} as const;

export type CostLevel = 'low' | 'medium' | 'high';

/**
 * Get cost level for color coding
 */
export function getCostLevel(costUsd: number): CostLevel {
  if (costUsd <= COST_THRESHOLDS.LOW) return 'low';
  if (costUsd <= COST_THRESHOLDS.MEDIUM) return 'medium';
  return 'high';
}

/**
 * Format cost as USD string
 */
export function formatCost(costUsd: number | undefined | null, decimals: number = 4): string {
  if (costUsd === undefined || costUsd === null) return '$0.0000';
  return `$${costUsd.toFixed(decimals)}`;
}

/**
 * Format token count with K/M suffix
 */
export function formatTokens(tokens: number): string {
  if (tokens >= 1000000) {
    return `${(tokens / 1000000).toFixed(1)}M`;
  }
  if (tokens >= 1000) {
    return `${(tokens / 1000).toFixed(1)}K`;
  }
  return tokens.toString();
}
