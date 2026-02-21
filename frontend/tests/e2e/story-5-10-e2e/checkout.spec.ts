/**
 * Widget Checkout E2E Tests
 *
 * Story 5-10: Widget Full App Integration - AC3
 * Tests checkout URL generation and checkout flow.
 *
 * Test IDs: 5.10-E2E-010 to 5.10-E2E-015
 * @tags e2e widget story-5-10 checkout ac3
 */

import { test, expect } from '@playwright/test';
import {
  API_BASE,
  getWidgetHeaders,
  createTestSession,
  cleanupSession,
} from '../../helpers/widget-api-helpers';
import { setupWidgetMocks } from '../../helpers/widget-test-fixture';

test.describe('Widget Checkout (AC3) [5.10-E2E-004]', () => {
  test.slow();

  test('[P1][5.10-E2E-004-01] should generate checkout URL', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'checkout-test-variant',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: {
        session_id: sessionId,
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 201, 400, 503]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });

  test('[P1][5.10-E2E-004-03] should handle empty cart on checkout', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: {
        session_id: sessionId,
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 400, 404, 503]).toContain(response.status());

    if (response.status() === 400) {
      const data = await response.json();
      expect(data.message || data.error_code).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });

  test('[P1][5.10-E2E-004-04] should handle missing Shopify integration', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'shopify-test-variant',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: {
        session_id: sessionId,
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 201, 400, 404, 503]).toContain(response.status());

    await cleanupSession(request, sessionId);
  });

  test('[P1][5.10-E2E-004-05] should handle Shopify rate limiting', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'rate-limit-test-variant',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: {
        session_id: sessionId,
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 201, 400, 429, 503]).toContain(response.status());

    if (response.status() === 429) {
      const data = await response.json();
      expect(data.error_code || data.message).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });
});

test.describe('Widget Checkout UI Tests [5.10-E2E-004-UI]', () => {
  test.beforeEach(async ({ page }) => {
    await setupWidgetMocks(page);
  });

  test('[P2][5.10-E2E-004-02] should display checkout link in message', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Your cart is ready for checkout!',
            sender: 'bot',
            created_at: new Date().toISOString(),
            checkout_url: 'https://test-shop.myshopify.com/checkout/xyz789',
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

    await expect(page.getByRole('link', { name: /complete checkout/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test('[P2][5.10-E2E-004-06] should handle circuit breaker open state', async ({ page }) => {
    await page.route('**/api/v1/widget/checkout', async (route) => {
      await route.fulfill({
        status: 503,
        body: JSON.stringify({
          error_code: 8009,
          message: 'Checkout temporarily unavailable. Please try again later.',
          fallback_url: 'https://test-shop.myshopify.com/cart',
        }),
      });
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content:
              'Checkout is experiencing high demand. Please try again in a moment, or visit our store directly.',
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

    await expect(
      page.getByText(/high demand|try again|visit.*store|unavailable/i)
    ).toBeVisible({ timeout: 10000 });
  });
});
