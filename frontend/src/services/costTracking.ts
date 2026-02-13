/**
 * Cost Tracking API Service
 *
 * Story 3-5: Real-Time Cost Tracking
 * Story 3-8: Budget Alert Notifications
 *
 * Handles API calls for cost tracking endpoints
 */

import { apiClient } from './api';
import type { ApiEnvelope, ConversationCost, CostSummary, CostSummaryParams } from '../types/cost';

export interface BudgetAlert {
  id: number;
  threshold: number;
  message: string;
  createdAt: string;
  isRead: boolean;
}

export interface BudgetAlertListResponse {
  alerts: BudgetAlert[];
  unreadCount: number;
}

export interface BotStatus {
  isPaused: boolean;
  pauseReason: string | null;
  budgetPercentage: number | null;
  budgetCap: number | null;
  monthlySpend: number | null;
}

export interface ResumeBotResponse {
  success: boolean;
  message: string;
  newBudget: number | null;
}

export interface BudgetRecommendation {
  recommendedBudget: number;
  rationale: string;
  currentAvgDailyCost: number;
  projectedMonthlySpend: number;
}

/**
 * Cost tracking service
 */
export const costTrackingService = {
  /**
   * Get cost breakdown for a specific conversation
   *
   * @param conversationId - Conversation identifier
   * @returns Promise with conversation cost details
   */
  async getConversationCost(conversationId: string): Promise<ApiEnvelope<ConversationCost>> {
    return apiClient.get<ConversationCost>(`/api/costs/conversation/${conversationId}`);
  },

  /**
   * Get cost summary for the authenticated merchant
   *
   * @param params - Optional date range parameters
   * @returns Promise with cost summary data
   */
  async getCostSummary(params: CostSummaryParams = {}): Promise<ApiEnvelope<CostSummary>> {
    const queryParams = new URLSearchParams();

    if (params.dateFrom) {
      queryParams.append('date_from', params.dateFrom);
    }
    if (params.dateTo) {
      queryParams.append('date_to', params.dateTo);
    }

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/costs/summary?${queryString}` : '/api/costs/summary';

    return apiClient.get<CostSummary>(endpoint);
  },

  /**
   * Update merchant settings (e.g., budget cap)
   *
   * @param budgetCap - Optional budget cap value to update. Pass null to remove budget cap (no limit).
   * @returns Promise with updated merchant settings
   */
  async updateSettings(
    budgetCap?: number | null
  ): Promise<ApiEnvelope<{ budgetCap?: number; config: Record<string, unknown> }>> {
    const body = { budget_cap: budgetCap };

    return apiClient.patch<{ budgetCap?: number; config: Record<string, unknown> }>(
      '/api/merchant/settings',
      body
    );
  },

  /**
   * Get merchant settings
   *
   * @returns Promise with merchant settings
   */
  async getSettings(): Promise<
    ApiEnvelope<{ budgetCap?: number; config: Record<string, unknown> }>
  > {
    return apiClient.get<{ budgetCap?: number; config: Record<string, unknown> }>(
      '/api/merchant/settings'
    );
  },

  /**
   * Get budget alerts for the merchant
   *
   * @param unreadOnly - Only return unread alerts
   * @returns Promise with budget alerts
   */
  async getBudgetAlerts(unreadOnly = false): Promise<ApiEnvelope<BudgetAlertListResponse>> {
    const queryParams = unreadOnly ? '?unread_only=true' : '';
    return apiClient.get<BudgetAlertListResponse>(`/api/merchant/budget-alerts${queryParams}`);
  },

  /**
   * Mark a budget alert as read
   *
   * @param alertId - Alert ID to mark as read
   * @returns Promise with success status
   */
  async markAlertRead(alertId: number): Promise<ApiEnvelope<{ success: boolean }>> {
    return apiClient.post<{ success: boolean }>(`/api/merchant/budget-alerts/${alertId}/read`);
  },

  /**
   * Get bot status (paused/active)
   *
   * @returns Promise with bot status
   */
  async getBotStatus(): Promise<ApiEnvelope<BotStatus>> {
    return apiClient.get<BotStatus>('/api/merchant/bot-status');
  },

  /**
   * Resume bot manually
   *
   * @returns Promise with resume response
   */
  async resumeBot(): Promise<ApiEnvelope<ResumeBotResponse>> {
    return apiClient.post<ResumeBotResponse>('/api/merchant/bot/resume');
  },

  /**
   * Get budget recommendation based on cost history
   *
   * @returns Promise with budget recommendation
   */
  async getBudgetRecommendation(): Promise<ApiEnvelope<BudgetRecommendation>> {
    return apiClient.get<BudgetRecommendation>('/api/merchant/budget-recommendation');
  },
};
