/**
 * Analytics API Service
 *
 * Story 4-13: Geographic Analytics
 * Story 6-4: Anonymized Analytics Summary (Tier-Aware)
 * Story 9-10: Widget Analytics
 *
 * Handles API calls for analytics endpoints populated by Shopify webhooks.
 */

import { apiClient } from './api';

// ────────────────────────────────────────────────────────────────
// Widget Analytics (Story 9-10)
// ────────────────────────────────────────────────────────────────

export type WidgetEventType =
  | 'widget_open'
  | 'message_send'
  | 'quick_reply_click'
  | 'voice_input'
  | 'proactive_trigger'
  | 'carousel_engagement';

export interface WidgetAnalyticsEventPayload {
  type: WidgetEventType;
  timestamp: string;
  session_id: string;
  metadata?: Record<string, unknown>;
}

export interface WidgetAnalyticsEventsRequest {
  merchant_id: number;
  events: WidgetAnalyticsEventPayload[];
}

export interface WidgetAnalyticsEventsResponse {
  accepted: number;
}

export interface WidgetAnalyticsMetrics {
  merchantId: number;
  period: {
    start: string;
    end: string;
    days: number;
  };
  metrics: {
    openRate: number;
    messageRate: number;
    quickReplyRate: number;
    voiceInputRate: number;
    proactiveConversionRate: number;
    carouselEngagementRate: number;
  };
  trends: {
    openRateChange: number;
    messageRateChange: number;
  };
  performance: {
    avgLoadTimeMs: number;
    p95LoadTimeMs: number;
    bundleSizeKb: number;
  };
}

/**
 * Flush widget analytics events to the backend.
 * Used by the widget analytics utility for batch sending.
 *
 * @param payload Events payload with merchantId and events array
 * @returns Number of accepted events
 */
export async function flushWidgetAnalyticsEvents(
  payload: WidgetAnalyticsEventsRequest
): Promise<WidgetAnalyticsEventsResponse> {
  const response = await apiClient.post<WidgetAnalyticsEventsResponse>(
    '/api/v1/analytics/widget/events',
    payload as unknown as Record<string, unknown>
  );
  return response as unknown as WidgetAnalyticsEventsResponse;
}

// ────────────────────────────────────────────────────────────────
// Geographic Analytics
// ────────────────────────────────────────────────────────────────

export interface GeographicBreakdown {
  country: string;
  countryName: string | null;
  orderCount: number;
  totalRevenue: number;
}

export interface CityBreakdown {
  city: string;
  country: string;
  orderCount: number;
  totalRevenue: number;
}

export interface ProvinceBreakdown {
  province: string;
  country: string;
  orderCount: number;
  totalRevenue: number;
}

export interface GeographicAnalyticsResponse {
  byCountry: GeographicBreakdown[];
  byCity: CityBreakdown[];
  byProvince: ProvinceBreakdown[];
  totalOrders: number;
  totalRevenue: number;
}

// ────────────────────────────────────────────────────────────────
// Anonymized Analytics Summary (conversations + orders, 30-day)
// ────────────────────────────────────────────────────────────────

export interface ConversationStats {
  total: number;
  active: number;
  handoff: number;
  closed: number;
  satisfactionRate: number | null;
  conversations?: {
    total: number;
    avgMessagesPerConversation: number;
  };
  [key: string]: unknown;
}

export interface OrderStats {
  total: number;
  totalRevenue: number;
  byStatus: Record<string, number>;
  avgOrderValue: number | null;
  previousPeriod?: {
    total: number;
    totalRevenue: number;
  };
  momComparison?: {
    revenueChangePercent: number | null;
    ordersChangePercent: number | null;
    conversationsChangePercent: number | null;
  };
  [key: string]: unknown;
}

export interface TierDistribution {
  voluntary: number;
  operational: number;
  anonymized: number;
  [key: string]: unknown;
}

export interface AnonymizedSummaryResponse {
  merchantId: number;
  tierDistribution: TierDistribution;
  conversationStats: ConversationStats;
  orderStats: OrderStats;
  generatedAt: string;
  tier: string;
}

// ────────────────────────────────────────────────────────────────
// Service Methods
// ────────────────────────────────────────────────────────────────

export interface TopProduct {
  productId: string;
  title: string;
  quantitySold: number;
  totalRevenue: number;
  imageUrl: string | null;
}

export interface TopProductsResponse {
  items: TopProduct[];
  merchantId: number;
  days: number;
}

export interface PendingOrder {
  orderNumber: string;
  status: string;
  total: number;
  currencyCode: string;
  estimatedDelivery: string | null;
  createdAt: string | null;
}

export interface PendingOrdersResponse {
  items: PendingOrder[];
  merchantId: number;
}

export interface BotQualityMetrics {
  merchantId: number;
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  avgResponseTimeSeconds: number;
  fallbackRate: number;
  resolutionRate: number;
  csatScore: number | null;
  csatChange: number | null;
  satisfactionRate: number | null;
  totalConversations: number;
  healthStatus: 'healthy' | 'warning' | 'critical';
  metrics: {
    totalConversations: number;
    fallbackConversations: number;
    resolvedConversations: number;
    satisfiedCount: number;
    unsatisfiedCount: number;
  };
}

