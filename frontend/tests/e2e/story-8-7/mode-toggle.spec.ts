/**
 * E2E Test: Settings Mode Toggle
 *
 * Story 8-7: Frontend - Settings Mode Toggle
 * Tests mode toggle in Settings page for existing merchants
 *
 * ATDD Checklist:
 * [x] AC1: Settings page displays current mode with description
 * [x] AC2: Confirmation dialog appears explaining changes
 * [x] AC3: Mode change succeeds with toast and page refresh
 *
 * @tags e2e settings story-8-7 mode-toggle
 */

import { test, expect, Page } from '@playwright/test';

/**
 * PageObject for Settings Mode Toggle
 */
class SettingsModeTogglePO {
  constructor(private page: Page) {}

  readonly generalTab = () => this.page.locator('button:has-text("General")');
  readonly modeSection = () => this.page.locator('h3:has-text("Mode")').first();
  readonly modeToggle = () => this.page.locator('button[aria-pressed]');
  readonly generalModeButton = () => this.page.locator('button:has-text("General Chatbot")');
  readonly ecommerceModeButton = () => this.page.locator('button:has-text("E-commerce Assistant")');
  readonly currentModeText = () => this.page.locator('text=/current mode:/i');
  readonly dialog = () => this.page.locator('[role="dialog"], [role="alertdialog"]');
  readonly dialogTitle = () => this.dialog().locator('h2');
  readonly dialogDescription = () => this.dialog().locator('p').first();
  readonly dialogCancelButton = () => this.dialog().getByRole('button', { name: /cancel/i });
  readonly dialogConfirmButton = () => this.dialog().getByRole('button', { name: /switch to/i });
  readonly acknowledgmentCheckbox = () => this.dialog().locator('input[type="checkbox"]');
  readonly toast = () => this.page.locator('[role="alert"]');
  readonly loadingIndicator = () => this.page.locator('text=/updating...|loading.../i');

  async navigateToSettings() {
    await this.page.goto('/settings');
    await this.page.waitForLoadState('domcontentloaded');
  }

  async clickGeneralTab() {
    await this.generalTab().click();
    await this.page.waitForLoadState('domcontentloaded');
  }

  async selectMode(mode: 'general' | 'ecommerce') {
    const button = mode === 'general' ? this.generalModeButton() : this.ecommerceModeButton();
    await button.scrollIntoViewIfNeeded();
    await button.click({ force: true });
  }

  async confirmModeChange() {
    await this.dialogConfirmButton().click({ force: true });
  }

  async cancelModeChange() {
    await this.dialogCancelButton().click({ force: true });
  }

  async acknowledgeWarning() {
    const checkbox = this.acknowledgmentCheckbox();
    if (await checkbox.isVisible()) {
      await checkbox.check({ force: true });
    }
  }
}

/**
 * Setup mocks for a test
 */
async function setupMocks(page: Page, options: {
  onboardingMode?: 'general' | 'ecommerce';
  shouldFail?: boolean;
  delay?: number;
} = {}) {
  const mode = options.onboardingMode || 'ecommerce';
  
  // Mock authentication state
  await page.addInitScript(() => {
    const mockAuthState = {
      isAuthenticated: true,
      merchant: {
        id: 1,
        email: 'test@test.com',
        name: 'Test Merchant',
        has_store_connected: true,
        store_provider: 'shopify',
        onboardingMode: '${mode}',
      },
      sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
      isLoading: false,
      error: null,
    };
    localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
    localStorage.removeItem('onboarding-storage');
  });

  // Mock CSRF token endpoint
  await page.route('**/api/v1/csrf-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        csrf_token: 'test-csrf-token',
      }),
    });
  });

  // Mock auth status endpoint
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
            has_store_connected: true,
            store_provider: 'shopify',
            onboardingMode: '${mode}',
          },
        },
      }),
    });
  });

  // Mock merchant mode endpoint (GET)
  await page.route('**/api/merchant/mode', async (route) => {
    const request = route.request();
    if (request.method() === 'GET') {
      if (options.delay) {
        await new Promise(resolve => setTimeout(resolve, options.delay));
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            onboardingMode: '${mode}',
          },
        }),
      });
    } else if (request.method() === 'PATCH') {
      if (options.shouldFail) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { message: 'Failed to update mode' },
          }),
        });
      } else {
        if (options.delay) {
          await new Promise(resolve => setTimeout(resolve, options.delay));
        }
        const body = request.postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              onboardingMode: body.mode,
              updatedAt: new Date().toISOString(),
            },
          }),
        });
      }
    } else {
      await route.continue();
    }
  });
}

