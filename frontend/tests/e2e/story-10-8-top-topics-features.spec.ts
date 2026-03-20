/**
 * E2E Tests for Story 10-8: Top Topics Widget (Features & Edge Cases - P1/P2)
 *
 * Tests the TopTopicsWidget component's features and edge cases.
 * Uses network-first patterns and resilient selectors.
 *
 * Test ID Format: 10.8-E2E-XXX
 */

import AxeBuilder from '@axe-core/playwright';
import {
  test,
  expect,
  mockTopTopicsApi,
  WIDGET_TEST_ID,
  API_ENDPOINT
} from '../helpers/top-topics-fixture';

test.describe('[P1] Story 10-8: Top Topics Widget - Features', () => {
  test('[10.8-E2E-010] @p1 should display trend indicators', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const upTrend = widget.locator('.text-green-400').first();
    await expect(upTrend).toBeVisible();
  });

  test('[10.8-E2E-011] @p1 should export CSV', async ({
    page,
    setupDashboardMode
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const exportButton = page.getByTestId('export-csv-button');
    await expect(exportButton).toBeVisible();
  });

  test('[10.8-E2E-016] @p1 should change API params when time range changes', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const apiCallPromise = page.waitForRequest(
      (req) =>
        req.url().includes('/api/v1/analytics/top-topics') && req.url().includes('days=30')
    );

    const timeRangeSelector = page.getByTestId('time-range-selector');
    await timeRangeSelector.selectOption('30');

    const request = await apiCallPromise;
    expect(request.url()).toContain('days=30');
  });

  test('[10.8-E2E-017] @p1 should download CSV file when export button clicked', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const downloadPromise = page.waitForEvent('download');

    const exportButton = page.getByTestId('export-csv-button').first();
    await exportButton.click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('.csv');

    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream) {
      chunks.push(chunk);
    }
    const csvContent = Buffer.concat(chunks).toString();

    expect(csvContent).toContain('Topic Name');
    expect(csvContent).toContain('Query Count');
    expect(csvContent).toContain('Trend');
  });

  test('[10.8-E2E-018] @p1 should display trend indicators with correct colors', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page, {
      topics: [
        { name: 'shipping cost', queryCount: 45, trend: 'up' },
        { name: 'return policy', queryCount: 32, trend: 'down' },
        { name: 'track order', queryCount: 28, trend: 'stable' },
        { name: 'new product', queryCount: 15, trend: 'new' },
      ],
      lastUpdated: new Date().toISOString(),
      period: { days: 7 },
    });

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const upTrend = widget.locator('.text-green-400').filter({ hasText: 'up' });
    await expect(upTrend).toBeVisible();

    const downTrend = widget.locator('.text-red-400').filter({ hasText: 'down' });
    await expect(downTrend).toBeVisible();

    const newTrend = widget.locator('.text-blue-400').filter({ hasText: 'new' });
    await expect(newTrend).toBeVisible();
  });

  test('[10.8-E2E-019] @p1 should display last updated timestamp', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    const lastUpdated = new Date().toISOString();
    await mockTopTopicsApi(page, {
      topics: [{ name: 'test topic', queryCount: 10, trend: 'stable' }],
      lastUpdated,
      period: { days: 7 },
    });

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const lastUpdatedText = widget.getByText(/Last updated/i);
    await expect(lastUpdatedText).toBeVisible();
  });
});

test.describe('[P2] Story 10-8: Top Topics Widget - Loading & States', () => {
  test('[10.8-E2E-012] @p2 should handle empty state', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page, {
      topics: [],
      lastUpdated: new Date().toISOString(),
      period: { days: 7 },
    });

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const emptyState = page.getByTestId('top-topics-empty');
    await expect(emptyState).toBeVisible();
  });

  test('[10.8-E2E-013] @p2 should handle loading state', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');

    await page.goto('/dashboard');

    const skeleton = page.getByTestId('top-topics-skeleton');
    await expect(skeleton).toBeVisible();
  });

  test('[10.8-E2E-014] @p2 should handle error state', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');

    await page.route(API_ENDPOINT, async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    await page.goto('/dashboard');

    const errorMessage = page.getByTestId('top-topics-error');
    await expect(errorMessage).toBeVisible({ timeout: 15000 });
  });

  test('[10.8-E2E-015] @p2 should be accessible', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(`[data-testid="${WIDGET_TEST_ID}"]`)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('[10.8-E2E-020] @p2 should maintain selected time range after page refresh', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const timeRangeSelector = page.getByTestId('time-range-selector');
    await timeRangeSelector.selectOption('30');

    await expect(timeRangeSelector).toHaveValue('30');

    await page.reload();

    await expect(widget).toBeVisible({ timeout: 15000 });

    await expect(timeRangeSelector).toHaveValue('30');
  });
});
