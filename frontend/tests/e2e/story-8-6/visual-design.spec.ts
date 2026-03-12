/**
 * E2E Test: Onboarding Mode Selection - Visual Design
 *
 * Story 8-6: Frontend Onboarding Mode Selection
 * Tests visual design features for mode selection
 *
 * @tags e2e onboarding story-8-6 visual-design
 */

import { test, expect } from '@playwright/test';
import { OnboardingMode } from './pageobjects/onboarding-mode.po';

test.describe.serial('Story 8-6: Visual Design', () => {
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

    await page.route('**/api/merchant/mode', async (route) => {
      const request = route.request();
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Mode not found' },
            meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
          }),
        });
      } else {
        await route.continue();
      }
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

  test('[8.6-E2E-015][P2] should show visual feedback on mode selection', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);

    await generalCard.click();
    await expect(generalCard).toHaveAttribute('aria-pressed', 'true');

    await ecommerceCard.click();
    await expect(ecommerceCard).toHaveAttribute('aria-pressed', 'true');
    await expect(generalCard).toHaveAttribute('aria-pressed', 'false');
  });

  test('[8.6-E2E-016][P2] should show icons or images for each mode', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    const generalIcon = generalCard.locator('svg, img, [data-testid*="icon"]');
    const hasGeneralIcon = (await generalIcon.count()) > 0;
    expect(hasGeneralIcon).toBe(true);

    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);
    const ecommerceIcon = ecommerceCard.locator('svg, img, [data-testid*="icon"]');
    const hasEcommerceIcon = (await ecommerceIcon.count()) > 0;
    expect(hasEcommerceIcon).toBe(true);
  });

  test('[8.6-E2E-017][P2] should show mode descriptions', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    const generalText = await generalCard.textContent();
    expect(generalText).toMatch(/general|chatbot|ai assistant/i);

    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);
    const ecommerceText = await ecommerceCard.textContent();
    expect(ecommerceText).toMatch(/e-commerce|shopify|store/i);
  });
});
