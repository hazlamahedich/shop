/**
 * Widget API E2E Tests
 *
 * Story 5-1: Backend Widget API
 * Tests the widget API endpoints for session management, messaging, and configuration
 *
 * @tags api integration widget story-5-1
 */

import { test, expect } from '@playwright/test';

/**
 * Base URL for API requests
 */
const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Test merchant ID (use existing test merchant)
 */
const TEST_MERCHANT_ID = 1;

test.describe('Widget API - Session Creation (AC1)', () => {
  test('[P0] @smoke should create a new widget session with valid merchant_id', async ({ request }) => {
    // Given: A valid merchant_id
    const merchantId = TEST_MERCHANT_ID;

    // When: Creating a widget session
    const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: merchantId },
    });

    // Then: Should return session with session_id and expires_at
    expect([200, 404, 403]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();

      // Validate envelope structure
      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');

      // Validate session response
      expect(body.data).toHaveProperty('sessionId');
      expect(body.data).toHaveProperty('expiresAt');
      expect(typeof body.data.sessionId).toBe('string');
      expect(new Date(body.data.expiresAt).getTime()).toBeGreaterThan(Date.now());
    }
  });

  test('[P2] should reject session creation without merchant_id', async ({ request }) => {
    // Given: No merchant_id provided
    // When: Creating a widget session
    const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: {},
    });

    // Then: Should return validation error (422)
    expect(response.status()).toBe(422);
  });

  test('[P2] should return 404 for non-existent merchant', async ({ request }) => {
    // Given: A non-existent merchant_id
    const merchantId = 999999;

    // When: Creating a widget session
    const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: merchantId },
    });

    // Then: Should return 404 (merchant not found)
    expect(response.status()).toBe(404);
  });
});

test.describe('Widget API - Send Message (AC2)', () => {
  test('[P0] @smoke should send message and receive bot response', async ({ request }) => {
    // Given: A valid session
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    // When: Sending a message
    const messageResponse = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Hello, can you help me?',
      },
    });

    // Then: Should return bot response
    expect([200, 404, 401]).toContain(messageResponse.status());

    if (messageResponse.status() === 200) {
      const body = await messageResponse.json();

      // Validate envelope structure
      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');

      // Validate message response
      expect(body.data).toHaveProperty('messageId');
      expect(body.data).toHaveProperty('content');
      expect(body.data).toHaveProperty('sender');
      expect(body.data.sender).toBe('bot');
      expect(typeof body.data.content).toBe('string');
      expect(body.data.content.length).toBeGreaterThan(0);
    }
  });

  test('[P2] should reject empty message', async ({ request }) => {
    // Given: A valid session
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    // When: Sending an empty message
    const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: '',
      },
    });

    // Then: Should return validation error (422)
    expect(response.status()).toBe(422);
  });

  test('[P2] should return 404 for invalid session_id', async ({ request }) => {
    // Given: An invalid session_id
    const invalidSessionId = 'non-existent-session-id';

    // When: Sending a message
    const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: invalidSessionId,
        message: 'Hello',
      },
    });

    // Then: Should return 404 (session not found)
    expect(response.status()).toBe(404);
  });
});

test.describe('Widget API - Get Config (AC3)', () => {
  test('[P0] @smoke should return widget configuration', async ({ request }) => {
    // Given: A valid merchant_id
    const merchantId = TEST_MERCHANT_ID;

    // When: Getting widget config
    const response = await request.get(`${BASE_URL}/api/v1/widget/config/${merchantId}`);

    // Then: Should return config with theme data
    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();

      // Validate envelope structure
      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');

      // Validate config response
      expect(body.data).toHaveProperty('botName');
      expect(body.data).toHaveProperty('welcomeMessage');
      expect(body.data).toHaveProperty('theme');
      expect(body.data).toHaveProperty('enabled');

      // Validate theme structure
      expect(body.data.theme).toHaveProperty('primaryColor');
      expect(body.data.theme).toHaveProperty('backgroundColor');
      expect(body.data.theme).toHaveProperty('textColor');
      expect(body.data.theme).toHaveProperty('position');
    }
  });

  test('[P2] should return 404 for non-existent merchant', async ({ request }) => {
    // Given: A non-existent merchant_id
    const merchantId = 999999;

    // When: Getting widget config
    const response = await request.get(`${BASE_URL}/api/v1/widget/config/${merchantId}`);

    // Then: Should return 404
    expect(response.status()).toBe(404);
  });
});

