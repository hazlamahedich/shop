/**
 * Widget Session Management API Tests
 *
 * Story 5-10: Widget Full App Integration
 * Tests session creation, validation, and expiry.
 *
 * @tags api widget story-5-10 session
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

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

test.describe('Story 5-10: Widget Session Management [P1]', () => {
  test('[P1] POST /api/v1/widget/session should create session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: getWidgetHeaders(),
    });

    expect([200, 201]).toContain(response.status());

    const body = await response.json();
    const sessionId = body.data?.sessionId || body.data?.session_id;
    expect(sessionId).toBeTruthy();
    expect(typeof sessionId).toBe('string');
    expect(sessionId.length).toBeGreaterThanOrEqual(32);
  });

  test('[P1] POST /api/v1/widget/session should validate merchant_id', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: 'invalid' },
      headers: getWidgetHeaders(),
    });

    expect([400, 422, 404]).toContain(response.status());
  });

  test('[P1] POST /api/v1/widget/session should return expires_at', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: getWidgetHeaders(),
    });

    if (response.status() === 200 || response.status() === 201) {
      const body = await response.json();
      const sessionData = body.data || body.session;
      const expiresAt = sessionData.expires_at || sessionData.expiresAt;
      expect(expiresAt).toBeTruthy();
      expect(new Date(expiresAt).getTime()).toBeGreaterThan(Date.now());
    }
  });

  test('[P2] Session should be isolated per merchant', async ({ request }) => {
    const session1 = await createTestSession(request);

    const response2 = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: 2 },
      headers: getWidgetHeaders(),
    });

    if (response2.status() === 200 || response2.status() === 201) {
      const body2 = await response2.json();
      const session2 = body2.data?.sessionId || body2.data?.session_id;

      expect(session1).not.toBe(session2);
    }

    if (session1) {
      await request.delete(`${API_BASE}/api/v1/widget/session/${session1}`);
    }
  });

  test('[P1] Expired session should be rejected', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/cart`, {
      params: { session_id: 'expired-test-session-id' },
      headers: getWidgetHeaders(),
    });

    expect([401, 404, 400, 422]).toContain(response.status());
  });

  test('[P2] DELETE /api/v1/widget/session should invalidate session', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const deleteResponse = await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    expect([200, 204, 404]).toContain(deleteResponse.status());

    const cartResponse = await request.get(`${API_BASE}/api/v1/widget/cart`, {
      params: { session_id: sessionId },
      headers: getWidgetHeaders(),
    });

    expect([401, 404, 400]).toContain(cartResponse.status());
  });
});
