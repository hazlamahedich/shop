/**
 * @fileoverview Story 6-5: Retention Job Status Tests
 * @description E2E tests for retention job status widget in dashboard
 * @tags e2e story-6-5 retention scheduler dashboard
 */

import { test, expect } from './fixtures';

test.describe.configure({ mode: 'parallel' });

test.describe('Story 6-5: Retention Job Status', () => {
  test('[P0][smoke] should display retention job status in dashboard', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');

    const retentionStatusWidget = authenticatedPage.locator('[data-testid="retention-job-status"]');

    await expect(retentionStatusWidget).toBeVisible();

    const statusText = await retentionStatusWidget.locator('[data-testid="status-text"]').textContent();

    expect(['healthy', 'running', 'idle', 'scheduled']).toContain(statusText?.toLowerCase());

    const lastRunText = await retentionStatusWidget.locator('[data-testid="last-run-time"]').textContent();

    expect(lastRunText).toBeTruthy();
    expect(lastRunText).toContain('Last run:');
  });

  test('[P0][regression] should show last successful run timestamp', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard');

    const lastRunElement = authenticatedPage.locator('[data-testid="last-run-time"]');

    await expect(lastRunElement).toBeVisible();

    const timestampText = await lastRunElement.textContent();

    expect(timestampText).toBeTruthy();
    expect(timestampText).toMatch(/Last run:|ago|\d{4}-\d{2}-\d{2}/);
  });
});
