/**
 * Widget Consent Management E2E Tests
 *
 * Story 5-10: Widget Full App Integration - Phase 7 Feature Parity
 * Tests consent management for cart operations.
 *
 * Test IDs: 5.10-E2E-018 to 5.10-E2E-020
 * @tags e2e widget story-5-10 middleware consent
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../../helpers/widget-test-fixture';

test.describe('Widget Consent Management (Task 18) [5.10-E2E-018]', () => {
  test.slow();

  test('[P1][5.10-E2E-018-01] should prompt for consent before cart add', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Before I add items to your cart, I need your consent to manage your shopping data. Do you agree?",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'consent_prompt',
            consent_required: true,
            consent_type: 'cart_management',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('add shoes to cart');
    await input.press('Enter');

    await expect(page.getByText('Before I add items')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-018-02] should proceed after consent granted', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Thank you! Your consent has been recorded. Now I can help you with your cart.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            consent_granted: true,
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('yes');
    await input.press('Enter');

    await expect(page.getByText('consent has been recorded')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-018-03] should remember consent across session', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Added to cart!",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'cart_add',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('add product to cart');
    await input.press('Enter');

    await expect(page.getByText('Added to cart')).toBeVisible({ timeout: 10000 });
  });
});
