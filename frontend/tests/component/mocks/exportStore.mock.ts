/**
 * Mock Zustand Store for Playwright Component Testing
 *
 * This file provides a mock implementation of the export store that can be controlled
 * from component tests. It replaces the actual Zustand store during testing.
 */

import { vi } from 'vitest';

// Mock export store state that can be manipulated by tests
let mockExportState = {
  status: 'idle' as 'idle' | 'preparing' | 'exporting' | 'completed' | 'error',
  progress: 0,
  error: null as string | null,
  options: {} as any,
  metadata: null as any,
  isOptionsModalOpen: false,
};

// Track function calls
const mockFunctions = {
  openOptionsModal: vi.fn(() => {
    mockExportState.isOptionsModalOpen = true;
  }),
  closeOptionsModal: vi.fn(() => {
    mockExportState.isOptionsModalOpen = false;
  }),
  setExportOptions: vi.fn((options: any) => {
    mockExportState.options = options;
  }),
  startExport: vi.fn(() => Promise.resolve()),
  cancelExport: vi.fn(() => {
    mockExportState.status = 'idle';
    mockExportState.progress = 0;
    mockExportState.error = null;
    mockExportState.metadata = null;
  }),
  clearError: vi.fn(() => {
    mockExportState.error = null;
  }),
  reset: vi.fn(() => {
    mockExportState = {
      status: 'idle',
      progress: 0,
      error: null,
      options: {},
      metadata: null,
      isOptionsModalOpen: false,
    };
  }),
};

/**
 * Mock useExportStore hook
 * Returns current mock state and mock functions
 */
export const useExportStore = vi.fn(() => ({
  ...mockExportState,
  ...mockFunctions,
}));

/**
 * Helper to set mock state from tests
 * Call this before mounting a component to set the desired state
 */
export function setMockExportState(state: Partial<typeof mockExportState>) {
  mockExportState = { ...mockExportState, ...state };
}

/**
 * Helper to get mock functions for assertions
 */
export function getMockExportFunctions() {
  return mockFunctions;
}

/**
 * Helper to reset mock state between tests
 */
export function resetMockExportState() {
  mockExportState = {
    status: 'idle',
    progress: 0,
    error: null,
    options: {},
    metadata: null,
    isOptionsModalOpen: false,
  };
  Object.values(mockFunctions).forEach(fn => {
    if (typeof fn === 'function') {
      fn.mockClear();
    }
  });
}
