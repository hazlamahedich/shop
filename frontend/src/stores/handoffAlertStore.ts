/**
 * Handoff Alerts Store - Zustand state management for handoff notifications
 *
 * Story 4-6: Handoff Notifications
 * Story 4-7: Handoff Queue with Urgency
 *
 * Handles alert fetching, unread count, marking as read, and queue management
 */

import { create } from 'zustand';
import {
  handoffAlertsService,
  type HandoffAlert,
  type UrgencyLevel,
} from '../services/handoffAlerts';

const DEBUG = import.meta.env.DEV;

type LoadingState = 'idle' | 'loading' | 'success' | 'error';
type QueueUrgencyFilter = UrgencyLevel | 'all';

export interface HandoffAlertsState {
  // Notifications data
  alerts: HandoffAlert[];
  unreadCount: number;
  total: number;

  // Pagination (notifications)
  currentPage: number;
  limit: number;

  // Filter (notifications)
  urgencyFilter: UrgencyLevel | null;

  // Queue state (Story 4-7)
  queue: {
    items: HandoffAlert[];
    meta: {
      total: number;
      totalWaiting: number | null;
    };
    isLoading: boolean;
    filter: QueueUrgencyFilter;
    currentPage: number;
  };

  // UI state
  loadingState: LoadingState;
  error: string | null;

  // Polling
  pollingInterval: ReturnType<typeof setInterval> | null;
  queuePollingInterval: ReturnType<typeof setInterval> | null;

