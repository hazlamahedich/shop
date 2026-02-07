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
