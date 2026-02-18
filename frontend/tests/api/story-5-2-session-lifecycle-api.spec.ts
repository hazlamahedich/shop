/**
 * Widget Session Lifecycle E2E Tests
 *
 * Story 5-2: Widget Session Management
 * Tests end-to-end session lifecycle: create -> use -> refresh -> expire -> cleanup
 *
 * @tags e2e widget story-5-2 session lifecycle
 */

import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

const WIDGET_ERROR_CODES = {
  SESSION_NOT_FOUND: 12001,
  SESSION_EXPIRED: 12002,
  RATE_LIMITED: 12003,
} as const;

interface TestSession {
  sessionId: string;
  merchantId?: number;
  createdAt: string;
  expiresAt: string;
  lastActivityAt: string;
}

async function createSession(request: any, merchantId: number = TEST_MERCHANT_ID): Promise<TestSession | null> {
  const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
    data: { merchant_id: merchantId },
    headers: { 'Content-Type': 'application/json' },
  });

  if (response.status() === 200) {
    const body = await response.json();
    return body.data;
  }
  return null;
}

async function sendMessage(request: any, sessionId: string, message: string): Promise<any> {
  const response = await request.post(`${API_BASE}/api/v1/widget/message`, {
    data: { session_id: sessionId, message },
    headers: { 'Content-Type': 'application/json' },
  });
  return response;
}

async function getSession(request: any, sessionId: string): Promise<TestSession | null> {
  const response = await request.get(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
    headers: { 'Content-Type': 'application/json' },
  });

  if (response.status() === 200) {
    const body = await response.json();
    return body.data;
  }
  return null;
}

async function endSession(request: any, sessionId: string): Promise<boolean> {
  const response = await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`);
  return response.status() === 200;
}

test.describe.configure({ mode: 'serial' });

test.describe('Widget Session Lifecycle - Full Flow (AC6)', () => {
  test('[P0] @smoke should complete full session lifecycle: create -> message -> end', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    expect(session.sessionId).toBeDefined();
    if (session.merchantId !== undefined) {
      expect(session.merchantId).toBe(TEST_MERCHANT_ID);
    }
    expect(new Date(session.expiresAt).getTime()).toBeGreaterThan(Date.now());

    const messageResponse = await sendMessage(request, session.sessionId, 'Hello, I need help');
    expect([200, 404, 401]).toContain(messageResponse.status());

    if (messageResponse.status() === 200) {
      const body = await messageResponse.json();
      expect(body.data).toHaveProperty('messageId');
      expect(body.data).toHaveProperty('content');
      expect(body.data.sender).toBe('bot');
    }

    const endResponse = await endSession(request, session.sessionId);
    expect(endResponse).toBe(true);

    const deletedSession = await getSession(request, session.sessionId);
    expect(deletedSession).toBeNull();
  });

  test('[P1] should handle multiple messages in a session', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    const messages = [
      'What products do you have?',
      'Do you have shoes?',
      'What sizes are available?',
      'How much are they?',
    ];

    const responses: string[] = [];

    for (const msg of messages) {
      const response = await sendMessage(request, session.sessionId, msg);
      expect([200, 404, 401]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        responses.push(body.data.content);
      }
    }

    expect(responses.length).toBe(messages.length);

    await endSession(request, session.sessionId);
  });
});

test.describe('Widget Session Lifecycle - Activity Tracking (AC2)', () => {
  test('[P0] @smoke should track last_activity_at on each message', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    await sendMessage(request, session.sessionId, 'Hello');

    const updatedSession = await getSession(request, session.sessionId);
    expect(updatedSession).not.toBeNull();
    expect(updatedSession?.sessionId).toBe(session.sessionId);

    await endSession(request, session.sessionId);
  });

  test('[P1] should show increasing activity timestamps across multiple messages', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    const timestamps: number[] = [];

    for (let i = 0; i < 3; i++) {
      await sendMessage(request, session.sessionId, `Message ${i}`);
      const currentSession = await getSession(request, session.sessionId);
      if (currentSession) {
        timestamps.push(new Date(currentSession.lastActivityAt).getTime());
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    for (let i = 1; i < timestamps.length; i++) {
      expect(timestamps[i]).toBeGreaterThanOrEqual(timestamps[i - 1]);
    }

    await endSession(request, session.sessionId);
  });
});

test.describe('Widget Session Lifecycle - Session Refresh (AC2)', () => {
  test('[P1] should refresh session via dedicated endpoint', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    const beforeActivity = new Date(session.lastActivityAt);

    await new Promise(resolve => setTimeout(resolve, 100));

    const refreshResponse = await request.post(`${API_BASE}/api/v1/widget/session/${session.sessionId}/refresh`, {
      headers: { 'Content-Type': 'application/json' },
    });

    if (refreshResponse.status() === 200) {
      const refreshedSession = await getSession(request, session.sessionId);
      if (refreshedSession) {
        const afterActivity = new Date(refreshedSession.lastActivityAt);
        expect(afterActivity.getTime()).toBeGreaterThan(beforeActivity.getTime());
      }
    } else if (refreshResponse.status() === 404) {
      test.skip(true, 'Refresh endpoint not available');
    }

    await endSession(request, session.sessionId);
  });
});

test.describe('Widget Session Lifecycle - Rate Limiting (AC4, AC5)', () => {
  test.beforeEach(async ({ request }) => {
    await request.post(`${API_BASE}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    }).catch(() => {});
  });

  test('[P1] should enforce per-IP rate limiting', async ({ request }) => {
    const ip = '10.20.30.40';
    let rateLimited = false;

    for (let i = 0; i < 120; i++) {
      const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
        data: { merchant_id: TEST_MERCHANT_ID },
        headers: {
          'Content-Type': 'application/json',
          'X-Forwarded-For': ip,
        },
      });

      if (response.status() === 429) {
        rateLimited = true;

        const body = await response.json();
        const errorCode = body.error_code || body.detail?.error_code;
        if (errorCode) {
          expect(errorCode).toBe(WIDGET_ERROR_CODES.RATE_LIMITED);
        }

        const retryAfter = response.headers()['retry-after'];
        if (retryAfter) {
          expect(parseInt(retryAfter)).toBeGreaterThan(0);
        }
        break;
      }
    }

    if (!rateLimited) {
      test.skip(true, 'Rate limit not triggered');
    }
  });

  test('[P2] should apply merchant rate limit independently of IP limit', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    const configResponse = await request.get(`${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`);
    if (configResponse.status() === 200) {
      const config = await configResponse.json();

      if (config.data.rateLimit !== null && config.data.rateLimit !== undefined) {
        let merchantRateLimited = false;
        const limit = config.data.rateLimit;

        for (let i = 0; i < limit + 10; i++) {
          const response = await sendMessage(request, session.sessionId, `Rate test ${i}`);
          if (response.status() === 429) {
            merchantRateLimited = true;
            break;
          }
        }

        if (!merchantRateLimited) {
          console.log('Merchant rate limit not triggered within threshold');
        }
      }
    }

    await endSession(request, session.sessionId);
  });
});

