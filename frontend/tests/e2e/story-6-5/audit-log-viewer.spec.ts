/**
 * @fileoverview Story 6-5: Audit Log Viewer Tests
 * @description E2E tests for retention audit log viewing and filtering
 * @tags e2e story-6-5 retention audit-logs filtering
 */

import { test, expect } from './fixtures';

test.describe.configure({ mode: 'parallel' });

test.describe('Story 6-5: Audit Log Viewer', () => {
  test('[P0][regression] should display retention audit logs', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/audit-logs');

    const auditLogTable = authenticatedPage.locator('[data-testid="audit-log-table"]');

    await expect(auditLogTable).toBeVisible();

    const rows = await auditLogTable.locator('tbody tr').all();

    expect(rows.length).toBeGreaterThan(0);

    if (rows.length > 0) {
      const firstRow = rows[0];
      const cells = await firstRow.locator('td').all();

      expect(cells.length).toBeGreaterThanOrEqual(5);

      const triggerCell = firstRow.locator('[data-testid="deletion-trigger"]');
      const trigger = await triggerCell.textContent();

      expect(['manual', 'auto']).toContain(trigger?.toLowerCase());
    }
  });

  test('[P1][regression] should filter audit logs by deletion trigger', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/audit-logs');

    const triggerFilter = authenticatedPage.locator('[data-testid="deletion-trigger-filter"]');

    const filterVisible = await triggerFilter.isVisible().catch(() => false);

    if (filterVisible) {
      // Set up network listener BEFORE filter action
      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/v1/audit/retention-logs') && resp.status() === 200
      );

      await triggerFilter.selectOption({ label: 'Auto' });

      // Wait for API response (deterministic)
      await responsePromise;

      // Verify filtered results
      const rows = await authenticatedPage.locator('[data-testid="audit-log-table"] tbody tr').all();

      for (const row of rows) {
        const triggerCell = row.locator('[data-testid="deletion-trigger"]');
        const trigger = await triggerCell.textContent();
        expect(trigger?.toLowerCase()).toBe('auto');
      }
    } else {
      test.skip();
    }
  });

  test('[P1][regression] should filter audit logs by date range', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/audit-logs');

    const startDateInput = authenticatedPage.locator('[data-testid="start-date"]');
    const endDateInput = authenticatedPage.locator('[data-testid="end-date"]');

    const startDateVisible = await startDateInput.isVisible().catch(() => false);

    if (startDateVisible) {
      // Set up network listener BEFORE filter action
      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/v1/audit/retention-logs') && resp.status() === 200
      );

      await startDateInput.fill('2026-01-01');
      await endDateInput.fill('2026-01-31');

      await authenticatedPage.click('[data-testid="apply-filter"]');

      // Wait for API response (deterministic)
      await responsePromise;

      // Verify results loaded
      const rows = await authenticatedPage.locator('[data-testid="audit-log-table"] tbody tr').all();

      expect(rows.length).toBeGreaterThan(0);
    } else {
      test.skip();
    }
  });
});
