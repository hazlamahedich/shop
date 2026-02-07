/**
 * Conversations Store - Zustand state management for conversation list
 * Handles fetching, pagination, sorting, filtering, and loading states
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  Conversation,
  ConversationsListParams,
  PaginationMeta,
  ConversationsFilterState,
  SavedFilter,
  ConversationStatus,
  Sentiment,
} from '../types/conversation';
import { conversationsService } from '../services/conversations';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface ConversationsState {
  // Data
  conversations: Conversation[];
  pagination: PaginationMeta | null;

  // UI state
  loadingState: LoadingState;
  error: string | null;

  // Query params
  currentPage: number;
  perPage: number;
  sortBy: 'updated_at' | 'status' | 'created_at';
  sortOrder: 'asc' | 'desc';

  // Filter state
  filters: ConversationsFilterState;
  savedFilters: SavedFilter[];

  // Actions - Pagination and Sorting
  fetchConversations: (params?: ConversationsListParams) => Promise<void>;
  nextPage: () => Promise<void>;
  prevPage: () => Promise<void>;
  setPerPage: (perPage: number) => Promise<void>;
  setSorting: (sortBy: ConversationsState['sortBy'], sortOrder: ConversationsState['sortOrder']) => Promise<void>;

  // Actions - Filters
  setSearchQuery: (query: string) => Promise<void>;
  setDateRange: (from: string | null, to: string | null) => Promise<void>;
  setStatusFilters: (statuses: ConversationStatus[]) => Promise<void>;
  setSentimentFilters: (sentiments: Sentiment[]) => Promise<void>;
  setHasHandoffFilter: (hasHandoff: boolean | null) => Promise<void>;
  removeFilter: (key: keyof ConversationsFilterState, value?: any) => Promise<void>;
  clearAllFilters: () => Promise<void>;

  // Actions - Saved Filters
  saveCurrentFilters: (name: string) => void;
  deleteSavedFilter: (id: string) => void;
  applySavedFilter: (id: string) => Promise<void>;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
  syncWithUrl: () => Promise<void>;  // Sync filters with URL query params
  updateUrlFromState: () => void;  // Write current state to URL
}

// Initial filter state
const initialFilterState: ConversationsFilterState = {
  searchQuery: '',
  dateRange: { from: null, to: null },
  statusFilters: [],
  sentimentFilters: [],
  hasHandoffFilter: null,
};

// Initial state
const initialState = {
  conversations: [],
  pagination: null,
  loadingState: 'idle' as LoadingState,
  error: null as string | null,
  currentPage: 1,
  perPage: 20,
  sortBy: 'updated_at' as const,
  sortOrder: 'desc' as const,
  filters: initialFilterState,
  savedFilters: [],
};

// Helper to build request params from current state
const buildRequestParams = (
  state: Pick<ConversationsState, 'currentPage' | 'perPage' | 'sortBy' | 'sortOrder' | 'filters'>,
  overrides?: Partial<ConversationsListParams>
): ConversationsListParams => {
  const params: ConversationsListParams = {
    page: overrides?.page ?? state.currentPage,
    perPage: overrides?.perPage ?? state.perPage,
    sortBy: overrides?.sortBy ?? state.sortBy,
    sortOrder: overrides?.sortOrder ?? state.sortOrder,
  };

  // Add filter parameters if they have values
  if (state.filters.searchQuery) {
    params.search = state.filters.searchQuery;
  }
  if (state.filters.dateRange.from) {
    params.dateFrom = state.filters.dateRange.from;
  }
  if (state.filters.dateRange.to) {
    params.dateTo = state.filters.dateRange.to;
  }
  if (state.filters.statusFilters.length > 0) {
    params.status = state.filters.statusFilters;
  }
  if (state.filters.sentimentFilters.length > 0) {
    params.sentiment = state.filters.sentimentFilters;
  }
  if (state.filters.hasHandoffFilter !== null) {
    params.hasHandoff = state.filters.hasHandoffFilter;
  }

  return params;
};

/**
 * Update URL query parameters from current filter state
 * This enables bookmarking and sharing of filtered views
 */
const updateUrlFromStateHelper = (state: Pick<ConversationsState, 'filters'>): void => {
  if (typeof window === 'undefined') return;

  const url = new URL(window.location.href);
  const params = url.searchParams;

  // Clear existing filter params
  params.delete('search');
  params.delete('date_from');
  params.delete('date_to');
  params.delete('status');
  params.delete('sentiment');
  params.delete('has_handoff');

  // Add current filter state to URL
  if (state.filters.searchQuery) {
    params.set('search', state.filters.searchQuery);
  }
  if (state.filters.dateRange.from) {
    params.set('date_from', state.filters.dateRange.from);
  }
  if (state.filters.dateRange.to) {
    params.set('date_to', state.filters.dateRange.to);
  }
  state.filters.statusFilters.forEach((s) => params.append('status', s));
  state.filters.sentimentFilters.forEach((s) => params.append('sentiment', s));
  if (state.filters.hasHandoffFilter !== null) {
    params.set('has_handoff', String(state.filters.hasHandoffFilter));
  }

  // Update URL without triggering a page reload
  const newUrl = url.toString();
  window.history.replaceState({}, '', newUrl);
};

