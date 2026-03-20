/**
 * Shared fixtures for Story 10-7: Knowledge Effectiveness Widget tests
 */

import { test as base, Page } from '@playwright/test';

export const WIDGET_TEST_ID = 'knowledge-effectiveness-widget';
export const API_ENDPOINT = '**/api/v1/analytics/knowledge-effectiveness*';

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

export interface KnowledgeEffectivenessData {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  trend: number[];
  lastUpdated: string;
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

export async function mockKnowledgeEffectivenessApi(
  page: Page,
  data: Partial<KnowledgeEffectivenessData> = {}
) {
  const defaultData: KnowledgeEffectivenessData = {
    totalQueries: 150,
    successfulMatches: 120,
    noMatchRate: 20,
    avgConfidence: 0.85,
    trend: [0.75, 0.80, 0.78, 0.82, 0.85, 0.83, 0.87],
    lastUpdated: new Date().toISOString(),
    ...data,
  };

  await page.route(
    API_ENDPOINT,
    async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ data: defaultData }),
      });
    },
    { times: 1 }
  );
}

export async function mockDelayedKnowledgeEffectivenessApi(
  page: Page,
  delayMs: number,
  data: Partial<KnowledgeEffectivenessData> = {}
) {
  const defaultData: KnowledgeEffectivenessData = {
    totalQueries: 150,
    successfulMatches: 120,
    noMatchRate: 20,
    avgConfidence: 0.85,
    trend: [0.75, 0.80, 0.78, 0.82, 0.85, 0.83, 0.87],
    lastUpdated: new Date().toISOString(),
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
