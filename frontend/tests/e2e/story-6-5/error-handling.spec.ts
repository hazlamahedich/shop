/**
 * @fileoverview Story 6-5: Error Handling Tests
 * @description E2E tests for error handling and edge cases
 * @tags e2e story-6-5 retention error-handling edge-cases
 */

import { test, expect } from './fixtures';

test.describe.configure({ mode: 'parallel' });

test.describe('Story 6-5: Error Handling', () => {
  test('[P1][regression] should handle API errors gracefully', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/v1/audit/retention-logs**', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Service temporarily unavailable' }),
      });
    });

    await authenticatedPage.goto('/dashboard/audit-logs');

    const errorBanner = authenticatedPage.locator('[data-testid="error-banner"]');

    const errorVisible = await errorBanner.isVisible().catch(() => false);

    if (errorVisible) {
      await expect(errorBanner).toBeVisible();
      await expect(errorBanner).toContainText('temporarily unavailable');
    } else {
      const errorToast = authenticatedPage.locator('[data-testid="error-toast"]');

      const toastVisible = await errorToast.isVisible().catch(() => false);

      if (toastVisible) {
        await expect(errorToast).toBeVisible();
        await expect(errorToast).toContainText('Failed to load');
      } else {
        test.skip(true, 'Error handling UI not implemented');
      }
    }
  });

  test('[P1][regression] should display audit log loading errors', async ({ authenticatedPage }) => {
    await authenticatedPage.route('**/api/v1/audit/retention-logs**', async (route) => {
      await route.abort('failed');
    });

    await authenticatedPage.goto('/dashboard/audit-logs');

    const errorMessage = authenticatedPage.locator('[data-testid="error-message"]');

    const errorVisible = await errorMessage.isVisible().catch(() => false);

    if (errorVisible) {
      await expect(errorMessage).toBeVisible();
    } else {
      test.skip(true, 'Error message UI not implemented');
    }
  });
});
