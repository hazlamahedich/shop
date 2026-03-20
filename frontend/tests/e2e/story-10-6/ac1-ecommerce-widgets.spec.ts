/**
 * E2E Tests: Story 10-6 AC1 E-commerce Widgets Hidden in General Mode
 *
 * Tests that dashboard widgets are correctly hidden/shown based on merchant onboarding mode.
 */

import { test, expect } from '../../fixtures/dashboard-mode.fixture';

const ECOMMERCE_ONLY_WIDGETS = ['top-products', 'geographic', 'conversion-funnel'];

const WIDGET_TEST_IDS: Record<string, string> = {
  'top-products': 'top-products-widget-container',
  geographic: 'geographic-widget-container',
  'conversion-funnel': 'conversion-funnel-widget-container',
};

test.describe('AC1: E-commerce Widgets Hidden in General Mode', () => {
  test('[P0][10.6-E2E-001] should hide e-commerce widgets in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');

    for (const widget of ECOMMERCE_ONLY_WIDGETS) {
      const testId = WIDGET_TEST_IDS[widget];
      await expect(dashboardPage.getByTestId(testId)).not.toBeVisible();
    }
  });
});
