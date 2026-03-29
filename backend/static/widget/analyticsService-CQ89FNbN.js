import { e as apiClient } from "./loader-BNVANRgf.js";
async function flushWidgetAnalyticsEvents(payload) {
  const response = await apiClient.post(
    "/api/v1/analytics/widget/events",
    payload
  );
  return response;
}
const analyticsService = {
  /**
   * Get sales breakdown by country, city, and province.
   * Data is populated by Shopify order webhooks.
   */
  async getGeographic() {
    const response = await apiClient.get(
      "/api/v1/analytics/geographic"
    );
    return response;
  },
  /**
   * Get anonymized analytics summary with order stats and conversation stats.
   * All data is tier=ANONYMIZED with no PII. 30-day window.
   */
  async getSummary() {
    const response = await apiClient.get(
      "/api/v1/analytics/summary"
    );
    return response;
  },
  /**
   * Get top products sold in the last N days.
   */
  async getTopProducts(days = 30, limit = 5) {
    const response = await apiClient.get(
      `/api/v1/analytics/top-products?days=${days}&limit=${limit}`
    );
    return response;
  },
  /**
   * Get pending orders including unfulfilled orders and estimated delivery dates.
   */
  async getPendingOrders(limit = 10, offset = 0) {
    const response = await apiClient.get(
      `/api/v1/analytics/pending-orders?limit=${limit}&offset=${offset}`
    );
    return response;
  },
  async getBotQuality(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/bot-quality?days=${days}`
    );
    return response;
  },
  async getPeakHours(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/peak-hours?days=${days}`
    );
    return response;
  },
  async getConversionFunnel(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/conversion-funnel?days=${days}`
    );
    return response;
  },
  async getKnowledgeGaps(days = 30, limit = 10) {
    const response = await apiClient.get(
      `/api/v1/analytics/knowledge-gaps?days=${days}&limit=${limit}`
    );
    return response;
  },
  async getBenchmarks(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/benchmarks?days=${days}`
    );
    return response;
  },
  async getSentimentTrend(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/sentiment-trend?days=${days}`
    );
    return response;
  },
  // ────────────────────────────────────────────────────────────────
  // Widget Analytics (Story 9-10)
  // ────────────────────────────────────────────────────────────────
  /**
   * Send batched widget analytics events to the backend.
   */
  async sendWidgetEvents(payload) {
    return flushWidgetAnalyticsEvents(payload);
  },
  /**
   * Get widget analytics metrics for the dashboard.
   */
  async getWidgetMetrics(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/widget?days=${days}`
    );
    return response;
  },
  /**
   * Export widget analytics as CSV.
   */
  async exportWidgetAnalytics(startDate, endDate, merchantId) {
    const response = await fetch(
      `/api/v1/analytics/widget/export?merchant_id=${merchantId}&start_date=${startDate}&end_date=${endDate}`,
      {
        credentials: "include"
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
  async getFeedbackAnalytics(startDate, endDate) {
    const params = new URLSearchParams();
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    const queryString = params.toString();
    const response = await apiClient.get(
      `/api/v1/feedback/analytics${queryString ? `?${queryString}` : ""}`
    );
    return response;
  },
  async getKnowledgeEffectiveness(days = 7) {
    const response = await apiClient.get(
      `/api/v1/analytics/knowledge-effectiveness?days=${days}`
    );
    return response.data;
  },
  async getKnowledgeGapsData(days = 30, limit = 10) {
    const response = await apiClient.get(
      `/api/v1/analytics/knowledge-gaps?days=${days}&limit=${limit}`
    );
    return response;
  },
  async getTopTopics(days = 7) {
    const response = await apiClient.get(
      `/api/v1/analytics/top-topics?days=${days}`
    );
    return response.data;
  },
  async getResponseTimeDistribution(days = 7) {
    const response = await apiClient.get(
      `/api/v1/analytics/response-time-distribution?days=${days}`
    );
    return response.data;
  },
  async getFaqUsage(days = 30) {
    const response = await apiClient.get(
      `/api/v1/analytics/faq-usage?days=${days}`
    );
    return response;
  }
};
export {
  analyticsService,
  flushWidgetAnalyticsEvents
};