/**
 * Conversations store using Zustand
 */
export const useConversationStore = create<ConversationsState>()(
  persist(
    (set, get) => ({
      ...initialState,

      /**
       * Fetch conversations with optional parameters
       */
      fetchConversations: async (params = {}) => {
        const state = get();
        const requestParams = buildRequestParams(state, params);

        set({ loadingState: 'loading', error: null });

        try {
          const response = await conversationsService.getConversations(requestParams);

          set({
            conversations: response.data,
            pagination: response.meta.pagination,
            loadingState: 'success',
            currentPage: requestParams.page ?? 1,
            perPage: requestParams.perPage ?? 20,
            sortBy: requestParams.sortBy ?? 'updated_at',
            sortOrder: requestParams.sortOrder ?? 'desc',
          });
        } catch (error) {
          set({
            loadingState: 'error',
            error: error instanceof Error ? error.message : 'Failed to fetch conversations',
          });
        }
      },

      /**
       * Go to next page
       */
      nextPage: async () => {
        const { pagination, fetchConversations } = get();
        if (!pagination || pagination.page >= pagination.totalPages) return;

        await fetchConversations({ page: pagination.page + 1 });
      },

      /**
       * Go to previous page
       */
      prevPage: async () => {
        const { pagination, fetchConversations } = get();
        if (!pagination || pagination.page <= 1) return;

        await fetchConversations({ page: pagination.page - 1 });
      },

      /**
       * Set items per page
       */
      setPerPage: async (perPage: number) => {
        await get().fetchConversations({ page: 1, perPage });
      },

      /**
       * Set sorting parameters
       */
      setSorting: async (sortBy, sortOrder) => {
        await get().fetchConversations({ page: 1, sortBy, sortOrder });
      },

      /**
       * Set search query
       */
      setSearchQuery: async (query: string) => {
        set((state) => ({
          filters: { ...state.filters, searchQuery: query },
        }));
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Set date range filter
       */
      setDateRange: async (from: string | null, to: string | null) => {
        set((state) => ({
          filters: {
            ...state.filters,
            dateRange: { from, to },
          },
        }));
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Set status filters
       */
      setStatusFilters: async (statuses: ConversationStatus[]) => {
        set((state) => ({
          filters: { ...state.filters, statusFilters: statuses },
        }));
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Set sentiment filters
       */
      setSentimentFilters: async (sentiments: Sentiment[]) => {
        set((state) => ({
          filters: { ...state.filters, sentimentFilters: sentiments },
        }));
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Set handoff filter
       */
      setHasHandoffFilter: async (hasHandoff: boolean | null) => {
        set((state) => ({
          filters: { ...state.filters, hasHandoffFilter: hasHandoff },
        }));
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Remove a specific filter
       */
      removeFilter: async (key: keyof ConversationsFilterState, value?: any) => {
        const state = get();
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

        set({ filters: newFilters });
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Clear all filters
       */
      clearAllFilters: async () => {
        set({ filters: initialFilterState });
        updateUrlFromStateHelper(get());
        await get().fetchConversations({ page: 1 });
      },

      /**
       * Save current filters as a named filter
       */
      saveCurrentFilters: (name: string) => {
        const state = get();
        const newFilter: SavedFilter = {
          id: `filter-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          name,
          filters: { ...state.filters },
          createdAt: new Date().toISOString(),
        };
        set((state) => ({
          savedFilters: [...state.savedFilters, newFilter],
        }));
      },

      /**
       * Delete a saved filter
       */
      deleteSavedFilter: (id: string) => {
        set((state) => ({
          savedFilters: state.savedFilters.filter((f) => f.id !== id),
        }));
      },

      /**
       * Apply a saved filter
       */
      applySavedFilter: async (id: string) => {
        const state = get();
        const savedFilter = state.savedFilters.find((f) => f.id === id);
        if (savedFilter) {
          set({ filters: { ...savedFilter.filters } });
          updateUrlFromStateHelper(get());
          await get().fetchConversations({ page: 1 });
        }
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },

      /**
       * Reset store to initial state
       */
      reset: () => {
        set(initialState);
      },

      /**
       * Update URL from current filter state
       * Write current filters to URL query parameters
       */
      updateUrlFromState: () => {
        updateUrlFromStateHelper(get());
      },

      /**
       * Sync filters with URL query params
       */
      syncWithUrl: async () => {
        if (typeof window === 'undefined') return;

        const urlParams = new URLSearchParams(window.location.search);
        const state = get();
        const newFilters = { ...state.filters };
        let hasUrlParams = false;

        // Read filters from URL
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

        // Update state if URL params exist, then always fetch conversations
        if (hasUrlParams) {
          set({ filters: newFilters });
        }
        // Always fetch conversations - either with URL filters or default
        await get().fetchConversations({ page: 1 });
      },
    }),
    {
      name: 'conversation-store',
      partialize: (state) => ({
        savedFilters: state.savedFilters,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
        perPage: state.perPage,
      }),
    }
  )
);
