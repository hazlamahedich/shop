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
} from '../helpers/top-topics-fixture';

async function navigateToRagTab(page: import('@playwright/test').Page) {
  const ragTab = page.getByRole('button', { name: /rag intel/i });
  await ragTab.click();
  await page.waitForTimeout(500);
}

test.describe('[P1] Story 10-8: Top Topics Widget - Features', () => {
  test('[10.8-E2E-010] @p1 should display topic items', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await widget.scrollIntoViewIfNeeded();
    await expect(widget).toBeVisible({ timeout: 15000 });

    const topicItems = widget.locator('[class*="cursor-pointer"]');
    await expect(topicItems.first()).toBeVisible();
  });
});

test.describe('[P1] Story 10-8: Top Topics Widget - Empty State', () => {
  test('[10.8-E2E-019] @p1 should display empty state when no topics', async ({
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
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await widget.scrollIntoViewIfNeeded();
    await expect(widget).toBeVisible({ timeout: 15000 });

    const emptyMessage = widget.getByText(/no patterns detected/i);
    await expect(emptyMessage).toBeVisible();
  });
});

test.describe('[P2] Story 10-8: Top Topics Widget - Loading State', () => {
  test('[10.8-E2E-013] @p2 should show loading skeleton initially', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await widget.scrollIntoViewIfNeeded();
    await expect(widget).toBeVisible({ timeout: 15000 });

    const skeleton = widget.locator('.animate-pulse');
    await expect(skeleton.first()).toBeVisible();
  });
});

test.describe('[P2] Story 10-8: Top Topics Widget - Accessibility', () => {
  test('[10.8-E2E-015] @p2 should be accessible', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await widget.scrollIntoViewIfNeeded();
    await expect(widget).toBeVisible({ timeout: 15000 });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include(`[data-testid="${WIDGET_TEST_ID}"]`)
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});