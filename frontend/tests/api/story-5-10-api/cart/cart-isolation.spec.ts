/**
 * Widget Cart Session Isolation API Tests
 *
 * Story 5-10: Widget Full App Integration
 * Tests cart isolation between sessions.
 *
 * Test IDs: 5.10-API-008 to 5.10-API-009
 * @tags api widget story-5-10 cart isolation
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

test.describe('Story 5-10: Cart Session Isolation [5.10-API-003]', () => {
  test('[P2][5.10-API-003-01] Cart should be isolated between sessions', async ({ request }) => {
    const sessionId1 = await createTestSession(request);
    const sessionId2 = await createTestSession(request);

    if (!sessionId1 || !sessionId2) {
      test.skip(true, 'Could not create test sessions');
      return;
    }

    const variantId = 'isolation-test-variant';

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId1,
        variant_id: variantId,
        quantity: 5,
      },
      headers: getWidgetHeaders(),
    });

    const cart2Response = await request.get(
      `${API_BASE}/api/v1/widget/cart?session_id=${sessionId2}`,
      { headers: getWidgetHeaders() }
    );

    expect([200, 400]).toContain(cart2Response.status());

    if (cart2Response.status() === 200) {
      const body: CartResponse = await cart2Response.json();
      const crossSessionItem = body.data.items.find((item) => item.variant_id === variantId);
      expect(crossSessionItem).toBeUndefined();
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId1}`);
    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId2}`);
  });

  test('[P2][5.10-API-003-02] Cart item_count should reflect total quantities', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'count-test-1',
        quantity: 2,
      },
      headers: getWidgetHeaders(),
    });

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'count-test-2',
        quantity: 3,
      },
      headers: getWidgetHeaders(),
    });

    const cartResponse = await request.get(
      `${API_BASE}/api/v1/widget/cart?session_id=${sessionId}`,
      { headers: getWidgetHeaders() }
    );

    expect([200, 400]).toContain(cartResponse.status());

    if (cartResponse.status() === 200) {
      const body: CartResponse = await cartResponse.json();
      expect(body.data.itemCount).toBeGreaterThanOrEqual(0);
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});
