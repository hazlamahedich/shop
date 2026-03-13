/**
 * Shared fixtures for Story 8.10 Dashboard Mode-Aware Widgets tests
 *
 * Usage:
 * import { test, expect } from './fixtures/dashboard-fixtures';
 *
 * test('my test', async ({ generalModePage }) => {
 *   await generalModePage.goto('/dashboard');
 * });
 */

import { test as base } from '@playwright/test';
import type { Page } from '@playwright/test';

type DashboardFixtures = {
  authenticatedPage: Page;
  generalModePage: Page;
  ecommerceModePage: Page;
};

/**
 * Helper to set up auth state in localStorage
 */
function createAuthScript(mode: 'general' | 'ecommerce', hasStore: boolean = false) {
  return () => {
    const mockAuthState = {
      isAuthenticated: true,
      merchant: {
        id: 1,
        email: 'test@test.com',
        name: 'Test Merchant',
        has_store_connected: hasStore,
        store_provider: hasStore ? 'shopify' : 'none',
        onboardingMode: mode,
      },
      sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
      isLoading: false,
      error: null,
    };
    localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));

    const mockOnboardingState = {
      state: {
        completedSteps: ['prerequisites', 'deploy', 'connect', 'config'],
        currentPhase: 'complete',
        personalityConfigured: true,
        businessInfoConfigured: true,
        botNamed: true,
        greetingsConfigured: true,
        pinsConfigured: true,
        isFullyOnboarded: true,
        onboardingCompletedAt: new Date().toISOString(),
      },
      version: 0,
    };
    localStorage.setItem('shop_onboarding_phase_progress', JSON.stringify(mockOnboardingState));

    const mockTutorialState = {
      state: {
        isStarted: false,
        isCompleted: true,
        isSkipped: false,
        currentStep: 0,
        completedSteps: [],
      },
      version: 0,
    };
    localStorage.setItem('shop-tutorial-storage', JSON.stringify(mockTutorialState));
  };
}

/**
 * Base authenticated page with common mocks
 */
export const test = base.extend<DashboardFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await page.addInitScript(createAuthScript('ecommerce', true));

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            merchant_key: 'test-merchant',
            has_store_connected: true,
            store_provider: 'shopify',
            onboardingMode: 'ecommerce',
          },
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null }),
      });
    });

    await use(page);
  },

  generalModePage: async ({ page }, use) => {
    await page.addInitScript(createAuthScript('general', false));

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            merchant_key: 'test-merchant',
            has_store_connected: false,
            store_provider: 'none',
            onboardingMode: 'general',
          },
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null }),
      });
    });

    await use(page);
  },

  ecommerceModePage: async ({ page }, use) => {
    await page.addInitScript(createAuthScript('ecommerce', true));

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            merchant_key: 'test-merchant',
            has_store_connected: true,
            store_provider: 'shopify',
            onboardingMode: 'ecommerce',
          },
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null }),
      });
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';