export const analyticsService = {
  /**
   * Get sales breakdown by country, city, and province.
   * Data is populated by Shopify order webhooks.
   */
  async getGeographic(): Promise<GeographicAnalyticsResponse> {
    const response = await apiClient.get<GeographicAnalyticsResponse>(
      '/api/v1/analytics/geographic'
    );
    return response as unknown as GeographicAnalyticsResponse;
  },

  /**
   * Get anonymized analytics summary with order stats and conversation stats.
   * All data is tier=ANONYMIZED with no PII. 30-day window.
   */
  async getSummary(): Promise<AnonymizedSummaryResponse> {
    const response = await apiClient.get<AnonymizedSummaryResponse>(
      '/api/v1/analytics/summary'
    );
    return response as unknown as AnonymizedSummaryResponse;
  },

  /**
   * Get top products sold in the last N days.
   */
  async getTopProducts(days = 30, limit = 5): Promise<TopProductsResponse> {
    const response = await apiClient.get<TopProductsResponse>(
      `/api/v1/analytics/top-products?days=${days}&limit=${limit}`
    );
    return response as unknown as TopProductsResponse;
  },

  /**
   * Get pending orders including unfulfilled orders and estimated delivery dates.
   */
  async getPendingOrders(limit = 10, offset = 0): Promise<PendingOrdersResponse> {
    const response = await apiClient.get<PendingOrdersResponse>(
      `/api/v1/analytics/pending-orders?limit=${limit}&offset=${offset}`
    );
    return response as unknown as PendingOrdersResponse;
  },

  async getBotQuality(days = 30): Promise<BotQualityMetrics> {
    const response = await apiClient.get<BotQualityMetrics>(
      `/api/v1/analytics/bot-quality?days=${days}`
    );
    return response as unknown as BotQualityMetrics;
  },

  async getPeakHours(days = 30): Promise<unknown> {
    const response = await apiClient.get(
      `/api/v1/analytics/peak-hours?days=${days}`
    );
    return response as unknown;
  },

  async getConversionFunnel(days = 30): Promise<unknown> {
    const response = await apiClient.get(
      `/api/v1/analytics/conversion-funnel?days=${days}`
    );
    return response as unknown;
  },

  async getKnowledgeGaps(days = 30, limit = 10): Promise<unknown> {
    const response = await apiClient.get(
      `/api/v1/analytics/knowledge-gaps?days=${days}&limit=${limit}`
    );
    return response as unknown;
  },

  async getBenchmarks(days = 30): Promise<unknown> {
    const response = await apiClient.get(
      `/api/v1/analytics/benchmarks?days=${days}`
    );
    return response as unknown;
  },

  async getSentimentTrend(days = 30): Promise<unknown> {
    const response = await apiClient.get(
      `/api/v1/analytics/sentiment-trend?days=${days}`
    );
    return response as unknown;
  },

  // ────────────────────────────────────────────────────────────────
  // Widget Analytics (Story 9-10)
  // ────────────────────────────────────────────────────────────────

  /**
   * Send batched widget analytics events to the backend.
   */
  async sendWidgetEvents(
    payload: WidgetAnalyticsEventsRequest
  ): Promise<WidgetAnalyticsEventsResponse> {
    return flushWidgetAnalyticsEvents(payload);
  },

  /**
   * Get widget analytics metrics for the dashboard.
   */
  async getWidgetMetrics(days = 30): Promise<WidgetAnalyticsMetrics> {
    const response = await apiClient.get<WidgetAnalyticsMetrics>(
      `/api/v1/analytics/widget?days=${days}`
    );
    return response as unknown as WidgetAnalyticsMetrics;
  },

  /**
   * Export widget analytics as CSV.
   */
  async exportWidgetAnalytics(
    startDate: string,
    endDate: string,
    merchantId: number
  ): Promise<Blob> {
    const response = await fetch(
      `/api/v1/analytics/widget/export?merchant_id=${merchantId}&start_date=${startDate}&end_date=${endDate}`,
      {
        credentials: 'include',
      }
    );
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }
    return response.blob();
  },

  // ────────────────────────────────────────────────────────────────
  // Feedback Analytics (Story 10-4)
  // ────────────────────────────────────────────────────────────────

  async getFeedbackAnalytics(startDate?: string, endDate?: string): Promise<FeedbackAnalyticsResponse> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const queryString = params.toString();
    const response = await apiClient.get<FeedbackAnalyticsResponse>(
      `/api/v1/feedback/analytics${queryString ? `?${queryString}` : ''}`
    );
    return response as unknown as FeedbackAnalyticsResponse;
  },

  async getKnowledgeEffectiveness(days = 7): Promise<KnowledgeEffectivenessResponse> {
    const response = await apiClient.get<{ data: KnowledgeEffectivenessResponse }>(
      `/api/v1/analytics/knowledge-effectiveness?days=${days}`
    );
    return (response as unknown as { data: KnowledgeEffectivenessResponse }).data;
  },

  async getKnowledgeGaps(days = 30, limit = 10): Promise<KnowledgeGapsData> {
    const response = await apiClient.get<KnowledgeGapsData>(
      `/api/v1/analytics/knowledge-gaps?days=${days}&limit=${limit}`
    );
    return response as unknown as KnowledgeGapsData;
  },
};

export interface RecentNegativeFeedback {
  messageId: number;
  comment: string | null;
  createdAt: string;
}

export interface DailyFeedbackTrend {
  date: string;
  positive: number;
  negative: number;
}

export interface FeedbackAnalyticsResponse {
  totalRatings: number;
  positiveCount: number;
  negativeCount: number;
  positivePercent: number;
  negativePercent: number;
  recentNegative: RecentNegativeFeedback[];
  trend: DailyFeedbackTrend[];
}

export interface KnowledgeEffectivenessResponse {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  trend: number[];
  lastUpdated: string;
}
