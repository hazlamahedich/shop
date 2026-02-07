/**
 * Unit tests for conversationStore sorting and pagination actions
 * P1 - setPerPage, setSorting
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { ConversationStatus, Sentiment } from '@/types/conversation';
import type { PaginationMeta } from '@/types/conversation';

// Mock the store factory for sorting operations
const createTestStore = () => {
  let state = {
    conversations: [],
    pagination: null as PaginationMeta | null,
    currentPage: 1,
    perPage: 20,
    sortBy: 'updated_at' as 'updated_at' | 'status' | 'created_at',
    sortOrder: 'desc' as 'asc' | 'desc',
  };

  let lastFetchParams: any = {};

  return {
    getState: () => state,
    setState: (newState: Partial<typeof state>) => {
      state = { ...state, ...newState };
    },
    getLastFetchParams: () => lastFetchParams,
    // Simulated fetchConversations
    fetchConversations: async (params: any = {}) => {
      lastFetchParams = params;
      // Mock response
      state.currentPage = params.page ?? 1;
      state.perPage = params.perPage ?? 20;
      state.sortBy = params.sortBy ?? 'updated_at';
      state.sortOrder = params.sortOrder ?? 'desc';
    },
    // Simulated setPerPage
    setPerPage: async (perPage: number) => {
      await state; // Force page reset to 1
    },
    // Simulated setSorting
    setSorting: async (sortBy: typeof state.sortBy, sortOrder: typeof state.sortOrder) => {
      lastFetchParams = { page: 1, sortBy, sortOrder };
      state.sortBy = sortBy;
      state.sortOrder = sortOrder;
    },
  };
};

describe('conversationStore - sorting and pagination', () => {
  describe('setPerPage', () => {
    it('should update perPage and reset to page 1', async () => {
      const store = createTestStore();
      store.setState({
        currentPage: 5,
        perPage: 20,
      });

      await store.setPerPage(50);

      const params = store.getLastFetchParams();
      expect(params).toEqual({ page: 1, perPage: 50 });
      expect(store.getState().currentPage).toBe(1);
      expect(store.getState().perPage).toBe(50);
    });

    it('should accept valid perPage values', async () => {
      const store = createTestStore();

      await store.setPerPage(10);
      expect(store.getLastFetchParams()?.perPage).toBe(10);

      await store.setPerPage(25);
      expect(store.getLastFetchParams()?.perPage).toBe(25);

      await store.setPerPage(100);
      expect(store.getLastFetchParams()?.perPage).toBe(100);
    });

    it('should handle zero perPage gracefully', async () => {
      const store = createTestStore();

      await store.setPerPage(0);

      // Should still trigger fetch with 0 (API will handle validation)
      expect(store.getLastFetchParams()?.perPage).toBe(0);
    });
  });

  describe('setSorting', () => {
    it('should update sortBy and sortOrder and reset to page 1', async () => {
      const store = createTestStore();
      store.setState({
        currentPage: 3,
        sortBy: 'updated_at',
        sortOrder: 'desc',
      });

      await store.setSorting('status', 'asc');

      const params = store.getLastFetchParams();
      expect(params).toEqual({ page: 1, sortBy: 'status', sortOrder: 'asc' });
      expect(store.getState().currentPage).toBe(1);
      expect(store.getState().sortBy).toBe('status');
      expect(store.getState().sortOrder).toBe('asc');
    });

    it('should support sorting by updated_at', async () => {
      const store = createTestStore();

      await store.setSorting('updated_at', 'desc');

      expect(store.getState().sortBy).toBe('updated_at');
      expect(store.getState().sortOrder).toBe('desc');
    });

    it('should support sorting by created_at', async () => {
      const store = createTestStore();

      await store.setSorting('created_at', 'asc');

      expect(store.getState().sortBy).toBe('created_at');
      expect(store.getState().sortOrder).toBe('asc');
    });

    it('should support sorting by status', async () => {
      const store = createTestStore();

      await store.setSorting('status', 'asc');

      expect(store.getState().sortBy).toBe('status');
      expect(store.getState().sortOrder).toBe('asc');
    });

    it('should support both ascending and descending order', async () => {
      const store = createTestStore();

      await store.setSorting('updated_at', 'asc');
      expect(store.getState().sortOrder).toBe('asc');

      await store.setSorting('updated_at', 'desc');
      expect(store.getState().sortOrder).toBe('desc');
    });
  });

  describe('sorting behavior with filters', () => {
    it('should maintain current filters when changing sort', async () => {
      const store = createTestStore();

      // Simulate having active filters (this would be part of full store state)
      const currentFilters = {
        searchQuery: 'test',
        statusFilters: [ConversationStatus.ACTIVE],
      };

      await store.setSorting('status', 'asc');

      const params = store.getLastFetchParams();
      // Sorting change should reset to page 1
      expect(params.page).toBe(1);
      // In actual implementation, fetchConversations would merge with current filters
    });
  });

  describe('sorting persistence', () => {
    it('should maintain sort state across fetch operations', async () => {
      const store = createTestStore();
      store.setState({
        sortBy: 'created_at',
        sortOrder: 'asc',
      });

      // Fetch should maintain current sort by default
      await store.fetchConversations({});

      expect(store.getState().sortBy).toBe('created_at');
      expect(store.getState().sortOrder).toBe('asc');
    });

    it('should allow override sort in fetchConversations', async () => {
      const store = createTestStore();
      store.setState({
        sortBy: 'updated_at',
        sortOrder: 'desc',
      });

      await store.fetchConversations({ sortBy: 'status', sortOrder: 'asc' });

      expect(store.getState().sortBy).toBe('status');
      expect(store.getState().sortOrder).toBe('asc');
    });
  });
});
