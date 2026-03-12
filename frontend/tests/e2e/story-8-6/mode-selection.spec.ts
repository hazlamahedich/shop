/**
 * E2E Test: Onboarding Mode Selection
 *
 * Story 8-6: Frontend Onboarding Mode Selection
 * Tests mode selection at start of onboarding flow
 *
 * ATDD Checklist:
 * [x] AC1: Mode selection appears first with two options
 * [x] AC2: General mode skips Facebook/Shopify, shows only LLM
 * [x] AC3: E-commerce mode shows all steps
 * [x] AC4: Mode persisted to backend
 *
 * @tags e2e onboarding story-8-6 mode-selection
 */

import { test, expect } from '@playwright/test';
import {
  OnboardingMode,
  OnboardingSteps,
} from './pageobjects/onboarding-mode.po';

test.describe.serial('Story 8-6: Onboarding Mode Selection @onboarding @story-8-6', () => {
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

  test('[8.6-E2E-001][P0] @smoke should display mode selection screen first', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const container = page.locator(OnboardingMode.container);
    await expect(container).toBeVisible();

    const title = page.locator(OnboardingMode.title);
    await expect(title).toBeVisible();
    await expect(title).toContainText(/choose|select|mode/i);
  });

  test('[8.6-E2E-002][P0] @smoke should show two mode options', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);

    await expect(generalCard).toBeVisible();
    await expect(ecommerceCard).toBeVisible();

    await expect(page.locator(OnboardingMode.modeLabels.general)).toBeVisible();
    await expect(page.locator(OnboardingMode.modeLabels.ecommerce)).toBeVisible();

    const generalDesc = page.locator(`${OnboardingMode.modeCards.general} ${OnboardingMode.modeDescription}`);
    const ecommerceDesc = page.locator(`${OnboardingMode.modeCards.ecommerce} ${OnboardingMode.modeDescription}`);

    await expect(generalDesc).toBeVisible();
    await expect(ecommerceDesc).toBeVisible();
  });

  test('[8.6-E2E-003][P0] should select general mode and continue', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    await generalCard.click();

    await expect(generalCard).toHaveAttribute('aria-pressed', 'true');

    const continueButton = page.locator(OnboardingMode.continueButton);
    await expect(continueButton).toBeEnabled();

    await continueButton.click();

    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });
  });

  test('[8.6-E2E-004][P0] should select ecommerce mode and continue', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);
    await ecommerceCard.click();

    await expect(ecommerceCard).toHaveAttribute('aria-pressed', 'true');

    const continueButton = page.locator(OnboardingMode.continueButton);
    await expect(continueButton).toBeEnabled();

    await continueButton.click();

    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });
  });

  test('[8.6-E2E-005][P1] should show general mode has fewer prerequisites', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    await page.locator(OnboardingMode.modeCards.general).click();
    await page.locator(OnboardingMode.continueButton).click();

    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });

    await expect(page.getByText('Facebook Business Account')).not.toBeVisible();
    await expect(page.getByText('Shopify Admin Access')).not.toBeVisible();
  });

  test('[8.6-E2E-006][P1] should show ecommerce mode has all prerequisites', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    await page.locator(OnboardingMode.modeCards.ecommerce).click();
    await page.locator(OnboardingMode.continueButton).click();

    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });

    await expect(page.getByText('Facebook Business Account')).toBeVisible();
    await expect(page.getByText('Shopify Admin Access')).toBeVisible();
  });

  test('[8.6-E2E-007][P1] should persist mode across page refresh', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    await page.locator(OnboardingMode.modeCards.general).click();
    await page.locator(OnboardingMode.continueButton).click();

    await expect(page.locator('h3')).toContainText('Prerequisites');
    await expect(page.locator('h3')).toBeVisible({ timeout: 10000 });

    await page.reload();

    await expect(page.locator('h3')).toContainText('Prerequisites');
    await expect(page.locator('h3')).toBeVisible({ timeout: 10000 });

    const storedMode = await page.evaluate(() => {
      const onboardingState = localStorage.getItem('shop_onboarding_prerequisites');
      if (onboardingState) {
        const parsed = JSON.parse(onboardingState);
        return parsed.onboardingMode || null;
      }
      return null;
    });

    expect(storedMode).toBe('general');
  });

  test('[8.6-E2E-008][P1] should support keyboard navigation', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const generalCard = page.locator(OnboardingMode.modeCards.general);
    await generalCard.focus();
    await expect(generalCard).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(generalCard).toHaveAttribute('aria-pressed', 'true');

    const ecommerceCard = page.locator(OnboardingMode.modeCards.ecommerce);
    await page.keyboard.press('Tab');
    await expect(ecommerceCard).toBeFocused();

    await page.keyboard.press('Space');
    await expect(ecommerceCard).toHaveAttribute('aria-pressed', 'true');
    await expect(generalCard).toHaveAttribute('aria-pressed', 'false');

    await page.keyboard.press('Tab');
    const continueButton = page.locator(OnboardingMode.continueButton);
    await expect(continueButton).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(page.locator('h3:has-text("Prerequisites")')).toBeVisible({ timeout: 10000 });
  });

  test('[8.6-E2E-009][P1] should disable continue button until mode selected', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const continueButton = page.locator(OnboardingMode.continueButton);
    await expect(continueButton).toBeDisabled();

    await page.locator(OnboardingMode.modeCards.general).click();

    await expect(continueButton).toBeEnabled();
  });

  test('[8.6-E2E-010][P1] should persist mode to localStorage', async ({ page }) => {
    await page.goto('/onboarding');
    await page.waitForLoadState('domcontentloaded');

    const container = page.locator(OnboardingMode.container);
    await expect(container).toBeVisible({ timeout: 10000 });

    await page.locator(OnboardingMode.modeCards.ecommerce).click();
    await page.locator(OnboardingMode.continueButton).click();

    await expect(page.locator('h3')).toContainText('Prerequisites');

    const storedMode = await page.evaluate(() => {
      const onboardingState = localStorage.getItem('shop_onboarding_prerequisites');
      if (onboardingState) {
        const parsed = JSON.parse(onboardingState);
        return parsed.onboardingMode || null;
      }
      return null;
    });

    expect(storedMode).toBe('ecommerce');
  });
});
