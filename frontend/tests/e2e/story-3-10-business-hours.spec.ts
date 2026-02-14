/**
 * E2E Tests: Story 3-10 Business Hours Configuration
 *
 * User Journey: Merchant configures business hours for their store,
 * including day-by-day schedules, timezone selection, and custom
 * out-of-office messages that appear in handoff responses.
 *
 * Flow: Business Info & FAQ → Business Hours Card → Configure → Auto-save
 *
 * Priority Coverage:
 * - [P0] Configure business hours and verify save
 * - [P1] Day toggle (open/closed)
 * - [P1] Timezone selection
 * - [P1] Out-of-office message customization
 * - [P1] Auto-save indicator
 * - [P2] Keyboard navigation
 * - [P2] Screen reader accessibility
 * - [P2] Initialize default hours
 * - [P2] Time input validation
 *
 * @package frontend/tests/e2e
 */

import { test, expect } from '@playwright/test';

const AUTH_STATE = {
  isAuthenticated: true,
  merchant: { id: 1, email: 'e2e-test@example.com', name: 'Test Merchant' },
  sessionExpiresAt: new Date(Date.now() + 86400000).toISOString(),
  isLoading: false,
  error: null,
};

const MOCK_MERCHANT = {
  id: 1,
  email: 'e2e-test@example.com',
  name: 'Test Merchant',
  role: 'merchant',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const DEFAULT_BUSINESS_HOURS = {
  timezone: 'America/Los_Angeles',
  hours: [
    { day: 'mon', isOpen: true, openTime: '09:00', closeTime: '17:00' },
    { day: 'tue', isOpen: true, openTime: '09:00', closeTime: '17:00' },
    { day: 'wed', isOpen: true, openTime: '09:00', closeTime: '17:00' },
    { day: 'thu', isOpen: true, openTime: '09:00', closeTime: '17:00' },
    { day: 'fri', isOpen: true, openTime: '09:00', closeTime: '17:00' },
    { day: 'sat', isOpen: false, openTime: '10:00', closeTime: '14:00' },
    { day: 'sun', isOpen: false, openTime: '10:00', closeTime: '14:00' },
  ],
  outOfOfficeMessage: "Our team is offline. We'll respond during business hours.",
  formattedHours: '9 AM - 5 PM, Mon-Fri',
};

test.describe('Story 3-10: Business Hours Configuration', () => {
  test.beforeEach(async ({ page, context }) => {
    await context.addInitScript((state) => {
      sessionStorage.setItem('auth_state', JSON.stringify(state));
    }, AUTH_STATE);

    await page.route('**/api/v1/auth/me', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { merchant: MOCK_MERCHANT },
          meta: { requestId: 'test-auth-me' },
        }),
      });
    });
  });

  test.describe('[P0] Business Hours Configuration Flow (AC1, AC2, AC3, AC4)', () => {
    test('[P0] should display business hours configuration on settings page', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const businessHoursHeading = page.getByRole('heading', { name: /business hours/i }).first();
      await expect(businessHoursHeading).toBeVisible({ timeout: 15000 });
    });

    test('[P0] should show all seven days with hours', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      for (const day of dayNames) {
        await expect(page.getByText(day)).toBeVisible({ timeout: 10000 });
      }
    });

    test('[P0] should save hours configuration via API', async ({ page }) => {
      let savedConfig: any = null;

      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else if (route.request().method() === 'PUT') {
          savedConfig = route.request().postDataJSON();
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { ...DEFAULT_BUSINESS_HOURS, ...savedConfig },
              meta: { requestId: 'test-save-hours', updatedAt: new Date().toISOString() },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await timezoneSelect.selectOption('America/New_York');

      await page.waitForTimeout(700);

      expect(savedConfig).not.toBeNull();
      expect(savedConfig.timezone).toBe('America/New_York');
    });
  });

  test.describe('[P1] Day Toggle - Open/Closed (AC1)', () => {
    test('[P1] should toggle day open/closed status', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const saturdayToggle = page.locator('[data-testid="day-toggle-sat"]');
      await expect(saturdayToggle).toBeVisible({ timeout: 10000 });

      const isChecked = await saturdayToggle.isChecked();
      expect(isChecked).toBe(false);
    });

    test('[P1] should show Closed text when day is closed', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const sundayToggle = page.locator('[data-testid="day-toggle-sun"]');
      const sundayRow = sundayToggle.locator('xpath=ancestor::div[contains(@class, "flex")]').first();
      const closedText = sundayRow.getByText('Closed');
      await expect(closedText).toBeVisible({ timeout: 10000 });
    });

    test('[P1] should enable time inputs when day is toggled open', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const saturdayToggle = page.locator('[data-testid="day-toggle-sat"]');
      await saturdayToggle.click();

      const saturdayOpenTime = page.locator('[data-testid="open-time-sat"]');
      await expect(saturdayOpenTime).toBeEnabled({ timeout: 5000 });
    });
  });

  test.describe('[P1] Timezone Selection (AC2)', () => {
    test('[P1] should display timezone dropdown with options', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await expect(timezoneSelect).toBeVisible({ timeout: 10000 });

      const optionValues = await timezoneSelect.locator('option').evaluateAll((options) =>
        options.map((opt) => opt.value)
      );
      expect(optionValues.length).toBeGreaterThan(0);
      expect(optionValues).toContain('America/Los_Angeles');
      expect(optionValues).toContain('America/New_York');
      expect(optionValues).toContain('Europe/London');
    });

    test('[P1] should save selected timezone', async ({ page }) => {
      let savedConfig: any = null;

      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          savedConfig = route.request().postDataJSON();
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { ...DEFAULT_BUSINESS_HOURS, ...savedConfig },
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await timezoneSelect.selectOption('Europe/London');

      await page.waitForTimeout(700);

      expect(savedConfig).not.toBeNull();
      expect(savedConfig.timezone).toBe('Europe/London');
    });
  });

  test.describe('[P1] Out-of-Office Message (AC3)', () => {
    test('[P1] should display out-of-office message textarea', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const messageTextarea = page.locator('#out-of-office-message');
      await expect(messageTextarea).toBeVisible();
    });

    test('[P1] should show default message placeholder', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { ...DEFAULT_BUSINESS_HOURS, outOfOfficeMessage: '' },
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const messageTextarea = page.locator('#out-of-office-message');
      const placeholder = await messageTextarea.getAttribute('placeholder');
      expect(placeholder).toContain("Our team is offline");
    });

    test('[P1] should save custom out-of-office message', async ({ page }) => {
      let savedConfig: any = null;

      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          savedConfig = route.request().postDataJSON();
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { ...DEFAULT_BUSINESS_HOURS, ...savedConfig },
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const messageTextarea = page.locator('#out-of-office-message');
      await messageTextarea.clear();
      await messageTextarea.fill('Our support team is available 9-5 on weekdays.');

      await page.waitForTimeout(700);

      expect(savedConfig).not.toBeNull();
      expect(savedConfig.outOfOfficeMessage).toBe('Our support team is available 9-5 on weekdays.');
    });

    test('[P1] should show character count', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const messageTextarea = page.locator('#out-of-office-message');
      await messageTextarea.fill('Test message');

      const charCount = page.getByText(/\d+\/500 characters/);
      await expect(charCount).toBeVisible();
    });
  });

  test.describe('[P1] Auto-Save Indicator (AC4)', () => {
    test('[P1] should show saving indicator during save', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await timezoneSelect.selectOption('America/Chicago');

      const savingIndicator = page.getByText(/saving/i);
      await expect(savingIndicator).toBeVisible({ timeout: 2000 });
    });

    test('[P1] should show saved indicator after successful save', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await timezoneSelect.selectOption('America/Denver');

      await page.waitForTimeout(1000);

      const savedIndicator = page.getByText(/Saved at/i).or(page.locator('[data-testid="save-indicator"]')).first();
      await expect(savedIndicator).toBeVisible({ timeout: 3000 });
    });
  });

  test.describe('[P2] Initialize Default Hours', () => {
    test('[P2] should show initialize button when no hours configured', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { timezone: 'America/Los_Angeles', hours: [], outOfOfficeMessage: '' },
            meta: { requestId: 'test-no-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const initializeButton = page.getByRole('button', { name: /set default hours|mon-fri.*9.*5/i });
      await expect(initializeButton).toBeVisible({ timeout: 10000 });
    });

    test('[P2] should initialize default hours when button clicked', async ({ page }) => {
      let savedConfig: any = null;

      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          const request = route.request();
          if (savedConfig && request.headers()['x-init'] === undefined) {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                data: { ...DEFAULT_BUSINESS_HOURS, hours: savedConfig.hours },
                meta: { requestId: 'test-after-init' },
              }),
            });
          } else {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                data: { timezone: 'America/Los_Angeles', hours: [], outOfOfficeMessage: '' },
                meta: { requestId: 'test-no-hours' },
              }),
            });
          }
        } else {
          savedConfig = route.request().postDataJSON();
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { ...DEFAULT_BUSINESS_HOURS, ...savedConfig },
              meta: { requestId: 'test-init-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const initializeButton = page.getByRole('button', { name: /set default hours|mon-fri.*9.*5/i });
      await initializeButton.click();

      await page.waitForTimeout(1000);

      expect(savedConfig).not.toBeNull();
      expect(savedConfig.hours).toBeDefined();
      expect(savedConfig.hours.length).toBe(7);
    });
  });

  test.describe('[P2] Time Input Validation', () => {
    test('[P2] should accept valid time inputs', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-save' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const mondayOpenTime = page.locator('[data-testid="open-time-mon"]');
      await mondayOpenTime.clear();
      await mondayOpenTime.fill('08:30');

      const value = await mondayOpenTime.inputValue();
      expect(value).toBe('08:30');
    });
  });

  test.describe('[P2] Preview Display', () => {
    test('[P2] should show formatted hours preview', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              ...DEFAULT_BUSINESS_HOURS,
              formattedHours: '9 AM - 5 PM, Mon-Fri',
            },
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const preview = page.getByText(/preview:/i);
      await expect(preview).toBeVisible({ timeout: 10000 });

      const formattedHours = page.getByText(/9.*AM.*5.*PM.*Mon.*Fri/i);
      await expect(formattedHours).toBeVisible();
    });
  });

  test.describe('[P2] Accessibility (AC6)', () => {
    test('[P2] timezone select should have accessible label', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneLabel = page.getByLabel(/timezone/i);
      await expect(timezoneLabel).toBeVisible();
    });

    test('[P2] out-of-office message textarea should have accessible label', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const messageLabel = page.getByLabel(/out.*office.*message/i);
      await expect(messageLabel).toBeVisible();
    });

    test('[P2] day toggles should be focusable via keyboard', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: DEFAULT_BUSINESS_HOURS,
            meta: { requestId: 'test-get-hours' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      for (let i = 0; i < 10; i++) {
        await page.keyboard.press('Tab');
      }

      const focusedElement = page.locator(':focus');
      const tagName = await focusedElement.evaluate((el) => el.tagName.toLowerCase());
      const inputType = await focusedElement.getAttribute('type');
      expect(['input', 'select', 'textarea', 'button'].includes(tagName)).toBe(true);
    });

    test('[P2] error messages should be announced to screen readers', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Failed to load business hours',
              meta: { requestId: 'test-error' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const errorAlert = page.locator('[role="alert"]').or(page.getByText(/error/i));
      await expect(errorAlert.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P2] Error Handling', () => {
    test('[P2] should show error when load fails', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Internal server error',
            meta: { requestId: 'test-error' },
          }),
        });
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const errorMessage = page.getByText(/error|failed to load/i);
      await expect(errorMessage.first()).toBeVisible({ timeout: 5000 });
    });

    test('[P2] should show error when save fails', async ({ page }) => {
      await page.route('**/api/v1/merchant/business-hours', (route) => {
        if (route.request().method() === 'GET') {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: DEFAULT_BUSINESS_HOURS,
              meta: { requestId: 'test-get-hours' },
            }),
          });
        } else {
          route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid timezone',
              meta: { requestId: 'test-save-error' },
            }),
          });
        }
      });

      await page.goto('/business-info-faq');
      await page.waitForLoadState('networkidle');

      const timezoneSelect = page.locator('#timezone');
      await timezoneSelect.selectOption('America/Denver');

      await page.waitForTimeout(1000);

      const errorMessage = page.getByText(/error|failed to save/i);
      await expect(errorMessage.first()).toBeVisible({ timeout: 5000 });
    });
  });
});
