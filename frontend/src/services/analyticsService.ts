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

  /**
   * Get top products sold in the last N days.
   *
   * @param days Number of days to include (default 30)
   * @param limit Number of top products to return (default 5)
   * @returns TopProductsResponse
   */
  async getTopProducts(days = 30, limit = 5): Promise<TopProductsResponse> {
    const response = await apiClient.get<TopProductsResponse>(
      `/api/v1/analytics/top-products?days=${days}&limit=${limit}`
    );
    return response as unknown as TopProductsResponse;
  },

  /**
   * Get pending orders including unfulfilled orders and estimated delivery dates.
   *
   * @param limit Number of pending orders to return (default 10)
   * @param offset Offset for pagination (default 0)
   * @returns PendingOrdersResponse
   */
  async getPendingOrders(limit = 10, offset = 0): Promise<PendingOrdersResponse> {
    const response = await apiClient.get<PendingOrdersResponse>(
      `/api/v1/analytics/pending-orders?limit=${limit}&offset=${offset}`
    );
    return response as unknown as PendingOrdersResponse;
  },
};
