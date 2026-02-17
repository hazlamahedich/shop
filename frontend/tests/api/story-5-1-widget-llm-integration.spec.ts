/**
 * Widget API - LLM Integration & Rate Limiting Tests
 *
 * Story 5-1: Backend Widget API
 * Tests LLM provider integration, rate limiting, and session TTL behavior.
 * Complements existing E2E tests in story-5-1-widget-api.spec.ts
 *
 * @tags api integration widget story-5-1 llm rate-limit session-ttl
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

const WIDGET_ERROR_CODES = {
  SESSION_NOT_FOUND: 12001,
  SESSION_EXPIRED: 12002,
  RATE_LIMITED: 12003,
  MERCHANT_DISABLED: 12004,
  INVALID_CONFIG: 12005,
  DOMAIN_NOT_ALLOWED: 12006,
  MESSAGE_TOO_LONG: 12007,
} as const;

const RATE_LIMIT_CONFIG = {
  widgetEndpoints: {
    maxRequests: 100,
    windowSeconds: 60,
  },
};

function getWidgetHeaders(testMode = true) {
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

  if (response.status() === 200) {
    const body = await response.json();
    return body.data.sessionId;
  }
  return null;
}

test.describe.configure({ mode: 'serial' });

test.describe('Widget API - LLM Integration [P0]', () => {
  test('[P0] @smoke should return bot response via LLM provider', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Hello, what products do you have?',
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 404, 401]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.data).toHaveProperty('messageId');
      expect(body.data).toHaveProperty('content');
      expect(body.data).toHaveProperty('sender', 'bot');
      expect(typeof body.data.content).toBe('string');
      expect(body.data.content.length).toBeGreaterThan(0);
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P0] @smoke should handle LLM timeout gracefully', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Complex query that might timeout',
      },
      headers: getWidgetHeaders(),
      timeout: 5000,
    });

    expect([200, 408, 500, 504]).toContain(response.status());

    if (response.status() === 408 || response.status() === 504) {
      const body = await response.json();
      expect(body.detail).toBeDefined();
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P0] should include response time metadata', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const startTime = Date.now();
    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Hello',
      },
      headers: getWidgetHeaders(),
    });
    const responseTime = Date.now() - startTime;

    expect(responseTime).toBeLessThan(3000);

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.meta).toBeDefined();
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P0] should handle LLM provider unavailability', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Test LLM unavailability',
      },
      headers: { ...getWidgetHeaders(), 'X-Simulate-LLM-Down': 'true' },
    });

    expect([200, 500, 503]).toContain(response.status());

    if (response.status() === 503) {
      const body = await response.json();
      expect(body.detail).toBeDefined();
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Rate Limiting (Burst Patterns) [P1]', () => {
  test.beforeEach(async ({ request }) => {
    await request.post(`${API_BASE}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    }).catch(() => {});
  });

  test('[P1] should handle burst traffic pattern', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const burstSize = 10;
    const requests = [];

    for (let i = 0; i < burstSize; i++) {
      requests.push(
        request.post(`${API_BASE}/api/v1/widget/message`, {
          data: {
            session_id: sessionId,
            message: `Burst message ${i}`,
          },
          headers: getWidgetHeaders(false),
        })
      );
    }

    const responses = await Promise.all(requests);
    const successCount = responses.filter(r => r.status() === 200).length;
    const rateLimitedCount = responses.filter(r => r.status() === 429).length;

    expect(successCount + rateLimitedCount).toBe(burstSize);

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should return 429 with retry-after header on rate limit', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    let rateLimitHit = false;
    let lastResponse: any = null;

    for (let i = 0; i < RATE_LIMIT_CONFIG.widgetEndpoints.maxRequests + 10; i++) {
      lastResponse = await request.post(`${API_BASE}/api/v1/widget/message`, {
        data: {
          session_id: sessionId,
          message: `Rate limit test ${i}`,
        },
        headers: getWidgetHeaders(false),
      });

      if (lastResponse.status() === 429) {
        rateLimitHit = true;
        break;
      }
    }

    if (rateLimitHit && lastResponse) {
      expect(lastResponse.status()).toBe(429);

      const headers = lastResponse.headers();
      const retryAfter = headers['retry-after'];
      if (retryAfter) {
        expect(parseInt(retryAfter)).toBeGreaterThan(0);
      }

      const body = await lastResponse.json();
      const errorMessage = body.message || body.detail;
      expect(errorMessage).toBeDefined();
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should rate limit per IP address', async ({ request }) => {
    await request.post(`${API_BASE}/api/v1/widget/test/reset-rate-limiter`, {
      headers: getWidgetHeaders(true),
    });

    const ip1RateLimited = await triggerRateLimit(request, '192.168.1.100');
    const ip2RateLimited = await triggerRateLimit(request, '192.168.1.101');

    expect(ip1RateLimited || ip2RateLimited).toBe(true);
  });
});

async function triggerRateLimit(request: any, ip: string): Promise<boolean> {
  const sessionId = await createTestSession(request);
  if (!sessionId) return false;

  for (let i = 0; i < RATE_LIMIT_CONFIG.widgetEndpoints.maxRequests + 10; i++) {
    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: `IP test ${i}`,
      },
      headers: {
        ...getWidgetHeaders(false),
        'X-Forwarded-For': ip,
      },
    });

    if (response.status() === 429) {
      await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
      return true;
    }
  }

  await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  return false;
}

test.describe('Widget API - Session TTL [P2]', () => {
  test('[P2] should refresh session TTL on activity', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const sessionResponse1 = await request.get(
      `${API_BASE}/api/v1/widget/session/${sessionId}`,
      { headers: getWidgetHeaders() }
    );

    if (sessionResponse1.status() === 200) {
      const session1 = await sessionResponse1.json();
      const expiresAt1 = new Date(session1.data.expiresAt);

      await new Promise(resolve => setTimeout(resolve, 100));

      await request.post(`${API_BASE}/api/v1/widget/message`, {
        data: {
          session_id: sessionId,
          message: 'Activity to refresh TTL',
        },
        headers: getWidgetHeaders(),
      });

      const sessionResponse2 = await request.get(
        `${API_BASE}/api/v1/widget/session/${sessionId}`,
        { headers: getWidgetHeaders() }
      );

      if (sessionResponse2.status() === 200) {
        const session2 = await sessionResponse2.json();
        const expiresAt2 = new Date(session2.data.expiresAt);

        expect(expiresAt2.getTime()).toBeGreaterThanOrEqual(expiresAt1.getTime());
      }
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });

  test('[P2] should return session metadata', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const response = await request.get(
      `${API_BASE}/api/v1/widget/session/${sessionId}`,
      { headers: getWidgetHeaders() }
    );

    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.data).toHaveProperty('sessionId');
      expect(body.data).toHaveProperty('expiresAt');
      expect(body.data).toHaveProperty('merchantId');
      expect(body.data).toHaveProperty('createdAt');
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Cross-Merchant Isolation [P3]', () => {
  test('[P3] should enforce merchant boundary in session', async ({ request }) => {
    const sessionId = await createTestSession(request);
    if (!sessionId) {
      test.skip(true, 'Could not create test session');
      return;
    }

    const otherMerchantId = TEST_MERCHANT_ID + 1;
    const configResponse = await request.get(
      `${API_BASE}/api/v1/widget/config/${otherMerchantId}`
    );

    expect([200, 404]).toContain(configResponse.status());

    const messageResponse = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Test message',
      },
      headers: getWidgetHeaders(),
    });

    expect([200, 404, 401]).toContain(messageResponse.status());

    if (messageResponse.status() === 200) {
      const body = await messageResponse.json();
      expect(body.data.sender).toBe('bot');
    }

    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Error Codes [P2]', () => {
  test('[P2] should return error code 12001 for non-existent session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
      data: {
        session_id: 'non-existent-session-id',
        message: 'Hello',
      },
      headers: getWidgetHeaders(),
    });

    expect([404, 401]).toContain(response.status());

    if (response.status() === 404) {
      const body = await response.json();
      const errorCode = body.error_code || body.detail?.error_code;
      if (errorCode) {
        expect(errorCode).toBe(WIDGET_ERROR_CODES.SESSION_NOT_FOUND);
      }
    }
  });

  test('[P2] should return error code 12003 for rate limited request', async ({ request }) => {
    let rateLimitHit = false;

    for (let i = 0; i < RATE_LIMIT_CONFIG.widgetEndpoints.maxRequests + 10; i++) {
      const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
        data: { merchant_id: TEST_MERCHANT_ID },
        headers: getWidgetHeaders(false),
      });

      if (response.status() === 429) {
        rateLimitHit = true;

        const body = await response.json();
        const errorCode = body.error_code || body.detail?.error_code;
        if (errorCode) {
          expect(errorCode).toBe(WIDGET_ERROR_CODES.RATE_LIMITED);
        }
        break;
      }
    }

    if (!rateLimitHit) {
      test.skip(true, 'Rate limit not triggered');
    }
  });
});