  // Actions - Notifications
  fetchAlerts: (page?: number, urgency?: UrgencyLevel | null) => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (alertId: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;

  // Actions - Queue (Story 4-7)
  fetchQueue: (page?: number, filter?: QueueUrgencyFilter) => Promise<void>;
  setQueueFilter: (filter: QueueUrgencyFilter) => Promise<void>;
  setQueuePage: (page: number) => Promise<void>;

  // Actions - Pagination (notifications)
  setPage: (page: number) => Promise<void>;
  setLimit: (limit: number) => Promise<void>;

  // Actions - Filter (notifications)
  setUrgencyFilter: (urgency: UrgencyLevel | null) => Promise<void>;

  // Actions - Polling
  startPolling: (intervalMs?: number) => void;
  stopPolling: () => void;
  startQueuePolling: (intervalMs?: number) => void;
  stopQueuePolling: () => void;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
}

const initialQueueState = {
  items: [],
  meta: {
    total: 0,
    totalWaiting: null,
  },
  isLoading: false,
  filter: 'all' as QueueUrgencyFilter,
  currentPage: 1,
};

const initialState = {
  alerts: [],
  unreadCount: 0,
  total: 0,
  currentPage: 1,
  limit: 20,
  urgencyFilter: null as UrgencyLevel | null,
  queue: initialQueueState,
  loadingState: 'idle' as LoadingState,
  error: null as string | null,
  pollingInterval: null as ReturnType<typeof setInterval> | null,
  queuePollingInterval: null as ReturnType<typeof setInterval> | null,
};

export const useHandoffAlertsStore = create<HandoffAlertsState>((set, get) => ({
  ...initialState,

  fetchAlerts: async (page?: number, urgency?: UrgencyLevel | null) => {
    const state = get();
    const targetPage = page ?? state.currentPage;
    const targetUrgency = urgency ?? state.urgencyFilter;

    set({ loadingState: 'loading', error: null });

    try {
      const response = await handoffAlertsService.getAlerts(
        targetPage,
        state.limit,
        targetUrgency ?? undefined
      );

      if (DEBUG) console.log('[HandoffAlerts] Fetched alerts:', response.data.length, 'total:', response.meta.total, 'unread:', response.meta.unreadCount);

      set({
        alerts: response.data,
        total: response.meta.total,
        unreadCount: response.meta.unreadCount,
        currentPage: targetPage,
        urgencyFilter: targetUrgency,
        loadingState: 'success',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch alerts';
      if (DEBUG) console.error('[HandoffAlerts] Fetch error:', message);
      set({ error: message, loadingState: 'error' });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const response = await handoffAlertsService.getUnreadCount();
      if (DEBUG) console.log('[HandoffAlerts] Fetched unread count:', response.unreadCount);
      set({ unreadCount: response.unreadCount });
    } catch (error) {
      if (DEBUG) console.error('[HandoffAlerts] Failed to fetch unread count:', error);
    }
  },

  markAsRead: async (alertId: number) => {
    try {
      await handoffAlertsService.markAsRead(alertId);

      // Update local state for notifications
      const state = get();
      const updatedAlerts = state.alerts.map((alert) =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      );

      // Update local state for queue (item stays but is marked read)
      const updatedQueueItems = state.queue.items.map((alert) =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      );

      const newUnreadCount = Math.max(0, state.unreadCount - 1);

      set({
        alerts: updatedAlerts,
        queue: { ...state.queue, items: updatedQueueItems },
        unreadCount: newUnreadCount,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to mark alert as read';
      set({ error: message });
    }
  },

  markAllAsRead: async () => {
    try {
      const response = await handoffAlertsService.markAllAsRead();

      // Update local state
      const state = get();
      const updatedAlerts = state.alerts.map((alert) => ({ ...alert, isRead: true }));
      const updatedQueueItems = state.queue.items.map((alert) => ({ ...alert, isRead: true }));

      set({
        alerts: updatedAlerts,
        queue: { ...state.queue, items: updatedQueueItems },
        unreadCount: 0,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to mark all alerts as read';
      set({ error: message });
    }
  },

  // Queue actions (Story 4-7)
  fetchQueue: async (page?: number, filter?: QueueUrgencyFilter) => {
    const state = get();
    const targetPage = page ?? state.queue.currentPage;
    const targetFilter = filter ?? state.queue.filter;

    set({ queue: { ...state.queue, isLoading: true } });

    try {
      const urgencyParam = targetFilter === 'all' ? undefined : targetFilter;
      const response = await handoffAlertsService.getQueue({
        page: targetPage,
        limit: 20,
        urgency: urgencyParam,
      });

      if (DEBUG) console.log('[HandoffQueue] Fetched queue:', response.data.length, 'total:', response.meta.total, 'waiting:', response.meta.totalWaiting);

      set({
        queue: {
          items: response.data,
          meta: {
            total: response.meta.total,
            totalWaiting: response.meta.totalWaiting,
          },
          isLoading: false,
          filter: targetFilter,
          currentPage: targetPage,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch queue';
      if (DEBUG) console.error('[HandoffQueue] Fetch error:', message);
      set({ error: message, queue: { ...get().queue, isLoading: false } });
    }
  },

  setQueueFilter: async (filter: QueueUrgencyFilter) => {
    await get().fetchQueue(1, filter);
  },

  setQueuePage: async (page: number) => {
    const state = get();
    await get().fetchQueue(page, state.queue.filter);
  },

  setPage: async (page: number) => {
    const state = get();
    await state.fetchAlerts(page);
  },

  setLimit: async (limit: number) => {
    set({ limit });
    const state = get();
    await state.fetchAlerts(1);
  },

  setUrgencyFilter: async (urgency: UrgencyLevel | null) => {
    const state = get();
    await state.fetchAlerts(1, urgency);
  },

  startPolling: (intervalMs = 30000) => {
    const state = get();

    // Stop any existing polling
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
    }

    // Start new polling
    const interval = setInterval(() => {
      get().fetchUnreadCount();
    }, intervalMs);

    set({ pollingInterval: interval });

    // Also fetch immediately
    state.fetchUnreadCount();
  },

  stopPolling: () => {
    const state = get();
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
      set({ pollingInterval: null });
    }
  },

  startQueuePolling: (intervalMs = 30000) => {
    const state = get();

    // Stop any existing queue polling
    if (state.queuePollingInterval) {
      clearInterval(state.queuePollingInterval);
    }

    // Start new polling
    const interval = setInterval(() => {
      const currentState = get();
      currentState.fetchQueue(currentState.queue.currentPage, currentState.queue.filter);
    }, intervalMs);

    set({ queuePollingInterval: interval });
  },

  stopQueuePolling: () => {
    const state = get();
    if (state.queuePollingInterval) {
      clearInterval(state.queuePollingInterval);
      set({ queuePollingInterval: null });
    }
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    const state = get();
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
    }
    if (state.queuePollingInterval) {
      clearInterval(state.queuePollingInterval);
    }
    set(initialState);
  },
}));
