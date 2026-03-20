/**
 * E2E Tests for Story 10-7: Knowledge Effectiveness Widget (Critical Path - P0)
 *
 * Tests the KnowledgeEffectivenessWidget component's critical user paths.
 * Uses network-first patterns and resilient selectors.
 *
 * Test ID Format: 10.7-E2E-XXX
 */

import {
  test,
  expect,
  mockKnowledgeEffectivenessApi,
  WIDGET_TEST_ID,
} from '../helpers/knowledge-effectiveness-fixture';

test.describe('[P0] Story 10-7: Knowledge Effectiveness Widget - Critical Path', () => {
  test('[10.7-E2E-001] @p0 @smoke should display widget in General mode dashboard', async ({
    page,
    setupDashboardMode,
          }) => {
    await setupDashboardMode('general');
    await mockKnowledgeEffectivenessApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });
          });

          test('[10.7-E2E-002] @p0 should display view details button', async ({
            page,
            setupDashboardMode,
          }) => {
    await setupDashboardMode('general');
    await mockKnowledgeEffectivenessApi(page);

    await page.goto('/dashboard');

    const widget = page.getByTestId(WIDGET_TEST_ID);
    await expect(widget).toBeVisible({ timeout: 15000 });

    const viewDetailsButton = page.getByTestId('view-details-button');
    await expect(viewDetailsButton).toBeVisible();
          });
        });
