/**
 * Playwright Component Testing Setup
 *
 * This file configures mocks for Zustand stores used in component tests.
 * It runs before all component tests to provide isolated, controllable state.
 */

import { test } from '@playwright/experimental-ct-react';
import { vi } from 'vitest';
import * as exportStoreMock from './mocks/exportStore.mock';
import * as conversationStoreMock from './mocks/conversationStore.mock';

// Mock the store modules
vi.mock('@/stores/exportStore', () => ({
  useExportStore: exportStoreMock.useExportStore,
}));

vi.mock('@/stores/conversationStore', () => ({
  useConversationStore: conversationStoreMock.useConversationStore,
}));

// Reset mock state before each test
test.beforeEach(() => {
  exportStoreMock.resetMockExportState();
  conversationStoreMock.resetMockConversationState();
});
