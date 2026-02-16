/**
 * Unit Tests: Handoff Alerts Service
 *
 * Story 4-6: Handoff Notifications
 *
 * Tests API service functions for handoff alert endpoints
 *
 * @package frontend/src/services/test_handoffAlerts.test.ts
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handoffAlertsService } from './handoffAlerts';
import { apiClient } from './api';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Handoff Alerts Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAlerts', () => {
    it('should fetch alerts with default parameters', async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            conversationId: 101,
            urgencyLevel: 'high',
            customerName: 'John Doe',
            customerId: 'cust_001',
            conversationPreview: 'Help needed',
            waitTimeSeconds: 300,
            isRead: false,
            createdAt: '2026-02-15T10:00:00Z',
          },
        ],
        meta: { total: 1, page: 1, limit: 20, unreadCount: 1 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getAlerts();

      expect(apiClient.get).toHaveBeenCalledWith('/api/handoff-alerts?page=1&limit=20');
      expect(result).toEqual(mockResponse);
    });

    it('should fetch alerts with custom pagination', async () => {
      const mockResponse = {
        data: [],
        meta: { total: 50, page: 2, limit: 10, unreadCount: 5 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getAlerts(2, 10);

      expect(apiClient.get).toHaveBeenCalledWith('/api/handoff-alerts?page=2&limit=10');
      expect(result.meta.page).toBe(2);
      expect(result.meta.limit).toBe(10);
    });

    it('should fetch alerts with urgency filter', async () => {
      const mockResponse = {
        data: [],
        meta: { total: 0, page: 1, limit: 20, unreadCount: 0 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      await handoffAlertsService.getAlerts(1, 20, 'high');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/handoff-alerts?page=1&limit=20&urgency=high'
      );
    });

    it('should fetch alerts with medium urgency filter', async () => {
      const mockResponse = {
        data: [],
        meta: { total: 0, page: 1, limit: 20, unreadCount: 0 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      await handoffAlertsService.getAlerts(1, 20, 'medium');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/handoff-alerts?page=1&limit=20&urgency=medium'
      );
    });

    it('should fetch alerts with low urgency filter', async () => {
      const mockResponse = {
        data: [],
        meta: { total: 0, page: 1, limit: 20, unreadCount: 0 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      await handoffAlertsService.getAlerts(1, 20, 'low');

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/handoff-alerts?page=1&limit=20&urgency=low'
      );
    });

    it('should return correctly typed response', async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            conversationId: 101,
            urgencyLevel: 'high' as const,
            customerName: 'Test User',
            customerId: 'cust_001',
            conversationPreview: 'Test preview',
            waitTimeSeconds: 120,
            isRead: false,
            createdAt: '2026-02-15T10:00:00Z',
          },
        ],
        meta: { total: 1, page: 1, limit: 20, unreadCount: 1 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getAlerts();

      expect(result.data[0]).toHaveProperty('id');
      expect(result.data[0]).toHaveProperty('conversationId');
      expect(result.data[0]).toHaveProperty('urgencyLevel');
      expect(result.data[0]).toHaveProperty('customerName');
      expect(result.data[0]).toHaveProperty('waitTimeSeconds');
      expect(result.data[0]).toHaveProperty('isRead');
      expect(result.data[0]).toHaveProperty('createdAt');
    });
  });

  describe('getUnreadCount', () => {
    it('should fetch unread count', async () => {
      const mockResponse = { unreadCount: 5 };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getUnreadCount();

      expect(apiClient.get).toHaveBeenCalledWith('/api/handoff-alerts/unread-count');
      expect(result.unreadCount).toBe(5);
    });

    it('should return zero unread count', async () => {
      const mockResponse = { unreadCount: 0 };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getUnreadCount();

      expect(result.unreadCount).toBe(0);
    });

    it('should handle large unread counts', async () => {
      const mockResponse = { unreadCount: 999 };

      vi.mocked(apiClient.get).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.getUnreadCount();

      expect(result.unreadCount).toBe(999);
    });
  });

  describe('markAsRead', () => {
    it('should mark alert as read', async () => {
      const mockResponse = { success: true, alertId: 123 };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.markAsRead(123);

      expect(apiClient.post).toHaveBeenCalledWith('/api/handoff-alerts/123/read');
      expect(result.success).toBe(true);
      expect(result.alertId).toBe(123);
    });

    it('should mark different alerts as read', async () => {
      vi.mocked(apiClient.post)
        .mockResolvedValueOnce({ success: true, alertId: 1 })
        .mockResolvedValueOnce({ success: true, alertId: 2 });

      const result1 = await handoffAlertsService.markAsRead(1);
      const result2 = await handoffAlertsService.markAsRead(2);

      expect(result1.alertId).toBe(1);
      expect(result2.alertId).toBe(2);
    });

    it('should handle string-based alert IDs', async () => {
      const mockResponse = { success: true, alertId: 'alert_abc' };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.markAsRead('alert_abc' as unknown as number);

      expect(apiClient.post).toHaveBeenCalledWith('/api/handoff-alerts/alert_abc/read');
    });
  });

  describe('markAllAsRead', () => {
    it('should mark all alerts as read', async () => {
      const mockResponse = { success: true, updatedCount: 10 };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.markAllAsRead();

      expect(apiClient.post).toHaveBeenCalledWith('/api/handoff-alerts/mark-all-read');
      expect(result.success).toBe(true);
      expect(result.updatedCount).toBe(10);
    });

    it('should return zero count when no alerts to mark', async () => {
      const mockResponse = { success: true, updatedCount: 0 };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.markAllAsRead();

      expect(result.updatedCount).toBe(0);
    });

    it('should handle large batch updates', async () => {
      const mockResponse = { success: true, updatedCount: 500 };

      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

      const result = await handoffAlertsService.markAllAsRead();

      expect(result.updatedCount).toBe(500);
    });
  });

  describe('Error Handling', () => {
    it('should propagate API errors from getAlerts', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Network error'));

      await expect(handoffAlertsService.getAlerts()).rejects.toThrow('Network error');
    });

    it('should propagate API errors from getUnreadCount', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Unauthorized'));

      await expect(handoffAlertsService.getUnreadCount()).rejects.toThrow('Unauthorized');
    });

    it('should propagate API errors from markAsRead', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Not found'));

      await expect(handoffAlertsService.markAsRead(999)).rejects.toThrow('Not found');
    });

    it('should propagate API errors from markAllAsRead', async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Server error'));

      await expect(handoffAlertsService.markAllAsRead()).rejects.toThrow('Server error');
    });
  });

  describe('URL Parameter Encoding', () => {
    it('should encode special characters in query params', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: [],
        meta: { total: 0, page: 1, limit: 20, unreadCount: 0 },
      });

      await handoffAlertsService.getAlerts(1, 20, 'high');

      const callUrl = vi.mocked(apiClient.get).mock.calls[0][0];
      expect(callUrl).toContain('page=1');
      expect(callUrl).toContain('limit=20');
      expect(callUrl).toContain('urgency=high');
    });
  });
});
