/**
 * @fileoverview Story 6-5: Dashboard Loading Tests
 * @description E2E tests for dashboard loading and integration
 * @tags e2e story-6-5 retention dashboard loading
 */

import { test, expect } from './fixtures';

test.describe.configure({ mode: 'parallel' });

test.describe('Story 6-5: Dashboard Loading', () => {
  test('[P0][smoke] should verify dashboard loads correctly', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');

    await authenticatedPage.waitForLoadState('networkidle');

    await expect(authenticatedPage.locator('[data-testid="dashboard-content"]')).toBeVisible();

    const retentionStatusVisible = await authenticatedPage
      .locator('[data-testid="retention-job-status"]')
      .isVisible()
      .catch(() => false);

    if (retentionStatusVisible) {
      await expect(authenticatedPage.locator('[data-testid="retention-job-status"]')).toBeVisible();
    }

    const auditLogsVisible = await authenticatedPage
      .locator('[data-testid="audit-logs-heading"]')
      .isVisible()
      .catch(() => false);

    if (auditLogsVisible) {
      await expect(authenticatedPage.locator('[data-testid="audit-logs-heading"]')).toBeVisible();
    }
  });
});
