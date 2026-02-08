/**
 * Cost Tracking API Service
 *
 * Story 3-5: Real-Time Cost Tracking
 *
 * Handles API calls for cost tracking endpoints
 */

import { apiClient } from './api';
import type { ApiEnvelope, ConversationCost, CostSummary, CostSummaryParams } from '../types/cost';

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
   * @param budgetCap - Optional budget cap value to update
   * @returns Promise with updated merchant settings
   */
  async updateSettings(
    budgetCap?: number
  ): Promise<ApiEnvelope<{ budgetCap?: number; config: Record<string, unknown> }>> {
    const body = budgetCap !== undefined ? { budget_cap: budgetCap } : {};

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
};
