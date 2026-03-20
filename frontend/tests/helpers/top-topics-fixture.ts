/**
 * Shared fixtures for Story 10-8: Top Topics Widget tests
 */

import { test as base, Page } from '@playwright/test';

export const WIDGET_TEST_ID = 'top-topics-widget';
export const API_ENDPOINT = '**/api/v1/analytics/top-topics*';

export type OnboardingMode = 'general' | 'ecommerce';

export type MockMerchant = {
  id: number;
  email: string;
  name: string;
  has_store_connected: boolean;
  store_provider: 'none' | 'shopify';
  onboardingMode: OnboardingMode;
};

export type MockAuthState = {
  isAuthenticated: boolean;
  merchant: MockMerchant;
  sessionExpiresAt: string;
  isLoading: boolean;
  error: string | null;
};

export type DashboardFixtures = {
  setupDashboardMode: (mode: OnboardingMode) => Promise<void>;
};

export interface TopTopicsData {
  topics: Array<{ name: string; queryCount: number; trend: string }>;
  lastUpdated: string;
  period: { days: number; startDate?: string; endDate?: string };
}

const createMockMerchant = (mode: OnboardingMode): MockMerchant => ({
  id: 1,
  email: 'test@test.com',
  name: 'Test Merchant',
  has_store_connected: mode === 'ecommerce',
  store_provider: mode === 'ecommerce' ? 'shopify' : 'none',
  onboardingMode: mode,
});

const createMockAuthState = (mode: OnboardingMode): MockAuthState => ({
  isAuthenticated: true,
  merchant: createMockMerchant(mode),
  sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
  isLoading: false,
  error: null,
});

export const test = base.extend<DashboardFixtures>({
  setupDashboardMode: async ({ page }, use) => {
    const setupDashboard = async (mode: OnboardingMode) => {
      const mockAuthState = createMockAuthState(mode);
      const mockMerchant = mockAuthState.merchant;

      await page.addInitScript((state) => {
        localStorage.setItem('shop_auth_state', JSON.stringify(state));
      }, mockAuthState);

      await page.route('**/api/v1/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { merchant: mockMerchant },
            meta: {},
          }),
        });
      });

      await page.route('**/api/v1/csrf-token', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ csrf_token: 'mock-csrf-token' }),
        });
      });
    };

    await use(setupDashboard);
  },
});

export async function mockTopTopicsApi(page: Page, data: Partial<TopTopicsData> = {}) {
  const defaultData: TopTopicsData = {
    topics: [
      { name: 'shipping cost', queryCount: 45, trend: 'up' },
      { name: 'return policy', queryCount: 32, trend: 'stable' },
      { name: 'track order', queryCount: 28, trend: 'new' },
    ],
    lastUpdated: new Date().toISOString(),
    period: { days: 7, startDate: '2026-03-13T00:00:00Z', endDate: '2026-03-20T00:00:00Z' },
    ...data,
  };

  await page.route(API_ENDPOINT, async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ data: defaultData }),
    });
  });
}

export async function mockDelayedTopTopicsApi(
  page: Page,
  delayMs: number,
  data: Partial<TopTopicsData> = {}
) {
  const defaultData: TopTopicsData = {
    topics: [
      { name: 'shipping cost', queryCount: 45, trend: 'up' },
      { name: 'return policy', queryCount: 32, trend: 'stable' },
      { name: 'track order', queryCount: 28, trend: 'new' },
    ],
    lastUpdated: new Date().toISOString(),
    period: { days: 7, startDate: '2026-03-13T00:00:00Z', endDate: '2026-03-20T00:00:00Z' },
    ...data,
  };

  await page.route(API_ENDPOINT, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ data: defaultData }),
    });
  });
}

export { expect } from '@playwright/test';
