/**
 * Unit Tests: Handoff Alerts Store
 *
 * Story 4-6: Handoff Notifications
 * Story 4-7: Handoff Queue with Urgency
 *
 * Tests Zustand store state management for handoff alerts
 *
 * @package frontend/src/stores/test_handoffAlertStore.test.ts
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useHandoffAlertsStore } from './handoffAlertStore';
import { handoffAlertsService } from '../services/handoffAlerts';

vi.mock('../services/handoffAlerts', () => ({
  handoffAlertsService: {
    getAlerts: vi.fn(),
    getQueue: vi.fn(),
    getUnreadCount: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  },
}));

const createMockAlert = (overrides = {}) => ({
  id: 1,
  conversationId: 101,
  urgencyLevel: 'high' as const,
  customerName: 'John Doe',
  customerId: 'cust_001',
  conversationPreview: 'I need help with my order',
  waitTimeSeconds: 300,
  isRead: false,
  createdAt: new Date().toISOString(),
  handoffReason: 'keyword' as const,
  ...overrides,
});

const createMockMeta = (overrides = {}) => ({
  total: 2,
  page: 1,
  limit: 20,
  unreadCount: 1,
  totalWaiting: null as number | null,
  ...overrides,
});

describe('Handoff Alerts Store', () => {
  const mockAlerts = [
    createMockAlert({ id: 1, urgencyLevel: 'high', customerName: 'John Doe' }),
    createMockAlert({ id: 2, urgencyLevel: 'medium', customerName: 'Jane Smith', isRead: true, handoffReason: 'low_confidence' }),
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    useHandoffAlertsStore.getState().reset();
  });

  afterEach(() => {
    useHandoffAlertsStore.getState().stopPolling();
    useHandoffAlertsStore.getState().stopQueuePolling();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useHandoffAlertsStore.getState();

      expect(state.alerts).toEqual([]);
      expect(state.unreadCount).toBe(0);
      expect(state.total).toBe(0);
      expect(state.currentPage).toBe(1);
      expect(state.limit).toBe(20);
      expect(state.urgencyFilter).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.pollingInterval).toBeNull();
      expect(state.queue.items).toEqual([]);
      expect(state.queue.filter).toBe('all');
      expect(state.queuePollingInterval).toBeNull();
    });
  });

  describe('fetchAlerts', () => {
    it('should fetch alerts successfully', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValueOnce({
        data: mockAlerts,
        meta: createMockMeta(),
      });

      const { fetchAlerts } = useHandoffAlertsStore.getState();
      await fetchAlerts();

      const state = useHandoffAlertsStore.getState();
      expect(state.alerts).toEqual(mockAlerts);
      expect(state.total).toBe(2);
      expect(state.unreadCount).toBe(1);
      expect(state.currentPage).toBe(1);
      expect(state.loadingState).toBe('success');
      expect(state.error).toBeNull();
    });

    it('should fetch alerts with specific page', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValueOnce({
        data: mockAlerts,
        meta: createMockMeta({ total: 10, page: 2, unreadCount: 3 }),
      });

      const { fetchAlerts } = useHandoffAlertsStore.getState();
      await fetchAlerts(2);

      const state = useHandoffAlertsStore.getState();
      expect(state.currentPage).toBe(2);
      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(2, 20, undefined);
    });

    it('should fetch alerts with urgency filter', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValueOnce({
        data: [mockAlerts[0]],
        meta: createMockMeta({ total: 1, unreadCount: 1 }),
      });

      const { fetchAlerts } = useHandoffAlertsStore.getState();
      await fetchAlerts(1, 'high');

      const state = useHandoffAlertsStore.getState();
      expect(state.urgencyFilter).toBe('high');
      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(1, 20, 'high');
    });

    it('should handle fetch error', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockRejectedValueOnce(
        new Error('Network error')
      );

      const { fetchAlerts } = useHandoffAlertsStore.getState();
      await fetchAlerts();

      const state = useHandoffAlertsStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Network error');
    });

    it('should set loading state during fetch', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  data: [],
                  meta: createMockMeta({ total: 0, unreadCount: 0 }),
                }),
              100
            )
          )
      );

      const { fetchAlerts } = useHandoffAlertsStore.getState();
      const promise = fetchAlerts();

      expect(useHandoffAlertsStore.getState().loadingState).toBe('loading');

      await promise;

      expect(useHandoffAlertsStore.getState().loadingState).toBe('success');
    });
  });

  describe('fetchUnreadCount', () => {
    it('should fetch unread count successfully', async () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValueOnce({
        unreadCount: 5,
      });

      const { fetchUnreadCount } = useHandoffAlertsStore.getState();
      await fetchUnreadCount();

      const state = useHandoffAlertsStore.getState();
      expect(state.unreadCount).toBe(5);
    });

    it('should handle unread count fetch error silently', async () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockRejectedValueOnce(
        new Error('Failed to fetch')
      );

      const { fetchUnreadCount } = useHandoffAlertsStore.getState();
      await fetchUnreadCount();

      const state = useHandoffAlertsStore.getState();
      expect(state.unreadCount).toBe(0);
    });
  });

  describe('markAsRead', () => {
    beforeEach(async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValueOnce({
        data: mockAlerts,
        meta: createMockMeta(),
      });

      await useHandoffAlertsStore.getState().fetchAlerts();
    });

    it('should mark alert as read and update local state', async () => {
      vi.mocked(handoffAlertsService.markAsRead).mockResolvedValueOnce({
        success: true,
        alertId: 1,
      });

      const { markAsRead } = useHandoffAlertsStore.getState();
      await markAsRead(1);

      const state = useHandoffAlertsStore.getState();
      const alert = state.alerts.find((a) => a.id === 1);
      expect(alert?.isRead).toBe(true);
      expect(state.unreadCount).toBe(0);
    });

    it('should not decrement unread count below 0', async () => {
      useHandoffAlertsStore.setState({ unreadCount: 0 });

      vi.mocked(handoffAlertsService.markAsRead).mockResolvedValueOnce({
        success: true,
        alertId: 1,
      });

      const { markAsRead } = useHandoffAlertsStore.getState();
      await markAsRead(1);

      const state = useHandoffAlertsStore.getState();
      expect(state.unreadCount).toBe(0);
    });

    it('should handle mark as read error', async () => {
      vi.mocked(handoffAlertsService.markAsRead).mockRejectedValueOnce(
        new Error('Failed to mark as read')
      );

      const { markAsRead } = useHandoffAlertsStore.getState();
      await markAsRead(1);

      const state = useHandoffAlertsStore.getState();
      expect(state.error).toBe('Failed to mark as read');
    });
  });

  describe('markAllAsRead', () => {
    beforeEach(async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValueOnce({
        data: mockAlerts,
        meta: createMockMeta(),
      });

      await useHandoffAlertsStore.getState().fetchAlerts();
    });

    it('should mark all alerts as read', async () => {
      vi.mocked(handoffAlertsService.markAllAsRead).mockResolvedValueOnce({
        success: true,
        updatedCount: 1,
      });

      const { markAllAsRead } = useHandoffAlertsStore.getState();
      await markAllAsRead();

      const state = useHandoffAlertsStore.getState();
      expect(state.alerts.every((a) => a.isRead)).toBe(true);
      expect(state.unreadCount).toBe(0);
    });

    it('should handle mark all as read error', async () => {
      vi.mocked(handoffAlertsService.markAllAsRead).mockRejectedValueOnce(
        new Error('Failed to mark all as read')
      );

      const { markAllAsRead } = useHandoffAlertsStore.getState();
      await markAllAsRead();

      const state = useHandoffAlertsStore.getState();
      expect(state.error).toBe('Failed to mark all as read');
    });
  });

  describe('Pagination', () => {
    it('should set page and fetch alerts', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, page: 3, unreadCount: 0 }),
      });

      const { setPage } = useHandoffAlertsStore.getState();
      await setPage(3);

      const state = useHandoffAlertsStore.getState();
      expect(state.currentPage).toBe(3);
      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(3, 20, undefined);
    });

    it('should set limit and refetch from page 1', async () => {
      useHandoffAlertsStore.setState({ currentPage: 5 });

      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, page: 1, limit: 50, unreadCount: 0 }),
      });

      const { setLimit } = useHandoffAlertsStore.getState();
      await setLimit(50);

      const state = useHandoffAlertsStore.getState();
      expect(state.limit).toBe(50);
      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(1, 50, undefined);
    });
  });

  describe('Filtering', () => {
    it('should set urgency filter and refetch', async () => {
      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, unreadCount: 0 }),
      });

      const { setUrgencyFilter } = useHandoffAlertsStore.getState();
      await setUrgencyFilter('high');

      const state = useHandoffAlertsStore.getState();
      expect(state.urgencyFilter).toBe('high');
      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(1, 20, 'high');
    });

    it('should set urgency filter to null (uses existing filter due to ?? operator)', async () => {
      useHandoffAlertsStore.setState({ urgencyFilter: 'high' });

      vi.mocked(handoffAlertsService.getAlerts).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, unreadCount: 0 }),
      });

      const { setUrgencyFilter } = useHandoffAlertsStore.getState();
      await setUrgencyFilter(null);

      expect(handoffAlertsService.getAlerts).toHaveBeenCalledWith(1, 20, 'high');
    });
  });

  describe('Queue (Story 4-7)', () => {
    const mockQueueAlerts = [
      createMockAlert({ id: 10, urgencyLevel: 'high', waitTimeSeconds: 600 }),
      createMockAlert({ id: 11, urgencyLevel: 'medium', waitTimeSeconds: 300 }),
      createMockAlert({ id: 12, urgencyLevel: 'low', waitTimeSeconds: 120 }),
    ];

    it('should fetch queue successfully', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValueOnce({
        data: mockQueueAlerts,
        meta: createMockMeta({ total: 3, totalWaiting: 3, unreadCount: 2 }),
      });

      const { fetchQueue } = useHandoffAlertsStore.getState();
      await fetchQueue();

      const state = useHandoffAlertsStore.getState();
      expect(state.queue.items).toEqual(mockQueueAlerts);
      expect(state.queue.meta.total).toBe(3);
      expect(state.queue.meta.totalWaiting).toBe(3);
      expect(state.queue.isLoading).toBe(false);
    });

    it('should fetch queue with urgency filter', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValueOnce({
        data: [mockQueueAlerts[0]],
        meta: createMockMeta({ total: 1, totalWaiting: 1, unreadCount: 1 }),
      });

      const { fetchQueue } = useHandoffAlertsStore.getState();
      await fetchQueue(1, 'high');

      const state = useHandoffAlertsStore.getState();
      expect(state.queue.filter).toBe('high');
      expect(handoffAlertsService.getQueue).toHaveBeenCalledWith({
        page: 1,
        limit: 20,
        urgency: 'high',
      });
    });

    it('should set queue filter and refetch', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, totalWaiting: 0, unreadCount: 0 }),
      });

      const { setQueueFilter } = useHandoffAlertsStore.getState();
      await setQueueFilter('medium');

      const state = useHandoffAlertsStore.getState();
      expect(state.queue.filter).toBe('medium');
    });

    it('should set queue page and refetch', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 50, totalWaiting: 50, unreadCount: 10 }),
      });

      const { setQueuePage } = useHandoffAlertsStore.getState();
      await setQueuePage(2);

      const state = useHandoffAlertsStore.getState();
      expect(state.queue.currentPage).toBe(2);
    });

    it('should handle queue fetch error', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockRejectedValueOnce(
        new Error('Queue fetch failed')
      );

      const { fetchQueue } = useHandoffAlertsStore.getState();
      await fetchQueue();

      const state = useHandoffAlertsStore.getState();
      expect(state.error).toBe('Queue fetch failed');
      expect(state.queue.isLoading).toBe(false);
    });

    it('should update queue items when markAsRead is called', async () => {
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValueOnce({
        data: mockQueueAlerts,
        meta: createMockMeta({ total: 3, totalWaiting: 3, unreadCount: 3 }),
      });

      const { fetchQueue } = useHandoffAlertsStore.getState();
      await fetchQueue();

      vi.mocked(handoffAlertsService.markAsRead).mockResolvedValueOnce({
        success: true,
        alertId: 10,
      });

      const { markAsRead } = useHandoffAlertsStore.getState();
      await markAsRead(10);

      const state = useHandoffAlertsStore.getState();
      const queueAlert = state.queue.items.find((a) => a.id === 10);
      expect(queueAlert?.isRead).toBe(true);
    });

    describe('Queue Polling', () => {
      beforeEach(() => {
        vi.useFakeTimers();
      });

      afterEach(() => {
        vi.useRealTimers();
      });

      it('should start queue polling', () => {
        vi.mocked(handoffAlertsService.getQueue).mockResolvedValue({
          data: [],
          meta: createMockMeta({ total: 0, totalWaiting: 0, unreadCount: 0 }),
        });

        const { startQueuePolling } = useHandoffAlertsStore.getState();
        startQueuePolling(30000);

        expect(useHandoffAlertsStore.getState().queuePollingInterval).not.toBeNull();
      });

      it('should stop queue polling', () => {
        vi.mocked(handoffAlertsService.getQueue).mockResolvedValue({
          data: [],
          meta: createMockMeta({ total: 0, totalWaiting: 0, unreadCount: 0 }),
        });

        const { startQueuePolling, stopQueuePolling } = useHandoffAlertsStore.getState();
        startQueuePolling();
        expect(useHandoffAlertsStore.getState().queuePollingInterval).not.toBeNull();

        stopQueuePolling();
        expect(useHandoffAlertsStore.getState().queuePollingInterval).toBeNull();
      });
    });
  });

  describe('Polling', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should start polling with default interval', () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 0,
      });

      const { startPolling } = useHandoffAlertsStore.getState();
      startPolling();

      const state = useHandoffAlertsStore.getState();
      expect(state.pollingInterval).not.toBeNull();
      expect(handoffAlertsService.getUnreadCount).toHaveBeenCalledTimes(1);
    });

    it('should start polling with custom interval', () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 0,
      });

      const { startPolling } = useHandoffAlertsStore.getState();
      startPolling(10000);

      vi.advanceTimersByTime(10000);
      expect(handoffAlertsService.getUnreadCount).toHaveBeenCalledTimes(2);
    });

    it('should fetch unread count immediately on start', async () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 5,
      });

      const { startPolling } = useHandoffAlertsStore.getState();
      startPolling();

      await vi.waitFor(() => {
        expect(useHandoffAlertsStore.getState().unreadCount).toBe(5);
      });
    });

    it('should stop polling', () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 0,
      });

      const { startPolling, stopPolling } = useHandoffAlertsStore.getState();
      startPolling();

      expect(useHandoffAlertsStore.getState().pollingInterval).not.toBeNull();

      stopPolling();

      expect(useHandoffAlertsStore.getState().pollingInterval).toBeNull();
    });

    it('should replace existing polling interval', () => {
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 0,
      });

      const { startPolling } = useHandoffAlertsStore.getState();
      startPolling(30000);
      const firstInterval = useHandoffAlertsStore.getState().pollingInterval;

      startPolling(10000);
      const secondInterval = useHandoffAlertsStore.getState().pollingInterval;

      expect(firstInterval).not.toBe(secondInterval);
    });
  });

  describe('Utility Actions', () => {
    it('should clear error', () => {
      useHandoffAlertsStore.setState({ error: 'Some error' });

      const { clearError } = useHandoffAlertsStore.getState();
      clearError();

      expect(useHandoffAlertsStore.getState().error).toBeNull();
    });

    it('should reset store to initial state', () => {
      useHandoffAlertsStore.setState({
        alerts: mockAlerts,
        unreadCount: 5,
        total: 10,
        currentPage: 3,
        loadingState: 'success',
        error: 'error',
      });

      const { reset } = useHandoffAlertsStore.getState();
      reset();

      const state = useHandoffAlertsStore.getState();
      expect(state.alerts).toEqual([]);
      expect(state.unreadCount).toBe(0);
      expect(state.total).toBe(0);
      expect(state.currentPage).toBe(1);
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
    });

    it('should stop polling on reset', () => {
      vi.useFakeTimers();
      vi.mocked(handoffAlertsService.getUnreadCount).mockResolvedValue({
        unreadCount: 0,
      });

      const { startPolling } = useHandoffAlertsStore.getState();
      startPolling();
      expect(useHandoffAlertsStore.getState().pollingInterval).not.toBeNull();

      const { reset } = useHandoffAlertsStore.getState();
      reset();

      expect(useHandoffAlertsStore.getState().pollingInterval).toBeNull();

      vi.useRealTimers();
    });

    it('should stop queue polling on reset', () => {
      vi.useFakeTimers();
      vi.mocked(handoffAlertsService.getQueue).mockResolvedValue({
        data: [],
        meta: createMockMeta({ total: 0, totalWaiting: 0, unreadCount: 0 }),
      });

      const { startQueuePolling } = useHandoffAlertsStore.getState();
      startQueuePolling();
      expect(useHandoffAlertsStore.getState().queuePollingInterval).not.toBeNull();

      const { reset } = useHandoffAlertsStore.getState();
      reset();

      expect(useHandoffAlertsStore.getState().queuePollingInterval).toBeNull();

      vi.useRealTimers();
    });
  });
});
