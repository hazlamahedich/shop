/**
 * E2E Test: Onboarding Mode Selection - Accessibility
 *
 * Story 8-6: Frontend Onboarding Mode Selection
 * Tests accessibility features for mode selection
 *
 * @tags e2e onboarding story-8-6 accessibility
 */

import { test, expect } from '@playwright/test';
import { OnboardingMode } from './pageobjects/onboarding-mode.po';

test.describe.serial('Story 8-6: Accessibility', () => {
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

  test('[8.6-E2E-011][P1] should have proper ARIA labels on mode cards', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);

    const generalRole = await generalCard.getAttribute('role');
    const ecommerceRole = await ecommerceCard.getAttribute('role');

    expect(['radio', 'button', 'option']).toContain(generalRole);
    expect(['radio', 'button', 'option']).toContain(ecommerceRole);

    await expect(generalCard).toHaveAttribute('aria-pressed', 'false');
    await expect(ecommerceCard).toHaveAttribute('aria-pressed', 'false');
  });

  test('[8.6-E2E-012][P1] should have visible focus indicators', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    await generalCard.focus();

    const outline = await generalCard.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        outlineWidth: styles.outlineWidth,
        boxShadow: styles.boxShadow,
      };
    });

    const hasFocusIndicator =
      outline.outline !== 'none' ||
      outline.outlineWidth !== '0px' ||
      outline.boxShadow !== 'none';

    expect(hasFocusIndicator).toBe(true);
  });

  test('[8.6-E2E-013][P1] should announce selected mode to screen readers', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    await generalCard.click();

    await expect(generalCard).toHaveAttribute('aria-pressed', 'true');

    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);
    await expect(ecommerceCard).toHaveAttribute('aria-pressed', 'false');
  });

  test('[8.6-E2E-014][P1] should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const h1 = page.locator('h1').nth(1);
    await expect(h1).toBeVisible();
    const h1Text = await h1.textContent();
    expect(h1Text).toMatch(/Setting Up|Shop Assistant|Onboarding/i);
  });
});
