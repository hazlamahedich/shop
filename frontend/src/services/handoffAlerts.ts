/**
 * Handoff Alerts API Service
 *
 * Story 4-6: Handoff Notifications
 * Story 4-7: Handoff Queue with Urgency
 *
 * Handles API calls for handoff alert endpoints
 *
 * Note: These endpoints return data directly (not wrapped in envelope)
 */

import { apiClient } from './api';

export type UrgencyLevel = 'high' | 'medium' | 'low';
export type ViewMode = 'notifications' | 'queue';
export type SortBy = 'created_desc' | 'urgency_desc';

export interface HandoffAlert {
  id: number;
  conversationId: number;
  platformSenderId: string | null;
  urgencyLevel: UrgencyLevel;
  customerName: string | null;
  customerId: string | null;
  conversationPreview: string | null;
  waitTimeSeconds: number;
  isRead: boolean;
  isOffline: boolean;
  createdAt: string;
  handoffReason: 'keyword' | 'low_confidence' | 'clarification_loop' | null;
}

export interface HandoffAlertListMeta {
  total: number;
  page: number;
  limit: number;
  unreadCount: number;
  totalWaiting: number | null;
}

export interface HandoffAlertListResponse {
  data: HandoffAlert[];
  meta: HandoffAlertListMeta;
}

export interface UnreadCountResponse {
  unreadCount: number;
}

export interface MarkReadResponse {
  success: boolean;
  alertId: number;
}

export interface MarkAllReadResponse {
  success: boolean;
  updatedCount: number;
}

export interface GetAlertsParams {
  page?: number;
  limit?: number;
  urgency?: UrgencyLevel;
  view?: ViewMode;
  sortBy?: SortBy;
}

/**
 * Handoff alerts service
 */
export const handoffAlertsService = {
  /**
   * List handoff alerts with pagination and filtering
   *
   * @param page - Page number (1-indexed)
   * @param limit - Items per page
   * @param urgency - Optional urgency filter
   * @returns Promise with paginated alerts
   */
  async getAlerts(
    page = 1,
    limit = 20,
    urgency?: UrgencyLevel
  ): Promise<HandoffAlertListResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append('page', String(page));
    queryParams.append('limit', String(limit));

    if (urgency) {
      queryParams.append('urgency', urgency);
    }

    const response = await apiClient.get<HandoffAlertListResponse>(
      `/api/handoff-alerts?${queryParams.toString()}`
    );
    return response as unknown as HandoffAlertListResponse;
  },

  /**
   * Get queue of active handoffs sorted by urgency
   *
   * Story 4-7: Queue view for active handoffs
   *
   * @param params - Query parameters
   * @returns Promise with paginated alerts
   */
  async getQueue(params: GetAlertsParams = {}): Promise<HandoffAlertListResponse> {
    const queryParams = new URLSearchParams();
    queryParams.append('page', String(params.page ?? 1));
    queryParams.append('limit', String(params.limit ?? 20));
    queryParams.append('view', 'queue');
    queryParams.append('sort_by', 'urgency_desc');

    if (params.urgency) {
      queryParams.append('urgency', params.urgency);
    }

    const response = await apiClient.get<HandoffAlertListResponse>(
      `/api/handoff-alerts?${queryParams.toString()}`
    );
    return response as unknown as HandoffAlertListResponse;
  },

  /**
   * Get unread count for dashboard badge
   *
   * @returns Promise with unread count
   */
  async getUnreadCount(): Promise<UnreadCountResponse> {
    const response = await apiClient.get<UnreadCountResponse>(
      '/api/handoff-alerts/unread-count'
    );
    return response as unknown as UnreadCountResponse;
  },

  /**
   * Mark a single alert as read
   *
   * @param alertId - Alert ID to mark as read
   * @returns Promise with success status
   */
  async markAsRead(alertId: number): Promise<MarkReadResponse> {
    const response = await apiClient.post<MarkReadResponse>(
      `/api/handoff-alerts/${alertId}/read`
    );
    return response as unknown as MarkReadResponse;
  },

  /**
   * Mark all alerts as read for the current merchant
   *
   * @returns Promise with updated count
   */
  async markAllAsRead(): Promise<MarkAllReadResponse> {
    const response = await apiClient.post<MarkAllReadResponse>(
      '/api/handoff-alerts/mark-all-read'
    );
    return response as unknown as MarkAllReadResponse;
  },
};
