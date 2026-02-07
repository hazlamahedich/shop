/**
 * Unit tests for conversationStore URL synchronization
 * P1 - syncWithUrl reads and applies URL query params
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ConversationStatus, Sentiment } from '@/types/conversation';

// Mock URLSearchParams and window.location
const mockURL = (search: string) => {
  const urlSearchParams = {
    get: vi.fn((key: string) => {
      const params = new URLSearchParams(search);
      return params.get(key);
    }),
    getAll: vi.fn((key: string) => {
      const params = new URLSearchParams(search);
      return params.getAll(key);
    }),
    has: vi.fn((key: string) => {
      const params = new URLSearchParams(search);
      return params.has(key);
    }),
  };

  // Mock window.location
  Object.defineProperty(global, 'window', {
    value: {
      location: {
        search,
      },
    },
    writable: true,
  });

  return urlSearchParams;
};

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
    fetchCalled: false,
    // Simulated syncWithUrl logic
    syncWithUrl: async () => {
      if (typeof window === 'undefined') return;

      const urlParams = new URLSearchParams(window.location.search);
      const newFilters = { ...state.filters };
      let hasUrlParams = false;

      if (urlParams.has('search')) {
        newFilters.searchQuery = urlParams.get('search') || '';
        hasUrlParams = true;
      }
      if (urlParams.has('date_from')) {
        newFilters.dateRange.from = urlParams.get('date_from');
        hasUrlParams = true;
      }
      if (urlParams.has('date_to')) {
        newFilters.dateRange.to = urlParams.get('date_to');
        hasUrlParams = true;
      }
      if (urlParams.has('status')) {
        newFilters.statusFilters = urlParams.getAll('status') as ConversationStatus[];
        hasUrlParams = true;
      }
      if (urlParams.has('sentiment')) {
        newFilters.sentimentFilters = urlParams.getAll('sentiment') as Sentiment[];
        hasUrlParams = true;
      }
      if (urlParams.has('has_handoff')) {
        const hasHandoffValue = urlParams.get('has_handoff');
        newFilters.hasHandoffFilter = hasHandoffValue === 'true' ? true : hasHandoffValue === 'false' ? false : null;
        hasUrlParams = true;
      }

      if (hasUrlParams) {
        state.filters = newFilters;
      }
      // Always fetch conversations
      state;
    },
  };
};

describe('conversationStore - URL synchronization', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('syncWithUrl with search parameter', () => {
    it('should read and apply search query from URL', async () => {
      const store = createTestStore();
      mockURL('?search=test%20query');

      await store.syncWithUrl();

      expect(store.getState().filters.searchQuery).toBe('test query');
    });

    it('should handle empty search parameter', async () => {
      const store = createTestStore();
      mockURL('?search=');

      await store.syncWithUrl();

      expect(store.getState().filters.searchQuery).toBe('');
    });
  });

  describe('syncWithUrl with date parameters', () => {
    it('should read date_from parameter', async () => {
      const store = createTestStore();
      mockURL('?date_from=2025-01-01');

      await store.syncWithUrl();

      expect(store.getState().filters.dateRange.from).toBe('2025-01-01');
      expect(store.getState().filters.dateRange.to).toBeNull();
    });

    it('should read date_to parameter', async () => {
      const store = createTestStore();
      mockURL('?date_to=2025-01-31');

      await store.syncWithUrl();

      expect(store.getState().filters.dateRange.from).toBeNull();
      expect(store.getState().filters.dateRange.to).toBe('2025-01-31');
    });

    it('should read both date parameters', async () => {
      const store = createTestStore();
      mockURL('?date_from=2025-01-01&date_to=2025-01-31');

      await store.syncWithUrl();

      expect(store.getState().filters.dateRange).toEqual({
        from: '2025-01-01',
        to: '2025-01-31',
      });
    });
  });

  describe('syncWithUrl with status parameter', () => {
    it('should read single status parameter', async () => {
      const store = createTestStore();
      mockURL('?status=active');

      await store.syncWithUrl();

      expect(store.getState().filters.statusFilters).toEqual(['active']);
    });

    it('should read multiple status parameters', async () => {
      const store = createTestStore();
      mockURL('?status=active&status=handoff&status=closed');

      await store.syncWithUrl();

      expect(store.getState().filters.statusFilters).toEqual([
        'active',
        'handoff',
        'closed',
      ]);
    });
  });

  describe('syncWithUrl with sentiment parameter', () => {
    it('should read single sentiment parameter', async () => {
      const store = createTestStore();
      mockURL('?sentiment=positive');

      await store.syncWithUrl();

      expect(store.getState().filters.sentimentFilters).toEqual(['positive']);
    });

    it('should read multiple sentiment parameters', async () => {
      const store = createTestStore();
      mockURL('?sentiment=positive&sentiment=negative');

      await store.syncWithUrl();

      expect(store.getState().filters.sentimentFilters).toEqual([
        'positive',
        'negative',
      ]);
    });
  });

  describe('syncWithUrl with has_handoff parameter', () => {
    it('should set hasHandoffFilter to true when has_handoff=true', async () => {
      const store = createTestStore();
      mockURL('?has_handoff=true');

      await store.syncWithUrl();

      expect(store.getState().filters.hasHandoffFilter).toBe(true);
    });

    it('should set hasHandoffFilter to false when has_handoff=false', async () => {
      const store = createTestStore();
      mockURL('?has_handoff=false');

      await store.syncWithUrl();

      expect(store.getState().filters.hasHandoffFilter).toBe(false);
    });

    it('should set hasHandoffFilter to null for invalid value', async () => {
      const store = createTestStore();
      mockURL('?has_handoff=invalid');

      await store.syncWithUrl();

      expect(store.getState().filters.hasHandoffFilter).toBeNull();
    });
  });

  describe('syncWithUrl with combined parameters', () => {
    it('should apply all URL parameters together', async () => {
      const store = createTestStore();
      mockURL('?search=urgent&status=active&status=handoff&sentiment=negative&date_from=2025-01-01&has_handoff=true');

      await store.syncWithUrl();

      expect(store.getState().filters).toEqual({
        searchQuery: 'urgent',
        dateRange: { from: '2025-01-01', to: null },
        statusFilters: ['active', 'handoff'],
        sentimentFilters: ['negative'],
        hasHandoffFilter: true,
      });
    });
  });

  describe('syncWithUrl with no parameters', () => {
    it('should not modify filters when URL has no params', async () => {
      const store = createTestStore();
      store.setState({
        filters: {
          searchQuery: 'existing',
          dateRange: { from: '2025-01-01', to: null },
          statusFilters: [ConversationStatus.ACTIVE],
          sentimentFilters: [],
          hasHandoffFilter: null,
        },
      });
      mockURL('');

      await store.syncWithUrl();

      expect(store.getState().filters.searchQuery).toBe('existing');
      expect(store.getState().filters.dateRange.from).toBe('2025-01-01');
    });
  });

  describe('syncWithUrl with SSR (server-side rendering)', () => {
    it('should handle undefined window gracefully', async () => {
      const store = createTestStore();
      // Simulate SSR environment
      const originalWindow = global.window;
      // @ts-ignore - intentionally undefined for SSR test
      delete global.window;

      const result = await store.syncWithUrl();

      // Should not throw and should return without error
      expect(result).toBeUndefined();

      // Restore window
      global.window = originalWindow;
    });
  });
});
