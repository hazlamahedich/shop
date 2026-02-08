/**
 * Store Tests for Story 3-5: Cost Tracking
 *
 * Tests the cost tracking Zustand store for:
 * - State management
 * - Actions (fetch, polling)
 * - Error handling
 * - State persistence
 * - Polling logic
 *
 * @package frontend/tests/stores
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from 'react-dom/test-utils';
import { _getPollingTimer, _clearPollingTimer } from '../../src/stores/costTrackingStore';

// Mock data
const mockConversationCost = {
  conversationId: 'test-conv-123',
  totalCostUsd: 0.0234,
  totalTokens: 4532,
  requestCount: 5,
  avgCostPerRequest: 0.00468,
  provider: 'openai',
  model: 'gpt-4o-mini',
  requests: [],
};

const mockCostSummary = {
  totalCostUsd: 18.45,
  totalTokens: 2450000,
  requestCount: 847,
  avgCostPerRequest: 0.0218,
  topConversations: [],
  costsByProvider: {},
  dailyBreakdown: [],
};

const mockCostSummaryParams = {
  dateFrom: '2026-02-01',
  dateTo: '2026-02-28',
};

// Mock the costTrackingService
vi.mock('../../src/services/costTracking', () => ({
  costTrackingService: {
    getConversationCost: vi.fn(),
    getCostSummary: vi.fn(),
  },
}));

describe('CostTrackingStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    _clearPollingTimer();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    _clearPollingTimer();
  });

  describe('[P1] Store Initialization', () => {
    it('[P1] should initialize with default state', async () => {
      // Given: Store is imported
      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // Then: Should have initial state
      const state = useCostTrackingStore.getState();
      expect(state.conversationCosts).toEqual({});
      expect(state.costSummary).toBeNull();
      expect(state.costSummaryLoading).toBe(false);
      expect(state.costSummaryError).toBeNull();
      expect(state.isPolling).toBe(false);
      expect(state.pollingInterval).toBe(30000);
      expect(state.lastUpdate).toBeNull();
    });

    it('[P1] should have required actions', async () => {
      // Given: Store is imported
      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // Then: Should have required actions
      const actions = useCostTrackingStore.getState();
      expect(actions.fetchConversationCost).toBeDefined();
      expect(actions.fetchCostSummary).toBeDefined();
      expect(actions.setCostSummaryParams).toBeDefined();
      expect(actions.startPolling).toBeDefined();
      expect(actions.stopPolling).toBeDefined();
      expect(actions.setPollingInterval).toBeDefined();
      expect(actions.clearErrors).toBeDefined();
      expect(actions.reset).toBeDefined();
    });
  });

  describe('[P1] fetchConversationCost Action', () => {
    it('[P1] should set loading state while fetching', async () => {
      // Given: Store and mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching conversation cost
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Then: Loading state should be updated correctly
      const state = useCostTrackingStore.getState();
      expect(state.conversationCostsLoading['test-conv-123']).toBe(false); // After completion
      expect(state.conversationCosts['test-conv-123']).toEqual(mockConversationCost);
    });

    it('[P1] should store conversation cost data on success', async () => {
      // Given: Mock service returns cost data
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching conversation cost
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Then: Data should be stored
      const state = useCostTrackingStore.getState();
      expect(state.conversationCosts['test-conv-123']).toEqual(mockConversationCost);
      expect(state.conversationCostsError['test-conv-123']).toBeNull();
    });

    it('[P1] should update lastUpdate timestamp on success', async () => {
      // Given: Mock service returns cost data
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching conversation cost
      const beforeTimestamp = Date.now();
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Then: lastUpdate should be updated
      const state = useCostTrackingStore.getState();
      expect(state.lastUpdate).not.toBeNull();
      expect(new Date(state.lastUpdate!).getTime()).toBeGreaterThanOrEqual(beforeTimestamp);
    });

    it('[P2] should store error on fetch failure', async () => {
      // Given: Mock service throws error
      const { costTrackingService } = await import('../../src/services/costTracking');
      const mockError = new Error('Network error');
      costTrackingService.getConversationCost.mockRejectedValue(mockError);

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching conversation cost fails
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Then: Error should be stored
      const state = useCostTrackingStore.getState();
      expect(state.conversationCostsError['test-conv-123']).toBe('Network error');
      expect(state.conversationCostsLoading['test-conv-123']).toBe(false);
    });

    it('[P2] should clear error on successful retry', async () => {
      // Given: Previous error exists
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce({ data: mockConversationCost });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // First call fails
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Second call succeeds
      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // Then: Error should be cleared
      const state = useCostTrackingStore.getState();
      expect(state.conversationCostsError['test-conv-123']).toBeNull();
    });
  });

  describe('[P0] fetchCostSummary Action', () => {
    it('[P0] should set loading state while fetching', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching cost summary
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({});
      });

      // Then: Should set loading to false after completion
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryLoading).toBe(false);
    });

    it('[P0] should store cost summary data on success', async () => {
      // Given: Mock service returns summary
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching cost summary
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({});
      });

      // Then: Data should be stored
      const state = useCostTrackingStore.getState();
      expect(state.costSummary).toEqual(mockCostSummary);
      expect(state.costSummaryError).toBeNull();
    });

    it('[P0] should store query parameters', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching with parameters
      const params = { dateFrom: '2026-02-01', dateTo: '2026-02-28' };
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary(params);
      });

      // Then: Parameters should be stored
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryParams).toEqual(params);
    });

    it('[P0] should update lastUpdate timestamp on success', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching cost summary
      const beforeTimestamp = Date.now();
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({});
      });

      // Then: lastUpdate should be updated
      const state = useCostTrackingStore.getState();
      expect(state.lastUpdate).not.toBeNull();
      expect(new Date(state.lastUpdate!).getTime()).toBeGreaterThanOrEqual(beforeTimestamp);
    });

    it('[P2] should store error on fetch failure', async () => {
      // Given: Mock service throws error
      const { costTrackingService } = await import('../../src/services/costTracking');
      const mockError = new Error('API error');
      costTrackingService.getCostSummary.mockRejectedValue(mockError);

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Fetching cost summary fails
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({});
      });

      // Then: Error should be stored
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryError).toBe('API error');
      expect(state.costSummaryLoading).toBe(false);
    });
  });

  describe('[P1] setCostSummaryParams Action', () => {
    it('[P1] should update cost summary parameters', async () => {
      // Given: Store is imported
      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Setting cost summary params
      const params = { dateFrom: '2026-02-01', dateTo: '2026-02-28' };
      act(() => {
        useCostTrackingStore.getState().setCostSummaryParams(params);
      });

      // Then: Parameters should be updated
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryParams).toEqual(params);
    });

    it('[P0] should merge parameters with existing params', async () => {
      // Given: Store has existing params
      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');
      act(() => {
        useCostTrackingStore.getState().setCostSummaryParams({ dateFrom: '2026-02-01' });
      });

      // When: Setting additional params
      act(() => {
        useCostTrackingStore.getState().setCostSummaryParams({ dateTo: '2026-02-28' });
      });

      // Then: Both params should be present
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryParams).toEqual({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });
    });
  });

  describe('[P1] Polling Actions', () => {
    it('[P1] should start polling with default interval', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Starting polling
      await act(async () => {
        useCostTrackingStore.getState().startPolling();
      });

      // Then: Polling state should be active
      const state = useCostTrackingStore.getState();
      expect(state.isPolling).toBe(true);
      expect(state.pollingInterval).toBe(30000);
    });

    it('[P0] should start polling with custom interval', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Starting polling with custom interval
      const customInterval = 15000;
      await act(async () => {
        useCostTrackingStore.getState().startPolling(undefined, customInterval);
      });

      // Then: Polling interval should be updated
      const state = useCostTrackingStore.getState();
      expect(state.pollingInterval).toBe(customInterval);
      expect(state.isPolling).toBe(true);
    });

    it('[P0] should stop polling', async () => {
      // Given: Polling is active
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        useCostTrackingStore.getState().startPolling();
        expect(useCostTrackingStore.getState().isPolling).toBe(true);

        useCostTrackingStore.getState().stopPolling();
      });

      // When: Polling is stopped
      const state = useCostTrackingStore.getState();
      expect(state.isPolling).toBe(false);
    });

    it('[P2] should clear polling timer on stop', async () => {
      // Given: Polling is active
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        useCostTrackingStore.getState().startPolling();
        const timerBefore = _getPollingTimer();
        expect(timerBefore).not.toBeNull();

        useCostTrackingStore.getState().stopPolling();
      });

      // Then: Polling timer should be cleared
      const timerAfter = _getPollingTimer();
      expect(timerAfter).toBeNull();
    });

    it('[P2] should fetch conversation cost when conversationId provided', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Starting polling with conversationId
      await act(async () => {
        useCostTrackingStore.getState().startPolling('test-conv-123');
      });

      // Then: Should fetch conversation cost
      expect(costTrackingService.getConversationCost).toHaveBeenCalledWith('test-conv-123');
    });

    it('[P2] should fetch cost summary when starting polling', async () => {
      // Given: Mock service
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Starting polling
      await act(async () => {
        useCostTrackingStore.getState().startPolling();
      });

      // Then: Should fetch cost summary
      expect(costTrackingService.getCostSummary).toHaveBeenCalled();
    });
  });

  describe('[P2] setPollingInterval Action', () => {
    it('[P2] should update polling interval', async () => {
      // Given: Store is imported
      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // When: Setting polling interval
      const newInterval = 15000;
      act(() => {
        useCostTrackingStore.getState().setPollingInterval(newInterval);
      });

      // Then: Interval should be updated
      const state = useCostTrackingStore.getState();
      expect(state.pollingInterval).toBe(newInterval);
    });

    it('[P2] should restart polling if currently polling', async () => {
      // Given: Polling is active
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // Given: Start polling
      await act(async () => {
        useCostTrackingStore.getState().startPolling();
      });

      const timerBefore = _getPollingTimer();
      expect(timerBefore).not.toBeNull();

      // When: Changing interval while polling
      await act(async () => {
        useCostTrackingStore.getState().setPollingInterval(10000);
      });

      // Then: Polling timer should be cleared (restart happened)
      const timerAfter = _getPollingTimer();
      expect(timerAfter).not.toBe(timerBefore);
    });
  });

  describe('[P1] clearErrors Action', () => {
    it('[P1] should clear cost summary error', async () => {
      // Given: Store has error state
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockRejectedValueOnce(new Error('Error'));

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      // First, create an error
      await act(async () => {
        await useCostTrackingStore.getState().fetchCostSummary({});
      });

      const stateWithError = useCostTrackingStore.getState();
      expect(stateWithError.costSummaryError).not.toBeNull();

      // When: Clearing errors
      act(() => {
        useCostTrackingStore.getState().clearErrors();
      });

      // Then: Error should be cleared
      const state = useCostTrackingStore.getState();
      expect(state.costSummaryError).toBeNull();
    });

    it('[P2] should clear all conversation cost errors', async () => {
      // Given: Store has conversation cost errors
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockRejectedValueOnce(new Error('Error'));

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('conv-1');
      });

      const stateWithError = useCostTrackingStore.getState();
      expect(Object.keys(stateWithError.conversationCostsError)).toHaveLength(1);

      // When: Clearing errors
      act(() => {
        useCostTrackingStore.getState().clearErrors();
      });

      // Then: All errors should be cleared
      const state = useCostTrackingStore.getState();
      expect(Object.keys(state.conversationCostsError)).toHaveLength(0);
    });
  });

  describe('[P2] reset Action', () => {
    it('[P2] should reset store to initial state', async () => {
      // Given: Store has data
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        useCostTrackingStore.getState().fetchCostSummary({});
        useCostTrackingStore.getState().startPolling();
      });

      const stateWithData = useCostTrackingStore.getState();
      expect(stateWithData.costSummary).not.toBeNull();
      expect(stateWithData.isPolling).toBe(true);

      // When: Resetting store
      act(() => {
        useCostTrackingStore.getState().reset();
      });

      // Then: Should return to initial state
      const state = useCostTrackingStore.getState();
      expect(state.costSummary).toBeNull();
      expect(state.isPolling).toBe(false);
      expect(state.lastUpdate).toBeNull();
    });

    it('[P2] should clear polling timer on reset', async () => {
      // Given: Polling is active
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getCostSummary.mockResolvedValue({
        data: mockCostSummary,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        useCostTrackingStore.getState().startPolling();
        const timerBefore = _getPollingTimer();
        expect(timerBefore).not.toBeNull();

        // When: Resetting store
        useCostTrackingStore.getState().reset();
      });

      // Then: Polling timer should be cleared
      const timerAfter = _getPollingTimer();
      expect(timerAfter).toBeNull();
    });
  });

  describe('[P2] clearConversationCost Action', () => {
    it('[P2] should remove conversation cost from cache', async () => {
      // Given: Store has conversation cost data
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      const stateWithData = useCostTrackingStore.getState();
      expect(stateWithData.conversationCosts['test-conv-123']).toBeDefined();

      // When: Clearing conversation cost
      act(() => {
        useCostTrackingStore.getState().clearConversationCost('test-conv-123');
      });

      // Then: Data should be removed
      const state = useCostTrackingStore.getState();
      expect(state.conversationCosts['test-conv-123']).toBeUndefined();
    });

    it('[P2] should remove loading state for cleared conversation', async () => {
      // Given: Store has loading state
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockResolvedValue({
        data: mockConversationCost,
      });

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      // When: Clearing conversation cost
      act(() => {
        useCostTrackingStore.getState().clearConversationCost('test-conv-123');
      });

      // Then: Loading state should be removed
      const state = useCostTrackingStore.getState();
      expect(state.conversationCostsLoading['test-conv-123']).toBeUndefined();
    });

    it('[P2] should remove error state for cleared conversation', async () => {
      // Given: Store has error state
      const { costTrackingService } = await import('../../src/services/costTracking');
      costTrackingService.getConversationCost.mockRejectedValueOnce(new Error('Error'));

      const { useCostTrackingStore } = await import('../../src/stores/costTrackingStore');

      await act(async () => {
        await useCostTrackingStore.getState().fetchConversationCost('test-conv-123');
      });

      const stateWithError = useCostTrackingStore.getState();
      expect(stateWithError.conversationCostsError['test-conv-123']).toBeDefined();

      // When: Clearing conversation cost
      act(() => {
        useCostTrackingStore.getState().clearConversationCost('test-conv-123');
      });

      // Then: Error state should be removed
      const state = useCostTrackingStore.getState();
      expect(state.conversationCostsError['test-conv-123']).toBeUndefined();
    });
  });
});
