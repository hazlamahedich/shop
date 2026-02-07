/**
 * Mock Zustand Store for Playwright Component Testing
 *
 * This file provides a mock implementation of the conversation store that can be controlled
 * from component tests. It replaces the actual Zustand store during testing.
 */

import { vi } from 'vitest';

// Default mock filters
const mockFilters = {
  searchQuery: '',
  dateRange: { from: null as string | null, to: null as string | null },
  statusFilters: [] as string[],
  sentimentFilters: [] as string[],
  hasHandoffFilter: null as boolean | null,
};

// Track function calls
const mockFunctions = {
  setSearchQuery: vi.fn(),
  setDateRange: vi.fn(),
  setStatusFilters: vi.fn(),
  setSentimentFilters: vi.fn(),
  setHasHandoffFilter: vi.fn(),
  clearAllFilters: vi.fn(),
};

/**
 * Mock useConversationStore hook
 * Returns current mock filters and mock functions
 */
export const useConversationStore = vi.fn(() => ({
  filters: mockFilters,
  ...mockFunctions,
}));

/**
 * Helper to set mock filters from tests
 * Call this before mounting a component to set the desired state
 */
export function setMockConversationFilters(filters: Partial<typeof mockFilters>) {
  Object.assign(mockFilters, filters);
}

/**
 * Helper to get mock functions for assertions
 */
export function getMockConversationFunctions() {
  return mockFunctions;
}

/**
 * Helper to reset mock state between tests
 */
export function resetMockConversationState() {
  mockFilters.searchQuery = '';
  mockFilters.dateRange = { from: null, to: null };
  mockFilters.statusFilters = [];
  mockFilters.sentimentFilters = [];
  mockFilters.hasHandoffFilter = null;
  Object.values(mockFunctions).forEach(fn => {
    if (typeof fn === 'function') {
      fn.mockClear();
    }
  });
}
