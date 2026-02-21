/**
 * Widget Hybrid Mode E2E Tests
 *
 * Story 5-10: Widget Full App Integration - Phase 7 Feature Parity
 * Tests hybrid mode (@bot mentions) behavior.
 *
 * Test IDs: 5.10-E2E-021 to 5.10-E2E-022
 * @tags e2e widget story-5-10 middleware hybrid
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../../helpers/widget-test-fixture';

test.describe('Widget Hybrid Mode (Task 19) [5.10-E2E-019]', () => {
  test.slow();

  test('[P2][5.10-E2E-019-01] should respond to @bot mentions', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Hello! I'm here to help you shop.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'greeting',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('@bot hello');
    await input.press('Enter');

    await expect(page.getByText("I'm here to help you shop")).toBeVisible({ timeout: 10000 });
  });

  test('[P2][5.10-E2E-019-02] should activate hybrid mode for 2 hours', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Hybrid mode activated! I'll respond to all messages for the next 2 hours.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            hybrid_mode: true,
            hybrid_expires_at: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('@bot activate');
    await input.press('Enter');

    await expect(page.getByText('Hybrid mode activated')).toBeVisible({ timeout: 10000 });
  });
});
