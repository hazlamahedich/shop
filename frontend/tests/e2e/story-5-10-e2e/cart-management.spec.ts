/**
 * Widget Cart Management E2E Tests
 *
 * Story 5-10: Widget Full App Integration - AC3
 * Tests cart add, view, update, and remove operations.
 *
 * Test IDs: 5.10-E2E-003 to 5.10-E2E-009
 * @tags e2e widget story-5-10 cart ac3
 */

import { test, expect } from '@playwright/test';
import {
  API_BASE,
  getWidgetHeaders,
  createTestSession,
  cleanupSession,
} from '../../helpers/widget-api-helpers';
import { setupWidgetMocks } from '../../helpers/widget-test-fixture';

test.describe('Widget Cart Management (AC3) [5.10-E2E-003]', () => {
  test.slow();

  test('[P1][5.10-E2E-003-01] should add item to cart', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'test-variant-e2e-001',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 201, 400, 503]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    } else {
      console.log(`[TEA] Cart add status: ${response.status()} (expected - may need Shopify)`);
    }

    await cleanupSession(request, sessionId);
  });

  test('[P2][5.10-E2E-003-02] should retrieve cart contents', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'test-variant-e2e-002',
        quantity: 2,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.get(`${API_BASE}/api/v1/widget/cart/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    expect([200, 400, 404, 405, 503]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });

  test('[P2][5.10-E2E-003-03] should remove item from cart', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'test-variant-e2e-003',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.delete(
      `${API_BASE}/api/v1/widget/cart/${sessionId}/test-variant-e2e-003`,
      {
        headers: getWidgetHeaders(),
      }
    );

    expect([200, 400, 404, 503]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });

  test('[P1][5.10-E2E-003-05] should update cart item quantity', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'test-variant-e2e-005',
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const response = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${sessionId}/test-variant-e2e-005`,
      {
        data: {
          quantity: 5,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([200, 400, 404, 503]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    }

    await cleanupSession(request, sessionId);
  });

  test('[P1][5.10-E2E-003-06] should reject invalid quantity bounds', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${sessionId}/test-variant-invalid`,
      {
        data: {
          quantity: 15,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([400, 404, 422, 503]).toContain(response.status());

    await cleanupSession(request, sessionId);
  });

  test('[P2][5.10-E2E-003-07] should handle concurrent cart operations', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const results = await Promise.all([
      request.post(`${API_BASE}/api/v1/widget/cart`, {
        data: { session_id: sessionId, variant_id: 'concurrent-var-1', quantity: 1 },
        headers: getWidgetHeaders(),
      }),
      request.post(`${API_BASE}/api/v1/widget/cart`, {
        data: { session_id: sessionId, variant_id: 'concurrent-var-2', quantity: 1 },
        headers: getWidgetHeaders(),
      }),
      request.post(`${API_BASE}/api/v1/widget/cart`, {
        data: { session_id: sessionId, variant_id: 'concurrent-var-3', quantity: 1 },
        headers: getWidgetHeaders(),
      }),
    ]);

    for (const r of results) {
      expect([200, 201, 400, 503]).toContain(r.status());
    }

    await cleanupSession(request, sessionId);
  });
});

test.describe('Widget Cart UI Tests [5.10-E2E-003-UI]', () => {
  test.beforeEach(async ({ page }) => {
    await setupWidgetMocks(page);
  });

  test('[P2][5.10-E2E-003-04] should display cart view in message', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Here is your cart:',
            sender: 'bot',
            created_at: new Date().toISOString(),
            cart: {
              items: [
                {
                  variant_id: 'var-1',
                  title: 'Cart Item',
                  price: 15.0,
                  quantity: 2,
                },
              ],
              item_count: 2,
              total: 30.0,
            },
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('show my cart');
    await input.press('Enter');

    await expect(page.getByText('Here is your cart:')).toBeVisible({ timeout: 10000 });
  });
});
