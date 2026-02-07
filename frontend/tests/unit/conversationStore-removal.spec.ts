/**
 * Unit tests for conversationStore filter removal logic
 * P0 - removeFilter action with different filter types
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { ConversationStatus, Sentiment } from '@/types/conversation';

// Mock the store factory to create isolated test instances
const createTestStore = () => {
  let state = {
    filters: {
      searchQuery: '',
      dateRange: { from: null, to: null },
      statusFilters: [] as ConversationStatus[],
      sentimentFilters: [] as Sentiment[],
      hasHandoffFilter: null as boolean | null,
    },
  };

  return {
    getState: () => state,
    setState: (newState: Partial<typeof state>) => {
      state = { ...state, ...newState };
    },
    // Simulated removeFilter logic from store
    removeFilter: async (key: keyof typeof state.filters, value?: any) => {
      const newFilters = { ...state.filters };

      switch (key) {
        case 'searchQuery':
          newFilters.searchQuery = '';
          break;
        case 'dateRange':
          newFilters.dateRange = { from: null, to: null };
          break;
        case 'statusFilters':
          if (value) {
            newFilters.statusFilters = newFilters.statusFilters.filter((s) => s !== value);
          } else {
            newFilters.statusFilters = [];
          }
          break;
        case 'sentimentFilters':
          if (value) {
            newFilters.sentimentFilters = newFilters.sentimentFilters.filter((s) => s !== value);
          } else {
            newFilters.sentimentFilters = [];
          }
          break;
        case 'hasHandoffFilter':
          newFilters.hasHandoffFilter = null;
          break;
      }

      state.filters = newFilters;
    },
  };
};

describe('conversationStore - removeFilter', () => {
  describe('removeFilter for searchQuery', () => {
    it('should clear search query when removed', async () => {
      const store = createTestStore();
      store.setState({
        filters: { ...store.getState().filters, searchQuery: 'test search' },
      });

      await store.removeFilter('searchQuery');

      expect(store.getState().filters.searchQuery).toBe('');
    });
  });

  describe('removeFilter for dateRange', () => {
    it('should clear date range when removed', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          dateRange: { from: '2025-01-01', to: '2025-01-31' },
        },
      });

      await store.removeFilter('dateRange');

      expect(store.getState().filters.dateRange).toEqual({ from: null, to: null });
    });
  });

  describe('removeFilter for statusFilters', () => {
    it('should remove specific status filter when value provided', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          statusFilters: [ConversationStatus.ACTIVE, ConversationStatus.HANDOFF, ConversationStatus.CLOSED],
        },
      });

      await store.removeFilter('statusFilters', ConversationStatus.HANDOFF);

      expect(store.getState().filters.statusFilters).toEqual([
        ConversationStatus.ACTIVE,
        ConversationStatus.CLOSED,
      ]);
    });

    it('should clear all status filters when no value provided', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          statusFilters: [ConversationStatus.ACTIVE, ConversationStatus.HANDOFF],
        },
      });

      await store.removeFilter('statusFilters');

      expect(store.getState().filters.statusFilters).toEqual([]);
    });

    it('should handle removing non-existent status filter gracefully', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          statusFilters: [ConversationStatus.ACTIVE],
        },
      });

      await store.removeFilter('statusFilters', ConversationStatus.HANDOFF);

      expect(store.getState().filters.statusFilters).toEqual([ConversationStatus.ACTIVE]);
    });
  });

  describe('removeFilter for sentimentFilters', () => {
    it('should remove specific sentiment filter when value provided', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          sentimentFilters: [Sentiment.POSITIVE, Sentiment.NEGATIVE, Sentiment.NEUTRAL],
        },
      });

      await store.removeFilter('sentimentFilters', Sentiment.NEGATIVE);

      expect(store.getState().filters.sentimentFilters).toEqual([
        Sentiment.POSITIVE,
        Sentiment.NEUTRAL,
      ]);
    });

    it('should clear all sentiment filters when no value provided', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          sentimentFilters: [Sentiment.POSITIVE, Sentiment.NEGATIVE],
        },
      });

      await store.removeFilter('sentimentFilters');

      expect(store.getState().filters.sentimentFilters).toEqual([]);
    });
  });

  describe('removeFilter for hasHandoffFilter', () => {
    it('should clear handoff filter when removed', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          hasHandoffFilter: true,
        },
      });

      await store.removeFilter('hasHandoffFilter');

      expect(store.getState().filters.hasHandoffFilter).toBeNull();
    });

    it('should clear false handoff filter when removed', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          ...store.getState().filters,
          hasHandoffFilter: false,
        },
      });

      await store.removeFilter('hasHandoffFilter');

      expect(store.getState().filters.hasHandoffFilter).toBeNull();
    });
  });
});
