/**
 * E2E Test: Onboarding Mode Selection - Error Handling
 *
 * Story 8-6: Frontend Onboarding Mode Selection
 * Tests error handling for mode selection
 *
 * @tags e2e onboarding story-8-6 error-handling
 */

import { test, expect } from '@playwright/test';
import { OnboardingMode } from './pageobjects/onboarding-mode.po';

test.describe.serial('Story 8-6: Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: false,
          store_provider: 'none',
        },
        sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        isLoading: false,
        error: null,
      };
      localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
      // Remove onboarding state to start fresh
      localStorage.removeItem('shop_onboarding_prerequisites');
      localStorage.removeItem('onboarding-storage');
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            has_store_connected: false,
            store_provider: 'none',
          },
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: null,
          meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
        }),
      });
    });
  });

  test('[8.6-E2E-018][P2] should handle API failure gracefully', async ({ page }) => {
    // Setup: Route PATCH /api/merchant/mode to return 500 error
    await page.route('**/api/merchant/mode', async (route) => {
      const request = route.request();
      if (request.method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Internal server error' },
          }),
        });
      } else if (request.method() === 'GET') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Mode not found' },
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock CSRF token endpoint
    await page.route('**/api/v1/csrf-token*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          csrf_token: 'test-csrf-token',
        }),
      });
    });

    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');
    
    // Reset onboarding store state to ensure fresh start
    await page.evaluate(() => {
      localStorage.removeItem('shop_onboarding_prerequisites');
      // Force reload to reset React state
      window.location.reload();
    });
    await page.waitForLoadState('domcontentloaded');

    // Verify mode selection container is visible
    const container = page.locator(OnboardingMode.container);
    await expect(container).toBeVisible({ timeout: 10000 });

    // Select a mode
    await page.locator(OnboardingMode.modeCards.general).click();

    // Click continue - this should trigger the API error
    await page.locator(OnboardingMode.continueButton).click();

    // Wait for error message to appear
    const errorMessage = page.locator('[data-testid="mode-error-message"]');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });

    // Verify error message contains helpful text
    await expect(errorMessage).toContainText(/failed|error|try again/i);

    // Verify we're still on the mode selection screen (didn't navigate away)
    await expect(container).toBeVisible();

    // Verify the mode is still selected (not cleared)
    const selectedCard = page.locator(OnboardingMode.modeCards.general);
    await expect(selectedCard).toHaveAttribute('aria-pressed', 'true');
  });

  test('[8.6-E2E-019][P2] should allow retry after API failure', async ({ page }) => {
    // Setup: First PATCH call fails, second succeeds
    let patchCallCount = 0;
    await page.route('**/api/merchant/mode', async (route) => {
      const request = route.request();
      if (request.method() === 'PATCH') {
        patchCallCount++;
        if (patchCallCount === 1) {
          // First call fails
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              error: { message: 'Internal server error' },
            }),
          });
        } else {
          // Second call succeeds
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              mode: 'general',
              message: 'Mode updated successfully',
            }),
          });
        }
      } else if (request.method() === 'GET') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Mode not found' },
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock CSRF token endpoint
    await page.route('**/api/v1/csrf-token*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          csrf_token: 'test-csrf-token',
        }),
      });
    });

    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    // Verify mode selection container is visible
    const container = page.locator(OnboardingMode.container);
    await expect(container).toBeVisible({ timeout: 10000 });

    // Select a mode
    await page.locator(OnboardingMode.modeCards.general).click();

    // Click continue - this should trigger the first API error
    await page.locator(OnboardingMode.continueButton).click();

    // Wait for error message to appear
    const errorMessage = page.locator('[data-testid="mode-error-message"]');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });

    // Click retry button
    const retryButton = page.locator('[data-testid="mode-retry-button"]');
    await expect(retryButton).toBeVisible();
    await retryButton.click();

    // After retry succeeds, should navigate to prerequisites step
    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });

    // Verify error message is gone
    await expect(errorMessage).not.toBeVisible();

    // Verify PATCH was called twice (initial + retry)
    expect(patchCallCount).toBe(2);
  });
});
