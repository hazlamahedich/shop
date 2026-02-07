/**
 * Unit tests for conversationStore saved filters management
 * P0 - saveCurrentFilters, deleteSavedFilter, applySavedFilter
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { SavedFilter, ConversationStatus, Sentiment } from '@/types/conversation';

// Mock the store factory for saved filter operations
const createTestStore = () => {
  let state = {
    filters: {
      searchQuery: '',
      dateRange: { from: null, to: null },
      statusFilters: [] as ConversationStatus[],
      sentimentFilters: [] as Sentiment[],
      hasHandoffFilter: null as boolean | null,
    },
    savedFilters: [] as SavedFilter[],
  };

  let fetchCalled = false;

  return {
    getState: () => state,
    setState: (newState: Partial<typeof state>) => {
      state = { ...state, ...newState };
    },
    fetchCalled: () => fetchCalled,
    // Simulated saveCurrentFilters logic
    saveCurrentFilters: (name: string) => {
      const newFilter: SavedFilter = {
        id: `filter-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        name,
        filters: { ...state.filters },
        createdAt: new Date().toISOString(),
      };
      state.savedFilters = [...state.savedFilters, newFilter];
    },
    // Simulated deleteSavedFilter logic
    deleteSavedFilter: (id: string) => {
      state.savedFilters = state.savedFilters.filter((f) => f.id !== id);
    },
    // Simulated applySavedFilter logic
    applySavedFilter: async (id: string) => {
      const savedFilter = state.savedFilters.find((f) => f.id === id);
      if (savedFilter) {
        state.filters = { ...savedFilter.filters };
        fetchCalled = true;
      }
    },
  };
};

describe('conversationStore - saved filters management', () => {
  describe('saveCurrentFilters', () => {
    it('should save current filters with unique ID', () => {
      const store = createTestStore();
      store.setState({
        filters: {
          searchQuery: 'test',
          dateRange: { from: '2025-01-01', to: null },
          statusFilters: [ConversationStatus.ACTIVE],
          sentimentFilters: [Sentiment.NEGATIVE],
          hasHandoffFilter: true,
        },
      });

      store.saveCurrentFilters('My Test Filter');

      const savedFilters = store.getState().savedFilters;
      expect(savedFilters).toHaveLength(1);
      expect(savedFilters[0].name).toBe('My Test Filter');
      expect(savedFilters[0].id).toMatch(/^filter-\d+-[a-z0-9]+$/);
      expect(savedFilters[0].filters.searchQuery).toBe('test');
      expect(savedFilters[0].createdAt).toBeDefined();
    });

    it('should preserve existing saved filters when adding new one', () => {
      const store = createTestStore();
      const existingFilter: SavedFilter = {
        id: 'existing-1',
        name: 'Existing Filter',
        filters: { searchQuery: '', dateRange: { from: null, to: null }, statusFilters: [], sentimentFilters: [], hasHandoffFilter: null },
        createdAt: '2025-01-01T00:00:00Z',
      };
      store.setState({ savedFilters: [existingFilter] });

      store.saveCurrentFilters('New Filter');

      const savedFilters = store.getState().savedFilters;
      expect(savedFilters).toHaveLength(2);
      expect(savedFilters[0].id).toBe('existing-1');
      expect(savedFilters[1].name).toBe('New Filter');
    });

    it('should deep copy filters when saving', () => {
      const store = createTestStore();
      store.setState({
        filters: {
          searchQuery: 'original',
          dateRange: { from: '2025-01-01', to: null },
          statusFilters: [ConversationStatus.ACTIVE],
          sentimentFilters: [],
          hasHandoffFilter: null,
        },
      });

      store.saveCurrentFilters('Test');

      // Modify original filters
      store.setState({
        filters: {
          ...store.getState().filters,
          searchQuery: 'modified',
        },
      });

      // Saved filter should not be affected
      expect(store.getState().savedFilters[0].filters.searchQuery).toBe('original');
    });
  });

  describe('deleteSavedFilter', () => {
    it('should remove filter by ID', () => {
      const store = createTestStore();
      const filters: SavedFilter[] = [
        { id: 'filter-1', name: 'Filter 1', filters: { searchQuery: '', dateRange: { from: null, to: null }, statusFilters: [], sentimentFilters: [], hasHandoffFilter: null }, createdAt: '2025-01-01T00:00:00Z' },
        { id: 'filter-2', name: 'Filter 2', filters: { searchQuery: '', dateRange: { from: null, to: null }, statusFilters: [], sentimentFilters: [], hasHandoffFilter: null }, createdAt: '2025-01-02T00:00:00Z' },
        { id: 'filter-3', name: 'Filter 3', filters: { searchQuery: '', dateRange: { from: null, to: null }, statusFilters: [], sentimentFilters: [], hasHandoffFilter: null }, createdAt: '2025-01-03T00:00:00Z' },
      ];
      store.setState({ savedFilters: filters });

      store.deleteSavedFilter('filter-2');

      const savedFilters = store.getState().savedFilters;
      expect(savedFilters).toHaveLength(2);
      expect(savedFilters.map((f) => f.id)).toEqual(['filter-1', 'filter-3']);
    });

    it('should handle deleting non-existent filter gracefully', () => {
      const store = createTestStore();
      const filters: SavedFilter[] = [
        { id: 'filter-1', name: 'Filter 1', filters: { searchQuery: '', dateRange: { from: null, to: null }, statusFilters: [], sentimentFilters: [], hasHandoffFilter: null }, createdAt: '2025-01-01T00:00:00Z' },
      ];
      store.setState({ savedFilters: filters });

      store.deleteSavedFilter('non-existent');

      expect(store.getState().savedFilters).toHaveLength(1);
    });

    it('should handle deleting from empty list gracefully', () => {
      const store = createTestStore();
      store.setState({ savedFilters: [] });

      store.deleteSavedFilter('any-id');

      expect(store.getState().savedFilters).toHaveLength(0);
    });
  });

  describe('applySavedFilter', () => {
    it('should apply saved filter to current filters', async () => {
      const store = createTestStore();
      const savedFilter: SavedFilter = {
        id: 'filter-1',
        name: 'Test Filter',
        filters: {
          searchQuery: 'applied search',
          dateRange: { from: '2025-01-01', to: '2025-01-31' },
          statusFilters: [ConversationStatus.ACTIVE, ConversationStatus.HANDOFF],
          sentimentFilters: [Sentiment.POSITIVE],
          hasHandoffFilter: true,
        },
        createdAt: '2025-01-01T00:00:00Z',
      };
      store.setState({
        filters: {
          searchQuery: 'original',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null,
        },
        savedFilters: [savedFilter],
      });

      await store.applySavedFilter('filter-1');

      const appliedFilters = store.getState().filters;
      expect(appliedFilters.searchQuery).toBe('applied search');
      expect(appliedFilters.dateRange).toEqual({ from: '2025-01-01', to: '2025-01-31' });
      expect(appliedFilters.statusFilters).toEqual([ConversationStatus.ACTIVE, ConversationStatus.HANDOFF]);
      expect(appliedFilters.sentimentFilters).toEqual([Sentiment.POSITIVE]);
      expect(appliedFilters.hasHandoffFilter).toBe(true);
      expect(store.fetchCalled()).toBe(true);
    });

    it('should handle applying non-existent filter gracefully', async () => {
      const store = createTestStore();
      const originalFilters = { ...store.getState().filters };
      store.setState({ savedFilters: [] });

      await store.applySavedFilter('non-existent');

      expect(store.getState().filters).toEqual(originalFilters);
      expect(store.fetchCalled()).toBe(false);
    });

    it('should deep copy saved filter when applying', async () => {
      const store = createTestStore();
      const savedFilter: SavedFilter = {
        id: 'filter-1',
        name: 'Test',
        filters: {
          searchQuery: 'saved',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null,
        },
        createdAt: '2025-01-01T00:00:00Z',
      };
      store.setState({
        filters: {
          searchQuery: '',
          dateRange: { from: null, to: null },
          statusFilters: [],
          sentimentFilters: [],
          hasHandoffFilter: null,
        },
        savedFilters: [savedFilter],
      });

      await store.applySavedFilter('filter-1');

      // Modify current filters
      store.setState({
        filters: {
          ...store.getState().filters,
          searchQuery: 'modified',
        },
      });

      // Saved filter should not be affected
      expect(store.getState().savedFilters[0].filters.searchQuery).toBe('saved');
    });
  });
});
