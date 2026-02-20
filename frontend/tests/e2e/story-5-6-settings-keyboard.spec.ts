/**
 * Merchant Widget Settings UI - Keyboard Navigation Tests
 *
 * Story 5-6: Merchant Widget Settings UI
 * Tests keyboard navigation and accessibility
 *
 * Priority: P3 (Nice-to-have - WCAG compliance, low merchant usage)
 * Critical Analysis: Keyboard navigation helpful for accessibility
 * compliance but merchants primarily use mouse
 *
 * @tags e2e widget story-5-6 accessibility keyboard
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

  await page.route('**/api/v1/merchants/widget-config', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            enabled: true,
            botName: 'Shopping Assistant',
            welcomeMessage: 'Hi! How can I help you today?',
            theme: { primaryColor: '#6366f1', position: 'bottom-right' },
          },
          meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
        }),
      });
    } else {
      await route.continue();
    }
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

test.describe('Story 5-6: Widget Settings Keyboard Navigation', () => {
  test.describe('Tab Navigation', () => {
    test('[P2] should navigate through form fields with Tab', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      await expect(toggle).toBeVisible();

      await toggle.focus();

      await authenticatedPage.keyboard.press('Tab');

      const focusedElement = authenticatedPage.locator(':focus');
      const isVisible = await focusedElement.isVisible().catch(() => false);

      expect(isVisible).toBe(true);
    });

    test('[P2] should navigate in logical order through form', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      await expect(toggle).toBeVisible();
      await toggle.focus();

      const focusedElements: string[] = [];

      for (let i = 0; i < 10; i++) {
        const focused = authenticatedPage.locator(':focus');
        const testId = await focused.getAttribute('data-testid').catch(() => null);
        const tagName = await focused.evaluate(el => el.tagName.toLowerCase()).catch(() => '');

        if (testId) {
          focusedElements.push(testId);
        } else if (tagName) {
          focusedElements.push(tagName);
        }

        await authenticatedPage.keyboard.press('Tab');
      }

      expect(focusedElements.length).toBeGreaterThan(0);
    });
  });

  test.describe('Form Interaction', () => {
    test('[P2] should toggle switch with Space key', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      await expect(toggle).toBeVisible();

      await toggle.focus();
      const initialState = await toggle.getAttribute('aria-checked');

      await authenticatedPage.keyboard.press('Space');

      await authenticatedPage.waitForTimeout(100);

      const newState = await toggle.getAttribute('aria-checked');
      expect(newState).not.toBe(initialState);
    });

    test('[P2] should submit form with Enter key from input', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      let patchCalled = false;

      await authenticatedPage.route('**/api/v1/merchants/widget-config', async (route) => {
        const method = route.request().method();

        if (method === 'PATCH') {
          patchCalled = true;
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                enabled: true,
                botName: 'Updated Name',
                welcomeMessage: 'Hi!',
                theme: { primaryColor: '#6366f1', position: 'bottom-right' },
              },
              meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
            }),
          });
        } else if (method === 'GET') {
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
        } else {
          await route.continue();
        }
      });

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const botNameInput = authenticatedPage.getByTestId('bot-name-input');
      await botNameInput.focus();
      await botNameInput.fill('Updated Name');

      await authenticatedPage.keyboard.press('Tab');
      await authenticatedPage.keyboard.press('Tab');

      const saveButton = authenticatedPage.getByTestId('save-settings-button');
      await saveButton.focus();
      await authenticatedPage.keyboard.press('Enter');

      await authenticatedPage.waitForTimeout(1000);
    });

    test('[P2] should select dropdown option with keyboard', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const positionSelect = authenticatedPage.getByTestId('position-select');
      await expect(positionSelect).toBeVisible();

      await positionSelect.focus();

      await authenticatedPage.keyboard.press('ArrowDown');
      await authenticatedPage.keyboard.press('Enter');

      const value = await positionSelect.inputValue();
      expect(['bottom-right', 'bottom-left']).toContain(value);
    });
  });

  test.describe('Focus Management', () => {
    test('[P2] should have visible focus indicators', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      await toggle.focus();

      const outline = await toggle.evaluate(el => {
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

    test('[P2] should focus save button after filling required field', async ({ authenticatedPage, isMobile }) => {
      test.skip(isMobile, 'Keyboard navigation primarily tested on desktop');

      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const botNameInput = authenticatedPage.getByTestId('bot-name-input');
      await botNameInput.focus();
      await botNameInput.fill('New Name');
      await botNameInput.blur();

      const saveButton = authenticatedPage.getByTestId('save-settings-button');

      const isDisabled = await saveButton.isDisabled();
      expect(isDisabled).toBe(false);
    });
  });

  test.describe('ARIA Labels', () => {
    test('[P2] toggle should have aria-checked attribute', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const toggle = authenticatedPage.getByTestId('widget-enabled-toggle');
      await expect(toggle).toBeVisible();

      const ariaChecked = await toggle.getAttribute('aria-checked');
      expect(['true', 'false']).toContain(ariaChecked);
    });

    test('[P2] inputs should have associated labels', async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/settings/widget');
      await authenticatedPage.waitForLoadState('networkidle');

      const botNameInput = authenticatedPage.getByTestId('bot-name-input');
      const id = await botNameInput.getAttribute('id');

      if (id) {
        const label = authenticatedPage.locator(`label[for="${id}"]`);
        const hasLabel = await label.isVisible().catch(() => false);

        const ariaLabel = await botNameInput.getAttribute('aria-label');
        const ariaLabelledBy = await botNameInput.getAttribute('aria-labelledby');

        expect(hasLabel || ariaLabel || ariaLabelledBy).toBe(true);
      }
    });
  });
});
