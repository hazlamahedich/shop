/**
 * Analytics API Service
 *
 * Story 4-13: Geographic Analytics
 * Story 6-4: Anonymized Analytics Summary (Tier-Aware)
 *
 * Handles API calls for analytics endpoints populated by Shopify webhooks.
 */

import { apiClient } from './api';

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
  // Additional fields the backend may return
  [key: string]: unknown;
}

export interface OrderStats {
  total: number;
  totalRevenue: number;
  byStatus: Record<string, number>;
  avgOrderValue: number | null;
  // Additional fields the backend may return
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

export const analyticsService = {
  /**
   * Get sales breakdown by country, city, and province.
   * Data is populated by Shopify order webhooks.
   *
   * @returns GeographicAnalyticsResponse
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
   *
   * @returns AnonymizedSummaryResponse
   */
  async getSummary(): Promise<AnonymizedSummaryResponse> {
    const response = await apiClient.get<AnonymizedSummaryResponse>(
      '/api/v1/analytics/summary'
    );
    return response as unknown as AnonymizedSummaryResponse;
  },
};
