/**
 * Widget Circuit Breaker E2E Tests
 *
 * Story 5-10: Widget Full App Integration - Phase 7 Feature Parity
 * Tests circuit breaker integration for checkout resilience.
 *
 * Test IDs: 5.10-E2E-026 to 5.10-E2E-027
 * @tags e2e widget story-5-10 middleware circuit-breaker
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../../helpers/widget-test-fixture';

test.describe('Widget Circuit Breaker Integration (Task 15) [5.10-E2E-015]', () => {
  test.slow();

  test('[P1][5.10-E2E-015-01] should show graceful message when circuit breaker is open', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Checkout is experiencing high demand. You can try again in 30 seconds, or visit our store directly.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            fallback_url: 'https://test-shop.myshopify.com/cart',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('checkout');
    await input.press('Enter');

    await expect(page.getByText('high demand')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-015-02] should provide fallback URL when Shopify unavailable', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I can't process checkout right now, but you can complete your purchase directly on our store.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            checkout_url: 'https://test-shop.myshopify.com/cart',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('checkout');
    await input.press('Enter');

    await expect(page.getByText('complete your purchase')).toBeVisible({ timeout: 10000 });
  });
});