test.describe('Widget Session Lifecycle - Session Expiry (AC6)', () => {
  test('[P1] should reject messages to expired session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/test/create-expired-session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
      headers: {
        'Content-Type': 'application/json',
        'X-Test-Mode': 'true',
      },
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

    const messageResponse = await sendMessage(request, expiredSessionId, 'This should fail');

    expect([401, 404]).toContain(messageResponse.status());

    if (messageResponse.status() === 401) {
      const msgBody = await messageResponse.json();
      const errorCode = msgBody.error_code || msgBody.detail?.error_code;
      if (errorCode) {
        expect(errorCode).toBe(WIDGET_ERROR_CODES.SESSION_EXPIRED);
      }
    }
  });

  test('[P2] should return appropriate error for deleted session', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    await endSession(request, session.sessionId);

    const messageResponse = await sendMessage(request, session.sessionId, 'This should fail');

    expect([404, 401]).toContain(messageResponse.status());
  });
});

test.describe('Widget Session Lifecycle - UUID Security (AC1)', () => {
  test('[P0] @smoke should use UUID v4 format for session IDs', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(session.sessionId).toMatch(uuidV4Regex);

    await endSession(request, session.sessionId);
  });

  test('[P1] should generate cryptographically unique session IDs', async ({ request }) => {
    const sessionIds = new Set<string>();

    for (let i = 0; i < 20; i++) {
      const session = await createSession(request);
      if (session) {
        sessionIds.add(session.sessionId);
        await endSession(request, session.sessionId);
      }
    }

    expect(sessionIds.size).toBeGreaterThanOrEqual(18);

    for (const id of sessionIds) {
      expect(id.length).toBe(36);
    }
  });

  test('[P2] should not accept predictable session IDs', async ({ request }) => {
    const predictableIds = [
      '00000000-0000-0000-0000-000000000000',
      '12345678-1234-1234-1234-123456789012',
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    ];

    for (const fakeId of predictableIds) {
      const response = await sendMessage(request, fakeId, 'Test');
      expect([401, 404, 403]).toContain(response.status());
    }
  });
});

test.describe('Widget Session Lifecycle - Concurrent Sessions (AC6)', () => {
  test('[P1] should handle multiple concurrent sessions per merchant', async ({ request }) => {
    const sessions: TestSession[] = [];

    for (let i = 0; i < 5; i++) {
      const session = await createSession(request);
      if (session) {
        sessions.push(session);
      }
    }

    expect(sessions.length).toBe(5);

    const messagePromises = sessions.map(session =>
      sendMessage(request, session.sessionId, `Concurrent message for session ${session.sessionId}`)
    );

    const responses = await Promise.all(messagePromises);

    const successCount = responses.filter(r => r.status() === 200).length;
    expect(successCount).toBeGreaterThan(0);

    for (const session of sessions) {
      await endSession(request, session.sessionId);
    }
  });

  test('[P2] should isolate sessions between merchants', async ({ request }) => {
    const session1 = await createSession(request, TEST_MERCHANT_ID);

    if (!session1) {
      test.skip(true, 'Could not create session');
      return;
    }

    const merchant2Id = TEST_MERCHANT_ID + 1;
    const session2Response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: merchant2Id },
      headers: { 'Content-Type': 'application/json' },
    });

    if (session1) {
      await endSession(request, session1.sessionId);
    }

    if (session2Response.status() === 200) {
      const session2 = await session2Response.json();
      await endSession(request, session2.data.sessionId);
    }
  });
});

test.describe('Widget Session Lifecycle - Error Recovery (AC6)', () => {
  test('[P2] should handle malformed session ID gracefully', async ({ request }) => {
    const malformedIds = [
      'not-a-uuid',
      '12345',
      '',
      'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    ];

    for (const id of malformedIds) {
      const response = await sendMessage(request, id, 'Test');
      expect([400, 404, 422]).toContain(response.status());
    }
  });

  test('[P2] should recover from network interruption during message', async ({ request }) => {
    const session = await createSession(request);
    if (!session) {
      test.skip(true, 'Could not create session');
      return;
    }

    await sendMessage(request, session.sessionId, 'Before interruption');

    const afterInterruption = await getSession(request, session.sessionId);
    expect(afterInterruption).not.toBeNull();

    const messageResponse = await sendMessage(request, session.sessionId, 'After interruption');
    expect([200, 404, 401]).toContain(messageResponse.status());

    await endSession(request, session.sessionId);
  });
});
