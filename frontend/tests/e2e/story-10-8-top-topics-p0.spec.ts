/**
 * E2E Tests for Story 10-8: Top Topics Widget (Critical Path - P0)
 *
 * Tests the TopTopicsWidget component's critical user paths.
 * Uses network-first patterns and resilient selectors.
 *
 * Test ID Format: 10.8-E2E-XXX
 */

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

test.describe('[P0] Story 10-8: Top Topics Widget - Critical Path', () => {
  test('[10.8-E2E-001] @p0 @smoke should display widget in General mode dashboard', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });
  });

  test('[10.8-E2E-002] @p0 should display topics list', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const topics = widget.locator('[class*="group/item"]');
    await expect(topics.first()).toBeVisible();
  });

  test('[10.8-E2E-003] @p0 should navigate to conversations on topic click', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const firstTopic = widget.locator('[class*="group/item"]').first();
    await firstTopic.click();

    await expect(page).toHaveURL(/conversations\?search=/);
  });

  test('[10.8-E2E-004] @p0 should display semantic clusters title', async ({
    page,
    setupDashboardMode,
  }) => {
    await setupDashboardMode('general');
    await mockTopTopicsApi(page);

    await page.goto('/dashboard');
    await navigateToRagTab(page);

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const title = widget.getByText('Semantic Clusters');
    await expect(title).toBeVisible();
  });
});