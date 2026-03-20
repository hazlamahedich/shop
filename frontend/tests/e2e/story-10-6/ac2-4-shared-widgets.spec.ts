/**
 * E2E Tests: Story 10-6 AC2-4 Shared Widgets
 *
 * Tests that dashboard widgets are correctly shown in both modes.
 */

import { test, expect } from '../../fixtures/dashboard-mode.fixture';

const SHARED_WIDGETS = [
  'conversation-overview',
  'handoff-queue',
  'ai-cost',
  'bot-quality',
  'alerts',
  'peak-hours',
  'knowledge-gap',
];

const WIDGET_TEST_IDS: Record<string, string> = {
  'conversation-overview': 'conversation-overview-widget-container',
  'handoff-queue': 'handoff-queue-widget-container',
  'ai-cost': 'financial-overview-widget-container',
  'bot-quality': 'bot-quality-widget-container',
  alerts: 'alerts-widget-container',
  'peak-hours': 'peak-hours-heatmap-widget-container',
  'knowledge-gap': 'knowledge-gap-widget-container',
};

test.describe('AC2: Conversation Widgets', () => {
  test('[P0][10.6-E2E-004] should show conversation-overview widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['conversation-overview'])).toBeVisible();
  });

  test('[P0][10.6-E2E-005] should show handoff-queue widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['handoff-queue'])).toBeVisible();
  });
});

test.describe('AC3: Cost Tracking Widget', () => {
  test('[P0][10.6-E2E-006] should show ai-cost widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['ai-cost'])).toBeVisible();
  });

  test('[P0][10.6-E2E-007] should show bot-quality widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['bot-quality'])).toBeVisible();
  });
});

test.describe('AC4: Quality/Analytics widgets', () => {
  test('[P1][10.6-E2E-008] should show alerts widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['alerts'])).toBeVisible();
  });

  test('[P1][10.6-E2E-009] should show peak-hours widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['peak-hours'])).toBeVisible();
  });

  test('[P1][10.6-E2E-010] should show knowledge-gap widget in General Mode', async ({ dashboardPage }) => {
    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId(WIDGET_TEST_IDS['knowledge-gap'])).toBeVisible();
  });
});
