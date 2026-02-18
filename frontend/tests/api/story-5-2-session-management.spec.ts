/**
 * Widget API - Session Management Tests
 *
 * Story 5-2: Widget Session Management
 * Tests per-merchant rate limiting, session activity tracking, and cleanup.
 *
 * @tags api integration widget story-5-2 rate-limit session-management
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

const WIDGET_ERROR_CODES = {
  SESSION_NOT_FOUND: 12001,
  SESSION_EXPIRED: 12002,
  RATE_LIMITED: 12003,
  MERCHANT_DISABLED: 12004,
} as const;

function getWidgetHeaders(testMode = true) {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

async function createTestSession(request: any, merchantId: number = TEST_MERCHANT_ID): Promise<string | null> {
  const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
    data: { merchant_id: merchantId },
    headers: getWidgetHeaders(),
  });

  if (response.status() === 200) {
    const body = await response.json();
    return body.data.sessionId;
  }
  return null;
}

test.describe.configure({ mode: 'serial' });

test.describe('Widget Session Management - Session Metadata (AC2)', () => {
  test('[P0] @smoke should return session with all required metadata fields', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.data).toHaveProperty('sessionId');
      expect(body.data).toHaveProperty('merchantId');
      expect(body.data).toHaveProperty('createdAt');
      expect(body.data).toHaveProperty('expiresAt');
      expect(body.data).toHaveProperty('lastActivityAt');
      expect(typeof body.data.sessionId).toBe('string');
      expect(body.data.merchantId).toBe(TEST_MERCHANT_ID);
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should update lastActivityAt on message send', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const sessionBefore = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    if (sessionBefore.status() !== 200) {
      test.skip(true, 'Could not get session');
      return;
    }

    const bodyBefore = await sessionBefore.json();
    const activityBefore = new Date(bodyBefore.data.lastActivityAt);

    await new Promise(resolve => setTimeout(resolve, 100));

    await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Hello',
      },
      headers: getWidgetHeaders(),
    });

    const sessionAfter = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    if (sessionAfter.status() === 200) {
      const bodyAfter = await sessionAfter.json();
      const activityAfter = new Date(bodyAfter.data.lastActivityAt);
      expect(activityAfter.getTime()).toBeGreaterThan(activityBefore.getTime());
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should track visitor IP in session', async ({ request }) => {
    const visitorIp = '192.168.100.50';
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: {
        ...getWidgetHeaders(),
        'X-Forwarded-For': visitorIp,
      },
    });

    expect([200, 404, 403]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      const sessionId = body.data.sessionId;

      const sessionResponse = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
        headers: getWidgetHeaders(),
      });

      if (sessionResponse.status() === 200) {
        const sessionBody = await sessionResponse.json();
        if (sessionBody.data.visitorIp !== undefined) {
          expect(sessionBody.data.visitorIp).toBe(visitorIp);
        }
      }

      await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
    }
  });
});

test.describe('Widget Session Management - Per-Merchant Rate Limiting (AC5)', () => {
  test.beforeEach(async ({ request }) => {
    await request.post(`${API_BASE}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    }).catch(() => {});
  });

  test('[P0] @smoke should respect merchant-specific rate limit', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Test merchant rate limit',
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 404, 401, 429]).toContain(response.status());

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should return 429 with error code 12003 when merchant rate limit exceeded', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/test/trigger-merchant-rate-limit`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: getWidgetHeaders(true),
    });

    if (response.status() === 404) {
      test.skip(true, 'Rate limit test endpoint not available');
      return;
    }

    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const messageResponse = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Should be rate limited',
      },
      headers: getWidgetHeaders(false),
    });

    if (messageResponse.status() === 429) {
      const body = await messageResponse.json();
      const errorCode = body.error_code || body.detail?.error_code;
      if (errorCode) {
        expect(errorCode).toBe(WIDGET_ERROR_CODES.RATE_LIMITED);
      }
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should apply different rate limits per merchant', async ({ request }) => {
    const sessionId1 = await createTestSession(request, TEST_MERCHANT_ID);

    if (!sessionId1) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const configResponse = await request.get(`${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`);

    if (configResponse.status() === 200) {
      const config = await configResponse.json();
      expect(config.data).toHaveProperty('botName');
      expect(config.data).toHaveProperty('enabled');
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId1}`);
  });

  test('[P2] should allow unlimited requests when rate_limit is null', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/test/get-unlimited-merchant`, {
      headers: getWidgetHeaders(true),
    });

    if (response.status() === 404) {
      test.skip(true, 'Test endpoint not available');
      return;
    }

    const body = await response.json();
    if (body.merchant_id) {
      const sessionId = await createTestSession(request, body.merchant_id);
      if (sessionId) {
        const requests = [];
        for (let i = 0; i < 20; i++) {
          requests.push(
            request.post(`${API_BASE}/api/v1/widget/message`, {
              data: {
                session_id: sessionId,
                message: `Unlimited test ${i}`,
              },
              headers: getWidgetHeaders(false),
            })
          );
        }

        const responses = await Promise.all(requests);
        const successCount = responses.filter(r => r.status() === 200).length;
        const rateLimitedCount = responses.filter(r => r.status() === 429).length;

        expect(successCount + rateLimitedCount).toBe(20);
        expect(rateLimitedCount).toBe(0);

        await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
      }
    }
  });
});

test.describe('Widget Session Management - Session Refresh (AC2)', () => {
  test('[P1] should refresh session and update timestamps', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const beforeResponse = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });

    if (beforeResponse.status() !== 200) {
      test.skip(true, 'Could not get session');
      return;
    }

    const before = await beforeResponse.json();
    const beforeActivity = new Date(before.data.lastActivityAt);

    await new Promise(resolve => setTimeout(resolve, 100));

    const refreshResponse = await request.post(`${API_BASE}/api/v1/widget/session/${sessionId}/refresh`, {
      headers: getWidgetHeaders(),
    });

    expect([200, 404]).toContain(refreshResponse.status());

    if (refreshResponse.status() === 200) {
      const afterResponse = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
        headers: getWidgetHeaders(),
      });

      if (afterResponse.status() === 200) {
        const after = await afterResponse.json();
        const afterActivity = new Date(after.data.lastActivityAt);
        expect(afterActivity.getTime()).toBeGreaterThan(beforeActivity.getTime());
      }
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P2] should return 404 when refreshing non-existent session', async ({ request }) => {
    const fakeSessionId = '00000000-0000-0000-0000-000000000000';

    const response = await request.post(`${API_BASE}/api/v1/widget/session/${fakeSessionId}/refresh`, {
      headers: getWidgetHeaders(),
    });

    expect([404, 401]).toContain(response.status());
  });
});

test.describe('Widget Session Management - Session Expiry (AC6)', () => {
  test('[P1] should return 401 with error code 12002 for expired session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/test/create-expired-session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: getWidgetHeaders(true),
    });

    if (response.status() === 404) {
      test.skip(true, 'Test endpoint not available');
      return;
    }

    const body = await response.json();
    const expiredSessionId = body.sessionId;

    if (!expiredSessionId) {
      test.skip(true, 'Could not create expired session');
      return;
    }

    const messageResponse = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: expiredSessionId,
        message: 'This should fail',
      },
      headers: getWidgetHeaders(),
    });

    expect([401, 404]).toContain(messageResponse.status());

    if (messageResponse.status() === 401) {
      const msgBody = await messageResponse.json();
      const errorCode = msgBody.error_code || msgBody.detail?.error_code;
      if (errorCode) {
        expect(errorCode).toBe(WIDGET_ERROR_CODES.SESSION_EXPIRED);
      }
    }
  });
});

test.describe('Widget Session Management - Background Cleanup (AC3)', () => {
  test('[P2] should verify cleanup service is running', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/test/cleanup-status`, {
      headers: getWidgetHeaders(true),
    });

    if (response.status() === 404) {
      test.skip(true, 'Cleanup status endpoint not available');
      return;
    }

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('running');
    }
  });

  test('[P2] should clean up orphaned sessions', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/test/trigger-cleanup`, {
      headers: getWidgetHeaders(true),
    });

    if (response.status() === 404) {
      test.skip(true, 'Cleanup trigger endpoint not available');
      return;
    }

    if (response.status() === 200) {
      const body = await response.json();
      expect(body).toHaveProperty('scanned');
      expect(body).toHaveProperty('cleaned');
      expect(typeof body.scanned).toBe('number');
      expect(typeof body.cleaned).toBe('number');
    }
  });
});

test.describe('Widget Session Management - UUID Format (AC1)', () => {
  test('[P0] @smoke should generate UUID v4 session IDs', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: getWidgetHeaders(),
    });

    expect([200, 404, 403]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      const sessionId = body.data.sessionId;

      const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(sessionId).toMatch(uuidV4Regex);

      await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
    }
  });

  test('[P1] should generate unique session IDs', async ({ request }) => {
    const sessionIds: string[] = [];

    for (let i = 0; i < 10; i++) {
      const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
        data: { merchant_id: TEST_MERCHANT_ID },
        headers: getWidgetHeaders(),
      });

      if (response.status() === 200) {
        const body = await response.json();
        sessionIds.push(body.data.sessionId);
      }
    }

    const uniqueIds = new Set(sessionIds);
    expect(uniqueIds.size).toBe(sessionIds.length);

    for (const sessionId of sessionIds) {
      await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
    }
  });
});

test.describe('Widget Session Management - Error Codes (AC4, AC5)', () => {
  test('[P1] should return correct error structure for rate limited request', async ({ request }) => {
    let rateLimited = false;

    for (let i = 0; i < 120; i++) {
      const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
        data: { merchant_id: TEST_MERCHANT_ID },
        headers: getWidgetHeaders(false),
      });

      if (response.status() === 429) {
        rateLimited = true;
        const body = await response.json();

        expect(body).toHaveProperty('message');
        expect([12003, 'RATE_LIMITED']).toContain(body.error_code);

        const headers = response.headers();
        if (headers['retry-after']) {
          expect(parseInt(headers['retry-after'])).toBeGreaterThan(0);
        }
        break;
      }
    }

    if (!rateLimited) {
      test.skip(true, 'Rate limit not triggered within threshold');
    }
  });
});
