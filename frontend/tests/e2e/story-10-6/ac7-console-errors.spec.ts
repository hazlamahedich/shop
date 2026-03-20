/**
 * E2E Tests: Story 10-6 AC7 Console Errors
 *
 * Tests that dashboard has no console errors in General Mode.
 */

import { test, expect } from '../../fixtures/dashboard-mode.fixture';

test.describe('AC7: No Console Errors', () => {
  test('[P2][10.6-E2E-011] should not have console errors in General Mode', async ({ dashboardPage }) => {
    const errors: string[] = [];
    dashboardPage.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await dashboardPage.goto('/dashboard');
    await expect(dashboardPage.getByTestId('conversation-overview-widget-container')).toBeVisible({ timeout: 10000 });

    const filteredErrors = errors.filter(
      (e) => !e.includes('Failed to load resource') && !e.includes('net::ERR_BLOCKED_BY_CLIENT') && !e.includes('favicon')
    );

    expect(filteredErrors).toHaveLength(0);
  });
});
