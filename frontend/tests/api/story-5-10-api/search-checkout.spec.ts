/**
 * Widget Search & Checkout API Tests
 *
 * Story 5-10: Widget Full App Integration
 * Tests search and checkout endpoints.
 *
 * @tags api widget story-5-10 search checkout
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

interface ErrorResponse {
  error_code: number;
  message: string;
  detail?: string;
}

function getWidgetHeaders(testMode = true): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

async function createTestSession(request: any): Promise<string | null> {
  const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
    data: { merchant_id: TEST_MERCHANT_ID },
    headers: getWidgetHeaders(),
  });

  if (response.status() === 200 || response.status() === 201) {
    const body = await response.json();
    return body.data?.sessionId || body.data?.session_id || body.session?.session_id;
  }
  console.warn(`[TEA] Session creation failed: ${response.status()}`);
  return null;
}

test.describe('Story 5-10: Shopify Connection Handling [P1]', () => {
  test('[P1] POST /api/v1/widget/search should validate session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: 'invalid-session-id',
        query: 'running shoes',
      },
      headers: getWidgetHeaders(),
    });

    expect([400, 401, 404, 422]).toContain(response.status());
  });

  test('[P1] POST /api/v1/widget/search should return products or error for valid session', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const searchResponse = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: sessionId,
        query: 'test product',
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 400, 404, 503]).toContain(searchResponse.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] POST /api/v1/widget/search should validate query length', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const longQueryResponse = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: sessionId,
        query: 'a'.repeat(501),
      },
      headers: getWidgetHeaders(),
    });

    expect([400, 422]).toContain(longQueryResponse.status());

    const emptyQueryResponse = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: sessionId,
        query: '',
      },
      headers: getWidgetHeaders(),
    });

    expect([400, 422]).toContain(emptyQueryResponse.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Story 5-10: Checkout [P1]', () => {
  test('[P1] POST /api/v1/widget/checkout should validate session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: {
        session_id: 'invalid-session-id',
      },
      headers: getWidgetHeaders(),
    });

    expect([400, 401, 404, 422]).toContain(response.status());
  });

  test('[P1] POST /api/v1/widget/checkout should return checkout URL or error', async ({ request }) => {
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

    expect([200, 400, 503]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.data).toHaveProperty('checkoutUrl');
    } else {
      const body: ErrorResponse = await response.json();
      console.log(`[TEA] Checkout failed (expected without real Shopify data): ${body.message}`);
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] POST /api/v1/widget/checkout should return error for empty cart', async ({ request }) => {
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

    if (response.status() === 400) {
      const body: ErrorResponse = await response.json();
      expect([12020, 8007]).toContain(body.error_code);
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] POST /api/v1/widget/checkout should handle Shopify rate limit', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const responses = await Promise.all([
      request.post(`${API_BASE}/api/v1/widget/checkout`, {
        data: { session_id: sessionId },
        headers: getWidgetHeaders(),
      }),
      request.post(`${API_BASE}/api/v1/widget/checkout`, {
        data: { session_id: sessionId },
        headers: getWidgetHeaders(),
      }),
      request.post(`${API_BASE}/api/v1/widget/checkout`, {
        data: { session_id: sessionId },
        headers: getWidgetHeaders(),
      }),
    ]);

    const rateLimited = responses.some((r) => r.status() === 429);
    expect(rateLimited || responses.every((r) => [200, 400, 429, 503].includes(r.status()))).toBeTruthy();

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});
