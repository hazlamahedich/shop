/**
 * E2E Tests: Story 10-6 AC5 General Mode Specific Widgets
 *
 * Tests that knowledge-base and feedback-analytics widgets are visible in General Mode.
 */

import { test, expect } from '../../fixtures/dashboard-mode.fixture';

const GENERAL_ONLY_WIDGETS = ['knowledge-base', 'feedback-analytics'];

const WIDGET_TEST_IDS: Record<string, string> = {
  'knowledge-base': 'knowledge-base-widget-container',
  'feedback-analytics': 'feedback-analytics-widget-container',
};

test.describe('AC5: General Mode Specific Widgets', () => {
  test('[P1][10.6-E2E-012] should show knowledge-base widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['knowledge-base'])).toBeVisible();
  });

  test('[P1][10.6-E2E-013] should show feedback-analytics widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['feedback-analytics'])).toBeVisible();
  });
});
