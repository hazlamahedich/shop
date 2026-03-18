/**
 * E2E Test: Dashboard Mode-Aware Widgets
 * Story 8.10: Frontend Dashboard Mode-Aware Widgets
 * Tests mode-aware widget visibility on dashboard
 *
 * ATDD Checklist
 * [x] AC1: General mode hides Shopify widgets
 * [x] AC2: E-commerce mode shows all widgets
 * [x] AC3: Mode switch updates widgets
 * [x] AC4: General mode shows Knowledge Base widget
 *
 * @tags e2e dashboard story-8-10 mode-visibility
 */

import { test, expect } from '@playwright/test';

test.describe.serial('Story 8.10: Dashboard Mode-Aware Widgets @dashboard @story-8-10', () => {
  test('[8.10-E2E-001][P0] @smoke General mode hides Shopify widgets', async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: false,
          store_provider: 'none',
          onboardingMode: 'general',
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
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: false,
              store_provider: 'none',
              onboardingMode: 'general',
            },
          },
          meta: {},
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null, meta: {} }),
      });
    });

    await page.route('**/api/v1/csrf-token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ csrf_token: 'mock-csrf-token' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByTestId('conversation-overview-widget-container')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('handoff-queue-widget-container')).toBeVisible();
    await expect(page.getByTestId('financial-overview-widget-container')).toBeVisible();
    await expect(page.getByTestId('knowledge-base-widget-container')).toBeVisible();
    await expect(page.getByTestId('peak-hours-heatmap-widget-container')).toBeVisible();
    await expect(page.getByTestId('quality-metrics-widget-container')).toBeVisible();

    // E-commerce widgets should NOT be visible in general mode
    await expect(page.getByTestId('conversion-funnel-widget-container')).not.toBeVisible();
    await expect(page.getByTestId('top-products-widget-container')).not.toBeVisible();
    await expect(page.getByTestId('geographic-widget-container')).not.toBeVisible();

    await expect(page.getByTestId('revenue-widget-container')).not.toBeVisible();
    await expect(page.getByTestId('top-products-widget-container')).not.toBeVisible();
    await expect(page.getByTestId('pending-orders-widget-container')).not.toBeVisible();
    await expect(page.getByTestId('geographic-widget-container')).not.toBeVisible();
  });

  test('[8.10-E2E-002][P0] @smoke E-commerce mode shows all widgets', async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: true,
          store_provider: 'shopify',
          onboardingMode: 'ecommerce',
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
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: true,
              store_provider: 'shopify',
              onboardingMode: 'ecommerce',
            },
          },
          meta: {},
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null, meta: {} }),
      });
    });

    await page.route('**/api/v1/csrf-token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ csrf_token: 'mock-csrf-token' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByTestId('conversation-overview-widget-container')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('handoff-queue-widget-container')).toBeVisible();
    await expect(page.getByTestId('financial-overview-widget-container')).toBeVisible();
    await expect(page.getByTestId('conversion-funnel-widget-container')).toBeVisible();
    await expect(page.getByTestId('top-products-widget-container')).toBeVisible();
    await expect(page.getByTestId('geographic-widget-container')).toBeVisible();
    await expect(page.getByTestId('peak-hours-heatmap-widget-container')).toBeVisible();
    await expect(page.getByTestId('quality-metrics-widget-container')).toBeVisible();
  });

  test('[8.10-E2E-003][P1] Mode switch updates widgets correctly', async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: true,
          store_provider: 'shopify',
          onboardingMode: 'ecommerce',
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
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: true,
              store_provider: 'shopify',
              onboardingMode: 'ecommerce',
            },
          },
          meta: {},
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null, meta: {} }),
      });
    });

    await page.route('**/api/v1/csrf-token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ csrf_token: 'mock-csrf-token' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.getByTestId('financial-overview-widget-container')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('conversion-funnel-widget-container')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('top-products-widget-container')).toBeVisible({ timeout: 15000 });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: false,
              store_provider: 'none',
              onboardingMode: 'general',
            },
          },
          meta: {},
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    // Financial overview should still be visible (shows AI cost only in general mode)
    await expect(page.getByTestId('financial-overview-widget-container')).toBeVisible({ timeout: 15000 });
    // E-commerce widgets should not be visible in general mode
    await expect(page.getByTestId('conversion-funnel-widget-container')).not.toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('top-products-widget-container')).not.toBeVisible({ timeout: 15000 });
    // Knowledge base should be visible in general mode
    await expect(page.getByTestId('knowledge-base-widget-container')).toBeVisible();
  });

  test('[8.10-E2E-004][P1] General mode shows KB widget', async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: false,
          store_provider: 'none',
          onboardingMode: 'general',
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
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: false,
              store_provider: 'none',
              onboardingMode: 'general',
            },
          },
          meta: {},
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null, meta: {} }),
      });
    });

    await page.route('**/api/v1/csrf-token', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ csrf_token: 'mock-csrf-token' }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');

    const kbWidget = page.getByTestId('knowledge-base-widget-container');
    await expect(kbWidget).toBeVisible({ timeout: 15000 });
  });
});
