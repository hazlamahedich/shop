/**
 * Widget Budget Alerts E2E Tests
 *
 * Story 5-10: Widget Full App Integration - Phase 7 Feature Parity
 * Tests budget alerts and warnings.
 *
 * Test IDs: 5.10-E2E-023 to 5.10-E2E-025
 * @tags e2e widget story-5-10 middleware budget
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../../helpers/widget-test-fixture';

test.beforeEach(async ({ page }) => {
  await setupWidgetMocks(page);
});

test.describe('Widget Budget Alerts (Task 20) [5.10-E2E-020]', () => {
  test.slow();

  test('[P2][5.10-E2E-020-01] should show budget exceeded message', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I'm taking a short break while we review our chat budget. A team member will be with you shortly!",
            sender: 'bot',
            created_at: new Date().toISOString(),
            budget_exceeded: true,
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/short break|budget|team member/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P2][5.10-E2E-020-02] should show budget warning at threshold', async ({ page }) => {
    let messageCount = 0;

    await page.route('**/api/v1/widget/message', async (route) => {
      messageCount++;

      if (messageCount >= 3) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            message: {
              message_id: crypto.randomUUID(),
              content: "We're approaching our chat budget limit. Is there anything specific I can help you with quickly?",
              sender: 'bot',
              created_at: new Date().toISOString(),
              budget_warning: true,
              budget_remaining_percent: 20,
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            message: {
              message_id: crypto.randomUUID(),
              content: `Response ${messageCount}`,
              sender: 'bot',
              created_at: new Date().toISOString(),
            },
          }),
        });
      }
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');

    await input.fill('message 1');
    await input.press('Enter');
    await expect(page.getByText('Response 1')).toBeVisible({ timeout: 10000 });

    await input.fill('message 2');
    await input.press('Enter');
    await expect(page.getByText('Response 2')).toBeVisible({ timeout: 10000 });

    await input.fill('message 3');
    await input.press('Enter');

    await expect(page.getByText(/budget limit|approaching/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P2][5.10-E2E-020-03] should handle zero budget gracefully', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Our chat budget has been reached. Please contact support for immediate assistance.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            budget_zero: true,
            support_contact: 'support@example.com',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/budget.*reached|contact support/i)).toBeVisible({ timeout: 10000 });
  });
});
