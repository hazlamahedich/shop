/**
 * Conversations Store - Zustand state management for conversation list
 * Handles fetching, pagination, sorting, and loading states
 */

import { create } from 'zustand';
import type {
  Conversation,
  ConversationsListParams,
  PaginationMeta,
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

  // Actions
  fetchConversations: (params?: ConversationsListParams) => Promise<void>;
  nextPage: () => Promise<void>;
  prevPage: () => Promise<void>;
  setPerPage: (perPage: number) => Promise<void>;
  setSorting: (sortBy: ConversationsState['sortBy'], sortOrder: ConversationsState['sortOrder']) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

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
};

/**
 * Conversations store using Zustand
 */
export const useConversationStore = create<ConversationsState>((set, get) => ({
  ...initialState,

  /**
   * Fetch conversations with optional parameters
   */
  fetchConversations: async (params = {}) => {
    const { currentPage, perPage, sortBy, sortOrder } = get();

    const requestParams: ConversationsListParams = {
      page: params.page ?? currentPage,
      perPage: params.perPage ?? perPage,
      sortBy: params.sortBy ?? sortBy,
      sortOrder: params.sortOrder ?? sortOrder,
    };

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
}));
