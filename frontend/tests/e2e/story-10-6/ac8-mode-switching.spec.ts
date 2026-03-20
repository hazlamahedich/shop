/**
 * E2E Tests: Story 10-6 AC8 Widget Visibility by Mode
 *
 * Tests that widget visibility is correct for each onboarding mode.
 * Note: Mode switching requires backend persistence - these tests verify
 * correct rendering in each mode independently.
 */

import { test, expect, Page } from '@playwright/test';

type OnboardingMode = 'general' | 'ecommerce';

type MockMerchant = {
  id: number;
  email: string;
  name: string;
  has_store_connected: boolean;
  store_provider: 'none' | 'shopify';
  onboardingMode: OnboardingMode;
};

type MockAuthState = {
  isAuthenticated: boolean;
  merchant: MockMerchant;
  sessionExpiresAt: string;
  isLoading: boolean;
  error: string | null;
};

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

async function setupDashboardMocks(page: Page, mode: OnboardingMode) {
  const mockMerchant = createMockMerchant(mode);

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

const ECOMMERCE_ONLY_WIDGETS = {
  'top-products': 'top-products-widget-container',
  geographic: 'geographic-widget-container',
  'conversion-funnel': 'conversion-funnel-widget-container',
};

const GENERAL_ONLY_WIDGETS = {
  'knowledge-base': 'knowledge-base-widget-container',
  'feedback-analytics': 'feedback-analytics-widget-container',
};

const SHARED_WIDGETS = {
  'conversation-overview': 'conversation-overview-widget-container',
  'ai-cost': 'financial-overview-widget-container',
  'handoff-queue': 'handoff-queue-widget-container',
  'bot-quality': 'bot-quality-widget-container',
};

test.describe('AC8: Widget Visibility by Mode', () => {
  test.describe('General Mode', () => {
    test('[P0][10.6-E2E-014] should show correct widgets in General mode', async ({ page }) => {
      await page.addInitScript((state) => {
        localStorage.setItem('shop_auth_state', JSON.stringify(state));
      }, createMockAuthState('general'));

      await setupDashboardMocks(page, 'general');
      await page.goto('/dashboard');

      await expect(page.getByTestId('conversation-overview-widget-container')).toBeVisible({ timeout: 10000 });

      for (const [name, testId] of Object.entries(ECOMMERCE_ONLY_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `E-commerce widget "${name}" should be hidden`).not.toBeVisible();
      }

      for (const [name, testId] of Object.entries(GENERAL_ONLY_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `General widget "${name}" should be visible`).toBeVisible();
      }

      for (const [name, testId] of Object.entries(SHARED_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `Shared widget "${name}" should be visible`).toBeVisible();
      }
    });
  });

  test.describe('E-commerce Mode', () => {
    test('[P0][10.6-E2E-015] should show correct widgets in E-commerce mode', async ({ page }) => {
      await page.addInitScript((state) => {
        localStorage.setItem('shop_auth_state', JSON.stringify(state));
      }, createMockAuthState('ecommerce'));

      await setupDashboardMocks(page, 'ecommerce');
      await page.goto('/dashboard');

      await expect(page.getByTestId('conversation-overview-widget-container')).toBeVisible({ timeout: 10000 });

      for (const [name, testId] of Object.entries(ECOMMERCE_ONLY_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `E-commerce widget "${name}" should be visible`).toBeVisible();
      }

      for (const [name, testId] of Object.entries(GENERAL_ONLY_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `General widget "${name}" should be hidden`).not.toBeVisible();
      }

      for (const [name, testId] of Object.entries(SHARED_WIDGETS)) {
        const locator = page.getByTestId(testId);
        await expect(locator, `Shared widget "${name}" should be visible`).toBeVisible();
      }
    });
  });
});
