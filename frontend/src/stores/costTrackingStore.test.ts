/**
 * Cost Tracking Store Tests
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useCostTrackingStore,
  useCostTrackingPolling,
  _clearPollingTimer,
} from './costTrackingStore';
import type { ConversationCost, CostSummary } from '../types/cost';

// Mock window object for jsdom environment
if (typeof window === 'undefined') {
  (global as any).window = {};
}

// Mock the cost tracking service
vi.mock('../services/costTracking', () => ({
  costTrackingService: {
    getConversationCost: vi.fn(),
    getCostSummary: vi.fn(),
  },
}));

const { costTrackingService } = await import('../services/costTracking');

describe('Cost Tracking Store', () => {
  beforeEach(() => {
    // Reset store before each test
    const store = useCostTrackingStore.getState();
    store.reset();
    _clearPollingTimer();
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up any polling after tests
    const store = useCostTrackingStore.getState();
    store.stopPolling();
    _clearPollingTimer();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useCostTrackingStore.getState();

      expect(state.conversationCosts).toEqual({});
      expect(state.conversationCostsLoading).toEqual({});
      expect(state.conversationCostsError).toEqual({});
      expect(state.costSummary).toBeNull();
      expect(state.costSummaryLoading).toBe(false);
      expect(state.costSummaryError).toBeNull();
      expect(state.isPolling).toBe(false);
      expect(state.pollingInterval).toBe(30000);
      expect(state.lastUpdate).toBeNull();
    });
  });

  describe('fetchConversationCost', () => {
    it('should fetch conversation cost successfully', async () => {
      const mockCost: ConversationCost = {
        conversationId: 'conv-123',
        totalCostUsd: 0.0456,
        totalTokens: 1500,
        requestCount: 3,
        avgCostPerRequest: 0.0152,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [],
      };

      vi.mocked(costTrackingService.getConversationCost).mockResolvedValue({
        data: mockCost,
        meta: { requestId: 'test-123' },
      });

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-123');
      });

      const state = useCostTrackingStore.getState();

      expect(costTrackingService.getConversationCost).toHaveBeenCalledWith('conv-123');
      expect(state.conversationCosts['conv-123']).toEqual(mockCost);
      expect(state.conversationCostsLoading['conv-123']).toBe(false);
      expect(state.conversationCostsError['conv-123']).toBeNull();
      expect(state.lastUpdate).toBeTruthy();
    });

    it('should handle fetch errors', async () => {
      vi.mocked(costTrackingService.getConversationCost).mockRejectedValue(
        new Error('Network error')
      );

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-123');
      });

      const state = useCostTrackingStore.getState();

      expect(state.conversationCostsLoading['conv-123']).toBe(false);
      expect(state.conversationCostsError['conv-123']).toBe('Network error');
    });

    it('should handle multiple concurrent conversation requests', async () => {
      const mockCost1: ConversationCost = {
        conversationId: 'conv-1',
        totalCostUsd: 0.01,
        totalTokens: 500,
        requestCount: 1,
        avgCostPerRequest: 0.01,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [],
      };

      const mockCost2: ConversationCost = {
        conversationId: 'conv-2',
        totalCostUsd: 0.02,
        totalTokens: 1000,
        requestCount: 2,
        avgCostPerRequest: 0.01,
        provider: 'ollama',
        model: 'llama3',
        requests: [],
      };

      vi.mocked(costTrackingService.getConversationCost)
        .mockResolvedValueOnce({ data: mockCost1, meta: { requestId: 'test-1' } })
        .mockResolvedValueOnce({ data: mockCost2, meta: { requestId: 'test-2' } });

      await act(async () => {
        await Promise.all([
          useCostTrackingStore.getState().fetchConversationCost('conv-1'),
          useCostTrackingStore.getState().fetchConversationCost('conv-2'),
        ]);
      });

      const state = useCostTrackingStore.getState();

      expect(state.conversationCosts['conv-1']).toEqual(mockCost1);
      expect(state.conversationCosts['conv-2']).toEqual(mockCost2);
    });
  });

  describe('clearConversationCost', () => {
    it('should clear cached conversation cost', async () => {
      const mockCost: ConversationCost = {
        conversationId: 'conv-123',
        totalCostUsd: 0.01,
        totalTokens: 500,
        requestCount: 1,
        avgCostPerRequest: 0.01,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [],
      };

      vi.mocked(costTrackingService.getConversationCost).mockResolvedValue({
        data: mockCost,
        meta: { requestId: 'test-123' },
      });

      // First, fetch a cost
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-123');
      });

      let state = useCostTrackingStore.getState();
      expect(state.conversationCosts['conv-123']).toBeDefined();

      // Then clear it
      act(() => {
        useCostTrackingStore.getState().clearConversationCost('conv-123');
      });

      state = useCostTrackingStore.getState();
      expect(state.conversationCosts['conv-123']).toBeUndefined();
      expect(state.conversationCostsLoading['conv-123']).toBeUndefined();
      expect(state.conversationCostsError['conv-123']).toBeUndefined();
    });
  });

  describe('fetchCostSummary', () => {
    it('should fetch cost summary successfully', async () => {
      const mockSummary: CostSummary = {
        totalCostUsd: 1.23,
        totalTokens: 50000,
        requestCount: 100,
        avgCostPerRequest: 0.0123,
        topConversations: [],
        costsByProvider: {
          openai: { costUsd: 0.80, requests: 60 },
          ollama: { costUsd: 0.00, requests: 30 },
        },
        dailyBreakdown: [],
      };

      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: mockSummary,
        meta: { requestId: 'test-123' },
      });

      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary();
      });

      const state = useCostTrackingStore.getState();

      expect(costTrackingService.getCostSummary).toHaveBeenCalledWith({});
      expect(state.costSummary).toEqual(mockSummary);
      expect(state.costSummaryLoading).toBe(false);
      expect(state.costSummaryError).toBeNull();
    });

    it('should pass date range parameters to service', async () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({
          dateFrom: '2026-02-01',
          dateTo: '2026-02-28',
        });
      });

      expect(costTrackingService.getCostSummary).toHaveBeenCalledWith({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });
    });

    it('should merge params with existing params', async () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      // Set initial params
      act(() => {
        useCostTrackingStore.getState().setCostSummaryParams({
          dateFrom: '2026-02-01',
        });
      });

      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({
          dateTo: '2026-02-28',
        });
      });

      expect(costTrackingService.getCostSummary).toHaveBeenCalledWith({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });
    });

    it('should handle fetch errors', async () => {
      vi.mocked(costTrackingService.getCostSummary).mockRejectedValue(
        new Error('API Error')
      );

      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary();
      });

      const state = useCostTrackingStore.getState();

      expect(state.costSummaryLoading).toBe(false);
      expect(state.costSummaryError).toBe('API Error');
    });
  });

  describe('Real-time Polling', () => {
    it('should start polling and trigger initial fetch', async () => {
      const mockSummary: CostSummary = {
        totalCostUsd: 0.50,
        totalTokens: 10000,
        requestCount: 20,
        avgCostPerRequest: 0.025,
        topConversations: [],
        costsByProvider: { openai: { costUsd: 0.50, requests: 20 } },
        dailyBreakdown: [],
      };

      const mockCost: ConversationCost = {
        conversationId: 'conv-123',
        totalCostUsd: 0.01,
        totalTokens: 500,
        requestCount: 1,
        avgCostPerRequest: 0.01,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [],
      };

      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: mockSummary,
        meta: { requestId: 'test' },
      });

      vi.mocked(costTrackingService.getConversationCost).mockResolvedValue({
        data: mockCost,
        meta: { requestId: 'test' },
      });

      act(() => {
        useCostTrackingStore.getState().startPolling('conv-123', 5000);
      });

      const state = useCostTrackingStore.getState();
      expect(state.isPolling).toBe(true);
      expect(state.pollingInterval).toBe(5000);

      // Wait for initial fetch
      await waitFor(() => {
        expect(costTrackingService.getCostSummary).toHaveBeenCalled();
        expect(costTrackingService.getConversationCost).toHaveBeenCalledWith('conv-123');
      });
    });

    it('should stop polling', () => {
      act(() => {
        useCostTrackingStore.getState().startPolling(undefined, 5000);
      });

      let state = useCostTrackingStore.getState();
      expect(state.isPolling).toBe(true);

      act(() => {
        useCostTrackingStore.getState().stopPolling();
      });

      state = useCostTrackingStore.getState();
      expect(state.isPolling).toBe(false);
    });

    it('should update polling interval', () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      act(() => {
        useCostTrackingStore.getState().startPolling(undefined, 5000);
      });

      let state = useCostTrackingStore.getState();
      expect(state.pollingInterval).toBe(5000);

      act(() => {
        useCostTrackingStore.getState().setPollingInterval(10000);
      });

      state = useCostTrackingStore.getState();
      expect(state.pollingInterval).toBe(10000);
      expect(state.isPolling).toBe(true); // Should still be polling
    });

    it('should not fetch conversation cost when conversationId not provided', async () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      act(() => {
        useCostTrackingStore.getState().startPolling(undefined, 5000);
      });

      await waitFor(() => {
        expect(costTrackingService.getCostSummary).toHaveBeenCalled();
      });

      expect(costTrackingService.getConversationCost).not.toHaveBeenCalled();
    });

    it('should verify clearInterval is called when stopping polling', () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

      act(() => {
        useCostTrackingStore.getState().startPolling(undefined, 5000);
      });

      act(() => {
        useCostTrackingStore.getState().stopPolling();
      });

      expect(clearIntervalSpy).toHaveBeenCalled();
      clearIntervalSpy.mockRestore();
    });
  });

  describe('Utility Actions', () => {
    it('should clear all errors', async () => {
      // Set some errors
      vi.mocked(costTrackingService.getConversationCost).mockRejectedValue(
        new Error('Test error')
      );

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-1');
      });

      let state = useCostTrackingStore.getState();
      expect(state.conversationCostsError['conv-1']).toBe('Test error');

      // Clear errors
      act(() => {
        useCostTrackingStore.getState().clearErrors();
      });

      state = useCostTrackingStore.getState();
      expect(state.conversationCostsError).toEqual({});
      expect(state.costSummaryError).toBeNull();
    });

    it('should reset store to initial state', async () => {
      const mockCost: ConversationCost = {
        conversationId: 'conv-1',
        totalCostUsd: 0.01,
        totalTokens: 500,
        requestCount: 1,
        avgCostPerRequest: 0.01,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [],
      };

      vi.mocked(costTrackingService.getConversationCost).mockResolvedValue({
        data: mockCost,
        meta: { requestId: 'test' },
      });

      // Set up some state
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-1');
        useCostTrackingStore.getState().startPolling('conv-1', 10000);
      });

      let state = useCostTrackingStore.getState();
      expect(state.conversationCosts['conv-1']).toBeDefined();
      expect(state.isPolling).toBe(true);

      // Reset
      act(() => {
        useCostTrackingStore.getState().reset();
      });

      state = useCostTrackingStore.getState();
      expect(state.conversationCosts).toEqual({});
      expect(state.isPolling).toBe(false);
      expect(state.pollingInterval).toBe(30000); // Back to default
    });
  });

  describe('useCostTrackingPolling Hook', () => {
    it('should start polling on mount', () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      const { result } = renderHook(() =>
        useCostTrackingPolling('conv-123', 5000)
      );

      expect(result.current).toBeDefined();
      expect(useCostTrackingStore.getState().isPolling).toBe(true);
      expect(useCostTrackingStore.getState().pollingInterval).toBe(5000);
    });

    it('should work without conversationId', () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      renderHook(() => useCostTrackingPolling());

      expect(useCostTrackingStore.getState().isPolling).toBe(true);
      expect(useCostTrackingStore.getState().pollingInterval).toBe(30000); // default
    });

    it('should verify cleanup function exists', () => {
      vi.mocked(costTrackingService.getCostSummary).mockResolvedValue({
        data: {
          totalCostUsd: 0,
          totalTokens: 0,
          requestCount: 0,
          avgCostPerRequest: 0,
          topConversations: [],
          costsByProvider: {},
          dailyBreakdown: [],
        },
        meta: { requestId: 'test' },
      });

      const { unmount } = renderHook(() =>
        useCostTrackingPolling('conv-123', 5000)
      );

      // Verify polling started
      expect(useCostTrackingStore.getState().isPolling).toBe(true);

      // Manually stop polling for this test
      act(() => {
        useCostTrackingStore.getState().stopPolling();
      });

      expect(useCostTrackingStore.getState().isPolling).toBe(false);

      unmount();
    });
  });
});
