/**
 * HandoffQueue Page Tests - Story 4-7
 *
 * Tests handoff queue functionality including:
 * - Queue display with sorting (urgency DESC, wait_time DESC)
 * - Urgency filter tabs
 * - Total waiting count
 * - Pagination
 * - Mark as read functionality
 * - Loading and error states
 *
 * Acceptance Criteria Coverage:
 * - AC1: Sort by Urgency then Wait Time
 * - AC2: Handoff Display Details (customer, urgency badge, wait time, preview, reason)
 * - AC3: Filter by Urgency
 * - AC4: Total Waiting Count
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HandoffQueue from './HandoffQueue';
import { useHandoffAlertsStore, type QueueUrgencyFilter } from '../stores/handoffAlertStore';
import type { HandoffAlert } from '../services/handoffAlerts';

vi.mock('../stores/handoffAlertStore', () => ({
  useHandoffAlertsStore: vi.fn(),
}));

const mockUseHandoffAlertsStore = vi.mocked(useHandoffAlertsStore);

const createMockAlert = (overrides: Partial<HandoffAlert> = {}): HandoffAlert => ({
  id: 1,
  conversationId: 'conv-001',
  customerId: 101,
  customerName: 'John Doe',
  urgencyLevel: 'high',
  waitTimeSeconds: 300,
  handoffReason: 'keyword',
  conversationPreview: 'I need help with my order',
  isRead: false,
  createdAt: '2026-02-15T10:00:00Z',
  ...overrides,
});

const mockFetchQueue = vi.fn();
const mockSetQueueFilter = vi.fn();
const mockSetQueuePage = vi.fn();
const mockMarkAsRead = vi.fn();
const mockStartQueuePolling = vi.fn();
const mockStopQueuePolling = vi.fn();
const mockClearError = vi.fn();

const defaultStoreState = {
  queue: {
    items: [] as HandoffAlert[],
    isLoading: false,
    filter: 'all' as QueueUrgencyFilter,
    currentPage: 1,
    meta: {
      total: 0,
      page: 1,
      limit: 20,
      totalWaiting: null as number | null,
    },
  },
  notifications: {
    items: [],
    isLoading: false,
    unreadCount: 0,
  },
  error: null as string | null,
  fetchQueue: mockFetchQueue,
  setQueueFilter: mockSetQueueFilter,
  setQueuePage: mockSetQueuePage,
  markAsRead: mockMarkAsRead,
  startQueuePolling: mockStartQueuePolling,
  stopQueuePolling: mockStopQueuePolling,
  clearError: mockClearError,
};

describe('HandoffQueue Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockUseHandoffAlertsStore.mockReturnValue(defaultStoreState);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Initial Render', () => {
    it('displays page title', () => {
      render(<HandoffQueue />);

      expect(screen.getByText('Handoff Queue')).toBeInTheDocument();
    });

    it('displays page description', () => {
      render(<HandoffQueue />);

      expect(screen.getByText('Active handoff conversations sorted by urgency')).toBeInTheDocument();
    });

    it('fetches queue on mount', () => {
      render(<HandoffQueue />);

      expect(mockFetchQueue).toHaveBeenCalledTimes(1);
    });

    it('starts polling on mount', () => {
      render(<HandoffQueue />);

      expect(mockStartQueuePolling).toHaveBeenCalledWith(30000);
    });

    it('stops polling on unmount', () => {
      const { unmount } = render(<HandoffQueue />);
      unmount();

      expect(mockStopQueuePolling).toHaveBeenCalled();
    });
  });

  describe('Total Waiting Count (AC4)', () => {
    it('displays total waiting count when available', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 5 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('5 customers waiting')).toBeInTheDocument();
    });

    it('displays singular customer when count is 1', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('1 customer waiting')).toBeInTheDocument();
    });

    it('hides waiting count when null', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: null },
        },
      });

      render(<HandoffQueue />);

      expect(screen.queryByTestId('total-waiting-count')).not.toBeInTheDocument();
    });
  });

  describe('Urgency Filter Tabs (AC3)', () => {
    it('displays all filter tabs', () => {
      render(<HandoffQueue />);

      expect(screen.getByTestId('filter-all')).toBeInTheDocument();
      expect(screen.getByTestId('filter-high')).toBeInTheDocument();
      expect(screen.getByTestId('filter-medium')).toBeInTheDocument();
      expect(screen.getByTestId('filter-low')).toBeInTheDocument();
    });

    it('displays urgency emoji indicators', () => {
      render(<HandoffQueue />);

      expect(screen.getByTestId('filter-high')).toHaveTextContent('🔴');
      expect(screen.getByTestId('filter-medium')).toHaveTextContent('🟡');
      expect(screen.getByTestId('filter-low')).toHaveTextContent('🟢');
    });

    it('calls setQueueFilter when filter tab clicked', async () => {
      const user = userEvent.setup({ delay: null });

      render(<HandoffQueue />);

      await user.click(screen.getByTestId('filter-high'));

      expect(mockSetQueueFilter).toHaveBeenCalledWith('high');
    });

    it('highlights active filter tab', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          filter: 'high',
        },
      });

      render(<HandoffQueue />);

      const highTab = screen.getByTestId('filter-high');
      expect(highTab).toHaveClass('border-blue-500');
    });
  });

  describe('Queue Items Display (AC1, AC2)', () => {
    const mockAlerts: HandoffAlert[] = [
      createMockAlert({ id: 1, urgencyLevel: 'high', waitTimeSeconds: 600, customerName: 'Alice Smith' }),
      createMockAlert({ id: 2, urgencyLevel: 'medium', waitTimeSeconds: 300, customerName: 'Bob Jones' }),
      createMockAlert({ id: 3, urgencyLevel: 'low', waitTimeSeconds: 120, customerName: 'Carol White' }),
    ];

    it('displays queue items when data exists', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: mockAlerts,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 3 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getAllByTestId('queue-item')).toHaveLength(3);
    });

    it('displays urgency badge for each item', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: mockAlerts,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 3 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('🔴 High')).toBeInTheDocument();
      expect(screen.getByText('🟡 Medium')).toBeInTheDocument();
      expect(screen.getByText('🟢 Low')).toBeInTheDocument();
    });

    it('displays customer name for each item', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: mockAlerts,
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 3 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
      expect(screen.getByText('Bob Jones')).toBeInTheDocument();
      expect(screen.getByText('Carol White')).toBeInTheDocument();
    });

    it('displays formatted wait time', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ waitTimeSeconds: 600 })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('10m')).toBeInTheDocument();
    });

    it('formats hours correctly', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ waitTimeSeconds: 3661 })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('1h 1m')).toBeInTheDocument();
    });

    it('displays handoff reason when available', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ handoffReason: 'keyword' })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText(/Keyword Trigger/)).toBeInTheDocument();
    });

    it('displays conversation preview when available', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ conversationPreview: 'I need help with my order #12345' })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('I need help with my order #12345')).toBeInTheDocument();
    });

    it('displays fallback customer name when name is null', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ customerName: null, customerId: 999 })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Customer 999')).toBeInTheDocument();
    });
  });

  describe('Mark as Read', () => {
    it('displays mark as read button for unread items', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ isRead: false })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('item-mark-read')).toBeInTheDocument();
    });

    it('hides mark as read button for read items', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ isRead: true })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.queryByTestId('item-mark-read')).not.toBeInTheDocument();
    });

    it('calls markAsRead when button clicked', async () => {
      const user = userEvent.setup({ delay: null });
      mockMarkAsRead.mockResolvedValue(undefined);

      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert({ id: 42, isRead: false })],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 1 },
        },
      });

      render(<HandoffQueue />);

      await user.click(screen.getByTestId('item-mark-read'));

      expect(mockMarkAsRead).toHaveBeenCalledWith(42);
    });
  });

  describe('Loading State', () => {
    it('displays loading message while fetching', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          isLoading: true,
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Loading queue...')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no items', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 0 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('queue-empty-state')).toBeInTheDocument();
      expect(screen.getByText('No active handoffs in the queue')).toBeInTheDocument();
    });

    it('displays helpful message in empty state', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [],
          meta: { ...defaultStoreState.queue.meta, totalWaiting: 0 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Customers needing assistance will appear here')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error message when error exists', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        error: 'Failed to load queue',
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Failed to load queue')).toBeInTheDocument();
    });

    it('displays dismiss button for error', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        error: 'Failed to load queue',
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Dismiss')).toBeInTheDocument();
    });

    it('calls clearError when dismiss clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        error: 'Failed to load queue',
      });

      render(<HandoffQueue />);

      await user.click(screen.getByText('Dismiss'));

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('Pagination', () => {
    it('hides pagination when total <= limit', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          meta: { ...defaultStoreState.queue.meta, total: 10 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.queryByTestId('pagination')).not.toBeInTheDocument();
    });

    it('displays pagination when total > limit', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 1, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });

    it('displays page info', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 2,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 2, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByText('Page 2 of 3')).toBeInTheDocument();
    });

    it('disables prev button on first page', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 1,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 1, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('pagination-prev')).toBeDisabled();
    });

    it('enables prev button on page 2', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 2,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 2, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('pagination-prev')).toBeEnabled();
    });

    it('disables next button on last page', () => {
      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 3,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 3, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      expect(screen.getByTestId('pagination-next')).toBeDisabled();
    });

    it('calls setQueuePage when next clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 1,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 1, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      await user.click(screen.getByTestId('pagination-next'));

      expect(mockSetQueuePage).toHaveBeenCalledWith(2);
    });

    it('calls setQueuePage when prev clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseHandoffAlertsStore.mockReturnValue({
        ...defaultStoreState,
        queue: {
          ...defaultStoreState.queue,
          items: [createMockAlert()],
          currentPage: 2,
          meta: { ...defaultStoreState.queue.meta, total: 50, page: 2, limit: 20 },
        },
      });

      render(<HandoffQueue />);

      await user.click(screen.getByTestId('pagination-prev'));

      expect(mockSetQueuePage).toHaveBeenCalledWith(1);
    });
  });
});
