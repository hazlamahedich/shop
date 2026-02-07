/**
 * ConversationStore Tests
 *
 * Tests conversation store state management
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useConversationStore } from './conversationStore';
import { conversationsService } from '../services/conversations';

// Mock the conversations service
vi.mock('../services/conversations', () => ({
  conversationsService: {
    getConversations: vi.fn(),
  },
}));

describe('ConversationStore', () => {
  const mockConversations = [
    {
      id: 1,
      platformSenderId: 'customer_123',
      platformSenderIdMasked: 'cust****',
      lastMessage: 'Hello',
      status: 'active' as const,
      sentiment: 'neutral' as const,
      messageCount: 2,
      updatedAt: '2026-02-07T10:00:00Z',
      createdAt: '2026-02-07T09:00:00Z',
    },
    {
      id: 2,
      platformSenderId: 'customer_456',
      platformSenderIdMasked: 'cust****',
      lastMessage: 'Help needed',
      status: 'handoff' as const,
      sentiment: 'neutral' as const,
      messageCount: 5,
      updatedAt: '2026-02-07T09:00:00Z',
      createdAt: '2026-02-07T08:00:00Z',
    },
  ];

  const mockResponse = {
    data: mockConversations,
    meta: {
      pagination: {
        total: 2,
        page: 1,
        perPage: 20,
        totalPages: 1,
      },
    },
  };

  beforeEach(() => {
    // Clear localStorage to prevent persist middleware from rehydrating old state
    localStorage.clear();
    // Reset store to initial state
    useConversationStore.getState().reset();
    vi.clearAllMocks();
  });

  it('has correct initial state', () => {
    const state = useConversationStore.getState();

    expect(state.conversations).toEqual([]);
    expect(state.pagination).toBeNull();
    expect(state.loadingState).toBe('idle');
    expect(state.error).toBeNull();
    expect(state.currentPage).toBe(1);
    expect(state.perPage).toBe(20);
    expect(state.sortBy).toBe('updated_at');
    expect(state.sortOrder).toBe('desc');
  });

  it('fetches conversations successfully', async () => {
    vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

    const state = useConversationStore.getState();
    await state.fetchConversations();

    expect(conversationsService.getConversations).toHaveBeenCalledWith({
      page: 1,
      perPage: 20,
      sortBy: 'updated_at',
      sortOrder: 'desc',
    });

    const newState = useConversationStore.getState();
    expect(newState.conversations).toEqual(mockConversations);
    expect(newState.pagination).toEqual(mockResponse.meta.pagination);
    expect(newState.loadingState).toBe('success');
    expect(newState.error).toBeNull();
  });

  it('handles fetch errors', async () => {
    const error = new Error('Network error');
    vi.mocked(conversationsService.getConversations).mockRejectedValue(error);

    const state = useConversationStore.getState();
    await state.fetchConversations();

    const newState = useConversationStore.getState();
    expect(newState.loadingState).toBe('error');
    expect(newState.error).toBe('Network error');
    expect(newState.conversations).toEqual([]);
  });

  it('navigates to next page', async () => {
    // First call returns page 1 with totalPages: 2
    const page1Response = {
      ...mockResponse,
      meta: {
        pagination: {
          total: 40,
          page: 1,
          perPage: 20,
          totalPages: 2,
        },
      },
    };

    // Second call returns page 2
    const page2Response = {
      ...mockResponse,
      meta: {
        pagination: {
          total: 40,
          page: 2,
          perPage: 20,
          totalPages: 2,
        },
      },
    };

    vi.mocked(conversationsService.getConversations)
      .mockResolvedValueOnce(page1Response)
      .mockResolvedValueOnce(page2Response);

    // First load page 1
    let state = useConversationStore.getState();
    await state.fetchConversations();

    // Go to next page
    state = useConversationStore.getState();
    await state.nextPage();

    expect(conversationsService.getConversations).toHaveBeenCalledWith({
      page: 2,
      perPage: 20,
      sortBy: 'updated_at',
      sortOrder: 'desc',
    });
  });

  it('navigates to previous page', async () => {
    const page2Response = {
      ...mockResponse,
      meta: {
        pagination: {
          total: 40,
          page: 2,
          perPage: 20,
          totalPages: 2,
        },
      },
    };

    vi.mocked(conversationsService.getConversations).mockResolvedValue(page2Response);

    // Load page 2 directly
    let state = useConversationStore.getState();
    await state.fetchConversations({ page: 2 });

    // Go to previous page
    state = useConversationStore.getState();
    await state.prevPage();

    expect(conversationsService.getConversations).toHaveBeenCalledWith({
      page: 1,
      perPage: 20,
      sortBy: 'updated_at',
      sortOrder: 'desc',
    });
  });

  it('does not navigate next when on last page', async () => {
    vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

    const state = useConversationStore.getState();
    await state.fetchConversations();

    // Try to go next when already on last page
    await state.nextPage();

    // Should not call getConversations again
    expect(conversationsService.getConversations).toHaveBeenCalledTimes(1);
  });

  it('does not navigate prev when on first page', async () => {
    vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

    const state = useConversationStore.getState();
    await state.fetchConversations();

    // Try to go prev when on first page
    await state.prevPage();

    // Should not call getConversations again
    expect(conversationsService.getConversations).toHaveBeenCalledTimes(1);
  });

  it('changes per page and resets to page 1', async () => {
    vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

    const state = useConversationStore.getState();
    await state.setPerPage(50);

    expect(conversationsService.getConversations).toHaveBeenCalledWith({
      page: 1,
      perPage: 50,
      sortBy: 'updated_at',
      sortOrder: 'desc',
    });
  });

  it('changes sorting parameters', async () => {
    vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

    const state = useConversationStore.getState();
    await state.setSorting('status', 'asc');

    expect(conversationsService.getConversations).toHaveBeenCalledWith({
      page: 1,
      perPage: 20,
      sortBy: 'status',
      sortOrder: 'asc',
    });
  });

  it('clears error state', () => {
    const state = useConversationStore.getState();
    state.clearError();

    expect(useConversationStore.getState().error).toBeNull();
  });

  it('resets to initial state', () => {
    const state = useConversationStore.getState();
    state.reset();

    const resetState = useConversationStore.getState();
    expect(resetState.conversations).toEqual([]);
    expect(resetState.pagination).toBeNull();
    expect(resetState.loadingState).toBe('idle');
    expect(resetState.error).toBeNull();
  });

  // Filter State Tests
  describe('Filter State Management', () => {
    it('sets search query and fetches conversations', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSearchQuery('test search');

      const newState = useConversationStore.getState();
      expect(newState.filters.searchQuery).toBe('test search');
      expect(conversationsService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'test search', page: 1 })
      );
    });

    it('sets date range from', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setDateRange('2026-02-01', null);

      const newState = useConversationStore.getState();
      expect(newState.filters.dateRange.from).toBe('2026-02-01');
      expect(newState.filters.dateRange.to).toBe(null);
    });

    it('sets date range to', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setDateRange(null, '2026-02-28');

      const newState = useConversationStore.getState();
      expect(newState.filters.dateRange.from).toBe(null);
      expect(newState.filters.dateRange.to).toBe('2026-02-28');
    });

    it('sets full date range', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setDateRange('2026-02-01', '2026-02-28');

      const newState = useConversationStore.getState();
      expect(newState.filters.dateRange).toEqual({
        from: '2026-02-01',
        to: '2026-02-28',
      });
    });

    it('sets single status filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setStatusFilters(['active']);

      const newState = useConversationStore.getState();
      expect(newState.filters.statusFilters).toEqual(['active']);
    });

    it('sets multiple status filters', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setStatusFilters(['active', 'closed']);

      const newState = useConversationStore.getState();
      expect(newState.filters.statusFilters).toEqual(['active', 'closed']);
    });

    it('sets single sentiment filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSentimentFilters(['positive']);

      const newState = useConversationStore.getState();
      expect(newState.filters.sentimentFilters).toEqual(['positive']);
    });

    it('sets multiple sentiment filters', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSentimentFilters(['positive', 'negative']);

      const newState = useConversationStore.getState();
      expect(newState.filters.sentimentFilters).toEqual(['positive', 'negative']);
    });

    it('sets hasHandoffFilter to true', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setHasHandoffFilter(true);

      const newState = useConversationStore.getState();
      expect(newState.filters.hasHandoffFilter).toBe(true);
    });

    it('sets hasHandoffFilter to false', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setHasHandoffFilter(false);

      const newState = useConversationStore.getState();
      expect(newState.filters.hasHandoffFilter).toBe(false);
    });

    it('sets hasHandoffFilter to null (any)', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setHasHandoffFilter(null);

      const newState = useConversationStore.getState();
      expect(newState.filters.hasHandoffFilter).toBe(null);
    });

    it('removes search query filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSearchQuery('test');
      await state.removeFilter('searchQuery');

      expect(state.filters.searchQuery).toBe('');
    });

    it('removes date range filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setDateRange('2026-02-01', '2026-02-28');
      await state.removeFilter('dateRange');

      expect(state.filters.dateRange).toEqual({ from: null, to: null });
    });

    it('removes single status filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setStatusFilters(['active', 'closed']);
      await state.removeFilter('statusFilters', 'active');

      const newState = useConversationStore.getState();
      expect(newState.filters.statusFilters).toEqual(['closed']);
    });

    it('removes single sentiment filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSentimentFilters(['positive', 'negative']);
      await state.removeFilter('sentimentFilters', 'positive');

      const newState = useConversationStore.getState();
      expect(newState.filters.sentimentFilters).toEqual(['negative']);
    });

    it('removes handoff filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setHasHandoffFilter(true);
      await state.removeFilter('hasHandoffFilter');

      expect(state.filters.hasHandoffFilter).toBe(null);
    });

    it('clears all filters', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();

      // Set multiple filters
      await state.setSearchQuery('test');
      await state.setDateRange('2026-02-01', '2026-02-28');
      await state.setStatusFilters(['active']);
      await state.setSentimentFilters(['positive']);
      await state.setHasHandoffFilter(true);

      // Clear all
      await state.clearAllFilters();

      expect(state.filters).toEqual({
        searchQuery: '',
        dateRange: { from: null, to: null },
        statusFilters: [],
        sentimentFilters: [],
        hasHandoffFilter: null,
      });
    });

    it('applies multiple filters together', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      const state = useConversationStore.getState();
      await state.setSearchQuery('shoes');
      await state.setDateRange('2026-02-01', '2026-02-28');
      await state.setStatusFilters(['active']);
      await state.setSentimentFilters(['positive']);

      expect(conversationsService.getConversations).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'shoes',
          dateFrom: '2026-02-01',
          dateTo: '2026-02-28',
          status: ['active'],
          sentiment: ['positive'],
        })
      );
    });
  });

  // Saved Filters Tests
  describe('Saved Filters Management', () => {
    it('saves current filters with name', () => {
      // Set filters directly via setState (saveCurrentFilters is synchronous)
      useConversationStore.setState({
        filters: {
          searchQuery: 'test',
          dateRange: { from: null, to: null },
          statusFilters: ['active'],
          sentimentFilters: [],
          hasHandoffFilter: null
        }
      });

      useConversationStore.getState().saveCurrentFilters('Active Test');

      // Get the state AFTER saving to see the updated savedFilters
      const newState = useConversationStore.getState();
      const saved = newState.savedFilters;
      expect(saved).toHaveLength(1);
      expect(saved[0].name).toBe('Active Test');
      expect(saved[0].filters.searchQuery).toBe('test');
      expect(saved[0].filters.statusFilters).toEqual(['active']);
    });

    it('deletes saved filter by id', () => {
      // Create first filter
      useConversationStore.setState({
        filters: {
          searchQuery: 'first',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null
        }
      });
      useConversationStore.getState().saveCurrentFilters('Filter 1');

      // Verify first filter was saved
      let state = useConversationStore.getState();
      expect(state.savedFilters).toHaveLength(1);
      const firstFilterId = state.savedFilters[0].id;

      // Create second filter
      useConversationStore.setState({
        filters: {
          searchQuery: 'second',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null
        }
      });

      // Get FRESH state and save
      const stateForSave = useConversationStore.getState();
      stateForSave.saveCurrentFilters('Filter 2');

      // Verify second filter was saved
      state = useConversationStore.getState();
      expect(state.savedFilters).toHaveLength(2);
      const secondFilterId = state.savedFilters[1].id;

      // Delete the FIRST filter by ID
      useConversationStore.getState().deleteSavedFilter(firstFilterId);

      // Get state AFTER deleting - should have 1 filter left
      const newState = useConversationStore.getState();
      expect(newState.savedFilters).toHaveLength(1);
      expect(newState.savedFilters[0].name).toBe('Filter 2');
      expect(newState.savedFilters[0].id).toBe(secondFilterId);
    });

    it('applies saved filter', async () => {
      vi.mocked(conversationsService.getConversations).mockResolvedValue(mockResponse);

      // Create and save a filter
      useConversationStore.setState({
        filters: {
          searchQuery: 'test',
          dateRange: { from: null, to: null },
          statusFilters: ['active'],
          sentimentFilters: [],
          hasHandoffFilter: null
        }
      });
      useConversationStore.getState().saveCurrentFilters('Saved Filter');

      const filterId = useConversationStore.getState().savedFilters[0].id;

      // Clear filters first
      useConversationStore.setState({
        filters: {
          searchQuery: '',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null
        }
      });

      // Apply saved filter (this is async and fetches conversations)
      await useConversationStore.getState().applySavedFilter(filterId);

      const newState = useConversationStore.getState();
      expect(newState.filters.searchQuery).toBe('test');
      expect(newState.filters.statusFilters).toContain('active');
    });
  });

  // URL Sync Tests
  describe('URL Sync with Filters', () => {
    it('syncs filters from URL query params when available', () => {
      // Mock URL with params
      const originalLocation = window.location;
      delete (window as any).location;
      (window as any).location = new URL('https://example.com/conversations?search=test&status=active&status=closed');

      useConversationStore.getState().syncWithUrl();

      const newState = useConversationStore.getState();
      expect(newState.filters.searchQuery).toBe('test');
      expect(newState.filters.statusFilters).toEqual(['active', 'closed']);

      // Restore original location
      (window as any).location = originalLocation;
    });

    it('syncs date range from URL params', () => {
      const originalLocation = window.location;
      delete (window as any).location;
      (window as any).location = new URL('https://example.com/conversations?date_from=2026-02-01&date_to=2026-02-28');

      useConversationStore.getState().syncWithUrl();

      const newState = useConversationStore.getState();
      expect(newState.filters.dateRange.from).toBe('2026-02-01');
      expect(newState.filters.dateRange.to).toBe('2026-02-28');

      (window as any).location = originalLocation;
    });

    it('syncs handoff filter from URL params', () => {
      const originalLocation = window.location;
      delete (window as any).location;
      (window as any).location = new URL('https://example.com/conversations?has_handoff=true');

      useConversationStore.getState().syncWithUrl();

      const newState = useConversationStore.getState();
      expect(newState.filters.hasHandoffFilter).toBe(true);

      (window as any).location = originalLocation;
    });
  });
});
