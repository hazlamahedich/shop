/**
 * Conversations API Service
 *
 * Handles API calls for conversation list and pagination
 */

import type {
  ConversationsListParams,
  ConversationsResponse,
} from '../types/conversation';

const API_BASE = '/api/conversations';

/**
 * Conversations service
 */
export const conversationsService = {
  /**
   * Get paginated list of conversations
   *
   * @param params - Query parameters for pagination and sorting
   * @returns Promise with conversations and pagination metadata
   */
  async getConversations(
    params: ConversationsListParams = {}
  ): Promise<ConversationsResponse> {
    const queryParams = new URLSearchParams();

    if (params.page) queryParams.append('page', params.page.toString());
    if (params.perPage) queryParams.append('per_page', params.perPage.toString());
    if (params.sortBy) queryParams.append('sort_by', params.sortBy);
    if (params.sortOrder) queryParams.append('sort_order', params.sortOrder);

    // Search and filter parameters
    if (params.search) queryParams.append('search', params.search);
    if (params.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params.dateTo) queryParams.append('date_to', params.dateTo);
    if (params.status) params.status.forEach((s) => queryParams.append('status', s));
    if (params.sentiment) params.sentiment.forEach((s) => queryParams.append('sentiment', s));
    if (params.hasHandoff !== undefined) queryParams.append('has_handoff', params.hasHandoff.toString());

    const url = queryParams.toString() ? `${API_BASE}?${queryParams}` : API_BASE;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch conversations');
    }

    return response.json();
  },
};
