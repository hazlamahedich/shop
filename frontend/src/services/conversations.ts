/**
 * Conversations API Service
 *
 * Handles API calls for conversation list and pagination
 */

import type {
  ConversationsListParams,
  ConversationsResponse,
  ConversationHistoryResponse,
  HybridModeRequest,
  HybridModeResponse,
  FacebookPageInfo,
} from '../types/conversation';

import { getCsrfToken } from '../stores/csrfStore';
import { useAuthStore } from '../stores/authStore';

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

  /**
   * Get count of active conversations
   *
   * Used for displaying badge on Conversations navigation.
   *
   * @returns Promise with active conversation count
   */
  async getActiveCount(): Promise<{ activeCount: number }> {
    const response = await fetch(`${API_BASE}/active-count`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch active count');
    }

    return response.json();
  },

  /**
   * Get conversation history with context
   *
   * Story 4-8: Returns full conversation history including messages,
   * bot context, handoff info, and customer info.
   *
   * @param conversationId - ID of the conversation
   * @returns Promise with conversation history data
   */
  async getConversationHistory(conversationId: number): Promise<ConversationHistoryResponse> {
    const response = await fetch(`${API_BASE}/${conversationId}/history`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch conversation history');
    }

    return response.json();
  },

  async setHybridMode(
    conversationId: number,
    request: HybridModeRequest
  ): Promise<HybridModeResponse> {
    const csrfToken = await getCsrfToken();
    const response = await fetch(`${API_BASE}/${conversationId}/hybrid-mode`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update hybrid mode');
    }

    return response.json();
  },

  async getFacebookPageInfo(): Promise<{ data: FacebookPageInfo }> {
    const merchantId = useAuthStore.getState().merchant?.id;
    if (!merchantId) {
      throw new Error('Not authenticated');
    }
    const response = await fetch(`/api/integrations/facebook/status?merchant_id=${merchantId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch Facebook page info');
    }

    const json = await response.json();
    return {
      data: {
        pageId: json.data.pageId || null,
        pageName: json.data.pageName || null,
        isConnected: json.data.connected === true,
      },
    };
  },

  /**
   * Send a merchant reply to a conversation
   *
   * Platform-specific behavior:
   * - Messenger: Sends via Facebook Send API
   * - Widget: Stores and broadcasts via SSE
   * - Preview: Returns error (read-only)
   *
   * @param conversationId - ID of the conversation
   * @param content - Message content to send
   * @returns Promise with the sent message details
   */
  async sendMerchantReply(
    conversationId: number,
    content: string
  ): Promise<{
    data: {
      message: {
        id: number;
        content: string;
        sender: string;
        createdAt: string;
        platform: string;
      };
    };
  }> {
    const csrfToken = await getCsrfToken();
    const response = await fetch(`${API_BASE}/${conversationId}/reply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to send reply');
    }

    return response.json();
  },
};