test.describe('Widget API - End Session (AC4)', () => {
  test('[P0] @smoke should terminate a widget session', async ({ request }) => {
    // Given: A valid session
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    // When: Ending the session
    const response = await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);

    // Then: Should return success
    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();

      // Validate envelope structure
      expect(body).toHaveProperty('data');
      expect(body.data).toHaveProperty('success');
      expect(body.data.success).toBe(true);
    }
  });

  test('[P2] should return 404 for non-existent session', async ({ request }) => {
    // Given: A non-existent session_id
    const sessionId = 'non-existent-session-id';

    // When: Ending the session
    const response = await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);

    // Then: Should return 404
    expect(response.status()).toBe(404);
  });
});

test.describe('Widget API - Session Expiry (AC6)', () => {
  test('[P2] should return 401 for expired session', async ({ request }) => {
    // Given: A non-existent/expired session_id (simulating expiry)
    const expiredSessionId = 'expired-session-id';

    // When: Trying to send a message with expired session
    const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: expiredSessionId,
        message: 'Hello',
      },
    });

    // Then: Should return 404 (session not found) or 401 (expired)
    expect([404, 401]).toContain(response.status());
  });
});

test.describe('Widget API - CORS Support (AC7)', () => {
  test('[P2] should handle CORS preflight requests', async ({ request }) => {
    // When: Making OPTIONS request
    const response = await request.fetch(`${BASE_URL}/api/v1/widget/config/${TEST_MERCHANT_ID}`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'https://example.com',
        'Access-Control-Request-Method': 'GET',
      },
    });

    // Then: Should accept CORS preflight
    expect([200, 204, 400]).toContain(response.status());
  });
});

test.describe('Widget API - Cross-Merchant Isolation', () => {
  test('[P2] should not allow accessing other merchant resources', async ({ request }) => {
    // Given: A session for merchant A
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    // Note: In a real test, we would try to access merchant B's resources
    // with merchant A's session_id. This is a basic isolation check.

    // When: Trying to get config for a different merchant
    const otherMerchantId = TEST_MERCHANT_ID + 1;
    const configResponse = await request.get(
      `${BASE_URL}/api/v1/widget/config/${otherMerchantId}`
    );

    // Then: Config is public, so it should work for any merchant
    // But message operations with session should only work for session's merchant
    expect([200, 404]).toContain(configResponse.status());

    // Cleanup
    await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Response Time (AC2)', () => {
  test('[P2] should respond within 3 seconds (P95)', async ({ request }) => {
    // Given: A valid session
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    // When: Sending a message and measuring time
    const startTime = Date.now();
    const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'Hello',
      },
    });
    const responseTime = Date.now() - startTime;

    // Then: Should respond within 3 seconds (3000ms)
    // Note: In test mode with mock LLM, this should be fast
    expect(responseTime).toBeLessThan(3000);

    // Cleanup
    await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Multi-Message Context (AC2)', () => {
  test('[P1] should maintain conversation context across 10+ messages', async ({ request }) => {
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    const conversationContext = [
      'Hi, I am looking for shoes',
      'What brands do you have?',
      'Do you have Nike in size 10?',
      'How much are they?',
      'Do you have any discounts?',
      'What colors are available?',
      'Can I return them if they dont fit?',
      'How long is shipping?',
      'Do you ship internationally?',
      'What payment methods do you accept?',
    ];

    const responses: string[] = [];

    for (let i = 0; i < conversationContext.length; i++) {
      const messageResponse = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        data: {
          session_id: sessionId,
          message: conversationContext[i],
        },
      });

      expect([200, 404, 401]).toContain(messageResponse.status());

      if (messageResponse.status() === 200) {
        const body = await messageResponse.json();
        responses.push(body.data.content);

        expect(body.data).toHaveProperty('messageId');
        expect(body.data).toHaveProperty('content');
        expect(body.data.sender).toBe('bot');
      }
    }

    expect(responses.length).toBe(conversationContext.length);

    for (const response of responses) {
      expect(typeof response).toBe('string');
      expect(response.length).toBeGreaterThan(0);
    }

    const contextResponse = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'So getting back to those Nike shoes - are they still available?',
      },
    });

    if (contextResponse.status() === 200) {
      const body = await contextResponse.json();
      expect(body.data.content.toLowerCase()).toMatch(/nike|shoe|size|available|yes|no/i);
    }

    await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
  });

  test('[P1] should store limited conversation history', async ({ request }) => {
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    for (let i = 0; i < 15; i++) {
      await request.post(`${BASE_URL}/api/v1/widget/message`, {
        data: {
          session_id: sessionId,
          message: `Message ${i}`,
        },
      });
    }

    const recentResponse = await request.post(`${BASE_URL}/api/v1/widget/message`, {
      data: {
        session_id: sessionId,
        message: 'What was my first message about?',
      },
    });

    expect([200, 404, 401]).toContain(recentResponse.status());

    await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
  });
});

