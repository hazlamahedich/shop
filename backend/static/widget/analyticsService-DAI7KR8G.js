var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
const API_BASE_URL = "";
class ApiClient {
  constructor() {
    __publicField(this, "csrfToken", null);
    __publicField(this, "tokenFetchPromise", null);
  }
  async fetchCsrfToken() {
    if (this.tokenFetchPromise) {
      return this.tokenFetchPromise;
    }
    this.tokenFetchPromise = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token`);
        if (!response.ok) {
          throw new Error(`Failed to fetch CSRF token: ${response.status}`);
        }
        const data = await response.json();
        this.csrfToken = data.csrf_token;
        return data.csrf_token;
      } catch (error) {
        console.error("Error fetching CSRF token:", error);
        throw error;
      } finally {
        this.tokenFetchPromise = null;
      }
    })();
    return this.tokenFetchPromise;
  }
  async request(endpoint, options = {}) {
    var _a;
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = new Headers(options.headers || {});
    if (!options.cache) {
      options.cache = "no-store";
    }
    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const method = (options.method || "GET").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      if (!this.csrfToken) {
        try {
          await this.fetchCsrfToken();
        } catch (e) {
          console.warn("Proceeding without CSRF token due to fetch error", e);
        }
      }
      if (this.csrfToken) {
        headers.set("X-CSRF-Token", this.csrfToken);
      }
    }
    const config = {
      credentials: "include",
      // Ensure cookies are sent (Story 1.8)
      ...options,
      headers
    };
    let response = await fetch(url, config);
    if (response.status === 403) {
      const errorBody = await response.clone().json().catch(() => ({}));
      if (errorBody.error_code === 2e3) {
        console.log("CSRF token invalid, refreshing...");
        this.csrfToken = null;
        try {
          const newToken = await this.fetchCsrfToken();
          headers.set("X-CSRF-Token", newToken);
          config.headers = headers;
          response = await fetch(url, config);
        } catch (e) {
          console.error("Failed to refresh CSRF token, throwing original error");
        }
      }
    }
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.message || ((_a = errorData.detail) == null ? void 0 : _a.message) || `API Error ${response.status}`;
      const error = new Error(message);
      error.status = response.status;
      error.code = errorData.error_code;
      error.details = errorData.details;
      throw error;
    }
    const jsonResult = await response.json();
    return jsonResult;
  }
  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: "GET" });
  }
  async post(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: "POST",
      body: JSON.stringify(body)
    });
  }
  async put(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: "PUT",
      body: JSON.stringify(body)
    });
  }
  async patch(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: "PATCH",
      body: JSON.stringify(body)
    });
  }
  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: "DELETE" });
  }
}
const apiClient = new ApiClient();
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
