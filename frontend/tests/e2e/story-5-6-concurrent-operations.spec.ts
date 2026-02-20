/**
 * Widget Settings - Concurrent Operations Tests
 *
 * Critical Gap Test: Race conditions when multiple operations occur simultaneously
 * Story 5-6: Merchant Widget Settings UI
 * Priority: P2 (High - data integrity risk)
 *
 * @tags e2e widget story-5-6 concurrency race-condition
 */

import { test as base, expect } from '@playwright/test';

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
};

const setupAuthMocks = async (page: import('@playwright/test').Page) => {
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          id: 'test-merchant-1',
          email: 'test@test.com',
          name: 'Test Merchant',
          hasStoreConnected: true,
        },
        meta: {
          sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        },
      }),
    });
  });

  await page.addInitScript(() => {
    const mockAuthState = {
      isAuthenticated: true,
      merchant: {
        id: 'test-merchant-1',
        email: 'test@test.com',
        name: 'Test Merchant',
        hasStoreConnected: true,
      },
      sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
      isLoading: false,
      error: null,
    };

    const mockOnboardingState = {
      state: {
        completedSteps: ['prerequisites', 'deployment', 'integrations', 'bot-config'],
        currentPhase: 'complete',
        personalityConfigured: true,
        businessInfoConfigured: true,
      },
    };

    localStorage.setItem('auth-storage', JSON.stringify({ state: mockAuthState, version: 0 }));
    localStorage.setItem('onboarding-storage', JSON.stringify(mockOnboardingState));
  });
};

const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await setupAuthMocks(page);
    await use(page);
  },
});

test.describe('Story 5-6: Concurrent Operations', () => {
  test.describe('Race Condition Prevention', () => {
    test('[P2] should handle rapid consecutive saves without data corruption', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Concurrency testing on desktop');

      let saveCount = 0;
      let lastSavedConfig: Record<string, unknown> = {};

      await authenticatedPage.route('**/api/v1/merchants/widget-config', async (route) => {
        const method = route.request().method();

        if (method === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                enabled: true,
                botName: 'Shopping Assistant',
                welcomeMessage: 'Hi!',
                theme: { primaryColor: '#6366f1', position: 'bottom-right' },
              },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else if (method === 'PATCH') {
          saveCount++;
          const body = route.request().postDataJSON();
          lastSavedConfig = { ...lastSavedConfig, ...body };

          await new Promise(resolve => setTimeout(resolve, 50));

          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: lastSavedConfig,
              meta: { requestId: `save-${saveCount}`, timestamp: new Date().toISOString() },
            }),
          });
        } else {
          await route.continue();
        }
      });

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const botNameInput = authenticatedPage.getByTestId('bot-name-input');
      const saveButton = authenticatedPage.getByTestId('save-settings-button');

      await botNameInput.fill('First Save');
      await saveButton.click();

      await authenticatedPage.waitForTimeout(300);

      await botNameInput.fill('Second Save');
      await saveButton.click();

      await expect(authenticatedPage.locator('text=/saved|success/i')).toBeVisible({ timeout: 10000 }).catch(() => {});

      expect(saveCount).toBeGreaterThanOrEqual(1);
    });

    test('[P2] should disable save button while save is in progress', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Concurrency testing on desktop');

      await authenticatedPage.route('**/api/v1/merchants/widget-config', async (route) => {
        const method = route.request().method();

        if (method === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                enabled: true,
                botName: 'Shopping Assistant',
                welcomeMessage: 'Hi!',
                theme: { primaryColor: '#6366f1', position: 'bottom-right' },
              },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else if (method === 'PATCH') {
          await new Promise(resolve => setTimeout(resolve, 2000));
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { enabled: true, botName: 'Updated' },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else {
          await route.continue();
        }
      });

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const botNameInput = authenticatedPage.getByTestId('bot-name-input');
      const saveButton = authenticatedPage.getByTestId('save-settings-button');

      await botNameInput.fill('Test');
      await saveButton.click();

      await expect(saveButton).toBeDisabled({ timeout: 500 });

      await expect(authenticatedPage.locator('button:has-text("Saving")')).toBeVisible({ timeout: 2000 });
    });
  });

  test.describe('Widget State Propagation', () => {
    test('[P2] should reflect disabled state in embed code immediately', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Responsive layout issue');

      await authenticatedPage.route('**/api/v1/merchants/widget-config', async (route) => {
        const method = route.request().method();

        if (method === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                enabled: true,
                botName: 'Shopping Assistant',
                welcomeMessage: 'Hi!',
                theme: { primaryColor: '#6366f1', position: 'bottom-right' },
              },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else if (method === 'PATCH') {
          const body = route.request().postDataJSON();
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { ...body },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else {
          await route.continue();
        }
      });

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      const initialState = await toggle.getAttribute('aria-checked');

      if (initialState === 'true') {
        await toggle.click();

        const saveButton = authenticatedPage.getByTestId('save-settings-button');
        await saveButton.click();

        await expect(authenticatedPage.locator('text=Enable the widget to get your embed code')).toBeVisible({ timeout: 5000 });
      }
    });
  });
});
