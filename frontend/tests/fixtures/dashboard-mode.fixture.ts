/**
 * Dashboard Mode-Aware Widget Fixture
 *
 * Provides setup for testing dashboard widget visibility based on merchant onboarding mode.
 */

import { test as base, Page } from '@playwright/test';

export type OnboardingMode = 'general' | 'ecommerce';

export type MockMerchant = {
  id: number;
  email: string;
  name: string;
  has_store_connected: boolean;
  store_provider: 'none' | 'shopify';
  onboardingMode: OnboardingMode;
}

export type MockAuthState = {
  isAuthenticated: boolean;
  merchant: MockMerchant;
  sessionExpiresAt: string;
  isLoading: boolean;
  error: string | null;
}

export type DashboardModeFixtures = {
  dashboardPage: Page;
  setupDashboardMode: (mode: OnboardingMode) => Promise<void>;
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

export const dashboardModeFixture = base.extend<DashboardModeFixtures>({
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
    }

    await use(setupDashboard)
  },

  dashboardPage: async ({ page, setupDashboardMode }, use) => {
    await setupDashboardMode('general');
    await use(page)
  },
})

export const test = dashboardModeFixture
export const expect = test.expect
