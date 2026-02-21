/**
 * Widget Intent Classification E2E Tests
 *
 * Story 5-10: Widget Full App Integration - AC4
 * Tests intent classification routing and fallback behavior.
 *
 * Test IDs: 5.10-E2E-016 to 5.10-E2E-022
 * @tags e2e widget story-5-10 intent ac4
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../helpers/widget-test-fixture';

test.describe('Widget Intent Classification (AC4) [5.10-E2E-005]', () => {
  test.slow();

  test('[P2][5.10-E2E-005-01] should classify product search intent', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'I found some products for you!',
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'product_search',
            confidence: 0.92,
            products: [
              {
                id: 'prod-1',
                variant_id: 'var-1',
                title: 'Searched Product',
                price: 49.99,
                available: true,
              },
            ],
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('find me blue shoes');
    await input.press('Enter');

    await expect(page.getByText('Searched Product')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-005-06] should classify greeting intent', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Hello! Welcome to our store. How can I help you today?',
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'greeting',
            confidence: 0.98,
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('Hello there!');
    await input.press('Enter');

    await expect(page.getByText('Hello! Welcome to our store.')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Cart View Intent [5.10-E2E-005-02]', () => {
  test('[P1] should display cart when viewing', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Here's what's in your cart:",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'cart_view',
            confidence: 0.95,
            cart: {
              items: [
                { variant_id: 'var-1', title: 'Wireless Earbuds', price: 79.99, quantity: 1 },
                { variant_id: 'var-2', title: 'Phone Case', price: 24.99, quantity: 2 },
              ],
              item_count: 3,
              total: 129.97,
            },
          },
        }),
      });
    });

    await page.goto('/widget-test');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page.getByPlaceholder('Type a message...').fill('show cart');
    await page.getByPlaceholder('Type a message...').press('Enter');

    await expect(page.getByText('Wireless Earbuds')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Cart Add Intent [5.10-E2E-005-03]', () => {
  test('[P1] should confirm item added', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "Great choice! I've added the Running Shoes to your cart.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'cart_add',
            confidence: 0.92,
          },
        }),
      });
    });

    await page.goto('/widget-test');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page.getByPlaceholder('Type a message...').fill('add to cart');
    await page.getByPlaceholder('Type a message...').press('Enter');

    await expect(page.getByText(/Running Shoes|added/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Checkout Intent [5.10-E2E-005-04]', () => {
  test('[P1] should show checkout link', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Perfect! Your checkout is ready.',
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'checkout',
            confidence: 0.98,
            checkout_url: 'https://test-store.myshopify.com/checkout/abc123',
          },
        }),
      });
    });

    await page.goto('/widget-test');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page.getByPlaceholder('Type a message...').fill('checkout');
    await page.getByPlaceholder('Type a message...').press('Enter');

    await expect(page.getByText('Perfect! Your checkout is ready.')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Fallback Intent [5.10-E2E-005-05]', () => {
  test('[P2] should show fallback message', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I'm here to help you shop! I can help you find products, check your cart, or assist with checkout.",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'fallback',
            confidence: 0.45,
          },
        }),
      });
    });

    await page.goto('/widget-test');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page.getByPlaceholder('Type a message...').fill('hello');
    await page.getByPlaceholder('Type a message...').press('Enter');

    await expect(page.getByText(/help you shop|find products/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Order Tracking Intent [5.10-E2E-005-07]', () => {
  test('[P1] should prompt for order number', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I'd be happy to help you track your order. Could you provide your order number?",
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'order_tracking',
            confidence: 0.91,
          },
        }),
      });
    });

    await page.goto('/widget-test');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await page.getByPlaceholder('Type a message...').fill('where is my order');
    await page.getByPlaceholder('Type a message...').press('Enter');

    await expect(page.getByText(/order number|track/i)).toBeVisible({ timeout: 10000 });
  });
});
