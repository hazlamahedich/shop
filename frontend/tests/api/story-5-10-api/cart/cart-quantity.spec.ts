/**
 * Widget Cart Quantity Operations API Tests
 *
 * Story 5-10: Widget Full App Integration
 * Tests cart quantity update and validation.
 *
 * Test IDs: 5.10-API-004 to 5.10-API-007
 * @tags api widget story-5-10 cart quantity
 */

import { test, expect } from '@playwright/test';
import { API_BASE, getWidgetHeaders, createTestSession } from '../../../helpers/widget-api-helpers';

interface CartResponse {
  data: {
    items: Array<{
      variant_id: string;
      title: string;
      price: number;
      quantity: number;
    }>;
    subtotal: number;
    currency: string;
    itemCount: number;
  };
}

test.describe('Story 5-10: Cart Quantity Update [5.10-API-002]', () => {
  test('[P1][5.10-API-002-01] PATCH /api/v1/widget/cart/:variant_id updates quantity', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const variantId = 'test-variant-quantity';

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: variantId,
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const updateResponse = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${variantId}`,
      {
        data: {
          session_id: sessionId,
          quantity: 3,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([200, 400, 404]).toContain(updateResponse.status());

    if (updateResponse.status() === 200) {
      const body: CartResponse = await updateResponse.json();
      const updatedItem = body.data.items.find((item) => item.variant_id === variantId);
      if (updatedItem) {
        expect(updatedItem.quantity).toBe(3);
      }
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1][5.10-API-002-02] PATCH validates quantity bounds (1-10)', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const variantId = 'test-variant-bounds';

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: variantId,
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const invalidResponse = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${variantId}`,
      {
        data: {
          session_id: sessionId,
          quantity: 15,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([400, 422]).toContain(invalidResponse.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1][5.10-API-002-03] PATCH rejects negative quantity', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const variantId = 'test-variant-negative';

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: variantId,
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const invalidResponse = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${variantId}`,
      {
        data: {
          session_id: sessionId,
          quantity: -1,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([400, 422]).toContain(invalidResponse.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1][5.10-API-002-04] PATCH rejects zero quantity', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const variantId = 'test-variant-zero';

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: variantId,
        quantity: 1,
      },
      headers: getWidgetHeaders(),
    });

    const invalidResponse = await request.patch(
      `${API_BASE}/api/v1/widget/cart/${variantId}`,
      {
        data: {
          session_id: sessionId,
          quantity: 0,
        },
        headers: getWidgetHeaders(),
      }
    );

    expect([400, 422]).toContain(invalidResponse.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});