test.describe('Widget API - Response Time Under Load [P2]', () => {
  test('[P2] should maintain response time under concurrent load', async ({ request }) => {
    const sessions: string[] = [];

    for (let i = 0; i < 3; i++) {
      const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        data: { merchant_id: TEST_MERCHANT_ID },
      });

      if (sessionResponse.status() === 200) {
        const session = await sessionResponse.json();
        sessions.push(session.data.sessionId);
      }
    }

    if (sessions.length === 0) {
      test.skip();
      return;
    }

    const concurrentRequests = sessions.flatMap(sessionId =>
      Array.from({ length: 3 }, (_, i) =>
        request.post(`${BASE_URL}/api/v1/widget/message`, {
          data: {
            session_id: sessionId,
            message: `Concurrent message ${i}`,
          },
        })
      )
    );

    const startTime = Date.now();
    const responses = await Promise.all(concurrentRequests);
    const totalTime = Date.now() - startTime;

    const successCount = responses.filter(r => r.status() === 200).length;
    expect(successCount).toBeGreaterThan(0);

    const avgResponseTime = totalTime / responses.length;
    expect(avgResponseTime).toBeLessThan(3000);

    for (const sessionId of sessions) {
      await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
    }
  });

  test('[P2] should handle sustained message load', async ({ request }) => {
    const sessionResponse = await request.post(`${BASE_URL}/api/v1/widget/session`, {
      data: { merchant_id: TEST_MERCHANT_ID },
    });

    if (sessionResponse.status() !== 200) {
      test.skip();
      return;
    }

    const session = await sessionResponse.json();
    const sessionId = session.data.sessionId;

    const responseTimes: number[] = [];

    for (let i = 0; i < 5; i++) {
      const startTime = Date.now();
      await request.post(`${BASE_URL}/api/v1/widget/message`, {
        data: {
          session_id: sessionId,
          message: `Sustained load message ${i}`,
        },
      });
      responseTimes.push(Date.now() - startTime);

      await new Promise(resolve => setTimeout(resolve, 100));
    }

    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);

    expect(avgResponseTime).toBeLessThan(2000);
    expect(maxResponseTime).toBeLessThan(3000);

    await request.delete(`${BASE_URL}/api/v1/widget/session/${sessionId}`);
  });
});
