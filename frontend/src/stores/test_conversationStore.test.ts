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
    // Reset store before each test
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
});