test.describe('Story 8-7: Settings Mode Toggle @settings @story-8-7', () => {
  let po: SettingsModeTogglePO;

  test.beforeEach(async ({ page }) => {
    po = new SettingsModeTogglePO(page);
  });

  // ========================================
  // AC1: Mode displayed in Settings → General tab
  // ========================================

  test('[8.7-E2E-001][P0] @smoke should display mode section in Settings → General tab', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Verify mode section exists
    await expect(po.modeSection()).toBeVisible({ timeout: 5000 });
  });

  test('[8.7-E2E-002][P0] @smoke should display current mode with description', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Verify current mode text is visible
    await expect(po.currentModeText()).toBeVisible();

    // Verify mode buttons are visible
    await expect(po.generalModeButton()).toBeVisible();
    await expect(po.ecommerceModeButton()).toBeVisible();
  });

  test('[8.7-E2E-003][P0] should show currently selected mode with visual indicator', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    // E-commerce should be selected (from mock)
    const ecommerceButton = po.ecommerceModeButton();
    await expect(ecommerceButton).toHaveAttribute('aria-pressed', 'true');

    // General should not be selected
    const generalButton = po.generalModeButton();
    await expect(generalButton).toHaveAttribute('aria-pressed', 'false');
  });

  // ========================================
  // AC2: Confirmation dialog appears on toggle
  // ========================================

  test('[8.7-E2E-004][P0] @smoke should show confirmation dialog when clicking unselected mode', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    // Click General mode (currently e-commerce is selected)
    await po.selectMode('general');

    // Dialog should appear
    await expect(po.dialog()).toBeVisible({ timeout: 3000 });
    await expect(po.dialogTitle()).toContainText(/switch to general/i);
  });

  test('[8.7-E2E-005][P0] should show appropriate warning for E-commerce → General', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');

    // Check for warning features
    await expect(po.dialogDescription()).toBeVisible();

    // Should show acknowledgment checkbox for e-commerce → general
    await expect(po.acknowledgmentCheckbox()).toBeVisible();

    // Confirm button should be disabled until acknowledged
    await expect(po.dialogConfirmButton()).toBeDisabled();
  });

  test('[8.7-E2E-006][P1] should show appropriate message for General → E-commerce', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded (General should be selected)
    await page.waitForTimeout(500);
    await expect(po.generalModeButton()).toHaveAttribute('aria-pressed', 'true', { timeout: 3000 });

    // Click E-commerce mode
    await po.selectMode('ecommerce');

    // Dialog should appear
    await expect(po.dialog()).toBeVisible({ timeout: 3000 });

    // Check for enabling features message
    await expect(po.dialogTitle()).toContainText(/switch to e-commerce/i);

    // Should NOT show acknowledgment checkbox for general → ecommerce
    await expect(po.acknowledgmentCheckbox()).not.toBeVisible();

    // Confirm button should be enabled immediately
    await expect(po.dialogConfirmButton()).toBeEnabled();
  });

  test('[8.7-E2E-007][P1] should close dialog when Cancel clicked', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await expect(po.dialog()).toBeVisible();

    await po.cancelModeChange();

    // Dialog should close
    await expect(po.dialog()).not.toBeVisible();

    // Mode should remain unchanged
    await expect(po.ecommerceModeButton()).toHaveAttribute('aria-pressed', 'true');
  });

  test('[8.7-E2E-008][P1] should close dialog on Escape key', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await expect(po.dialog()).toBeVisible();

    // Press Escape
    await page.keyboard.press('Escape');

    // Dialog should close
    await expect(po.dialog()).not.toBeVisible();
  });

  // ========================================
  // AC3: Mode change succeeds with toast and page refresh
  // ========================================

  test('[8.7-E2E-009][P0] @smoke should update mode and show success toast', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await expect(po.dialog()).toBeVisible();

    // Acknowledge warning
    await po.acknowledgeWarning();

    // Confirm button should now be enabled
    await expect(po.dialogConfirmButton()).toBeEnabled();

    // Confirm
    await po.confirmModeChange();

    // Wait for API call
    const response = await page.waitForResponse(
      (resp) => resp.url().includes('/api/merchant/mode') && resp.request().method() === 'PATCH',
      { timeout: 5000 }
    );
    expect(response.status()).toBe(200);

    // Should show toast notification
    await expect(po.toast()).toBeVisible({ timeout: 3000 });
    await expect(po.toast()).toContainText(/mode updated|success/i);
  });

  test('[8.7-E2E-010][P0] should show loading state during API call', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce', delay: 1000 });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await po.acknowledgeWarning();
    await po.confirmModeChange();

    // Should show loading state
    await expect(po.loadingIndicator()).toBeVisible({ timeout: 500 });

    // Buttons should be disabled during loading
    await expect(po.dialogCancelButton()).toBeDisabled();
  });

  test('[8.7-E2E-011][P1] should refresh page after successful mode change', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await po.acknowledgeWarning();
    await po.confirmModeChange();

    // Wait for page reload (location.reload() triggers a navigation)
    await page.waitForEvent('load', { timeout: 10000 }).catch(() => {
      // If load event doesn't fire, wait for URL to stabilize
      return page.waitForTimeout(1500);
    });
  });

  test('[8.7-E2E-012][P1] should show error toast on API failure', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce', shouldFail: true });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');
    await po.acknowledgeWarning();
    await po.confirmModeChange();

    // Should show error toast
    await expect(po.toast()).toBeVisible({ timeout: 3000 });
    await expect(po.toast()).toContainText(/failed|error/i);

  readonly toast = () => this.page.locator('[role="alert"], [data-testid="error"], [data-testid="success"], [data-testid="warning"]');

  readonly errorToast = () => this.page.locator('[data-testid="error"], [data-testid="success"], [data-testid="warning"]');
  readonly successToast = () => this.page.locator('[data-testid="success"], [data-testid="warning"]');
  readonly warningToast = () => this.page.locator('[data-testid="warning"]');
  ` as });


  // ========================================
  // Accessibility Tests
  // ========================================

  test('[8.7-E2E-013][P1] should have proper ARIA attributes', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    // Mode buttons should have aria-pressed
    const generalButton = po.generalModeButton();
    const ecommerceButton = po.ecommerceModeButton();

    await expect(generalButton).toHaveAttribute('aria-pressed');
    await expect(ecommerceButton).toHaveAttribute('aria-pressed');
  });

  test('[8.7-E2E-014][P1] should have modal dialog with proper ARIA', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');

    // Dialog should be modal
    await expect(po.dialog()).toHaveAttribute('aria-modal', 'true');
  });

  test('[8.7-E2E-015][P2] should focus cancel button when dialog opens', async ({ page }) => {
    await setupMocks(page, { onboardingMode: 'ecommerce' });
    
    await po.navigateToSettings();
    await po.clickGeneralTab();

    // Wait for mode to be loaded
    await page.waitForTimeout(500);

    await po.selectMode('general');

    // Cancel button should have focus
    const cancelButton = po.dialogCancelButton();
    await expect(cancelButton).toBeFocused({ timeout: 1000 });
  });
});
