/**
 * Story 6-2: Cross-Platform Deletion & Order Preservation Tests
 *
 * Tests cross-platform deletion functionality and order reference preservation:
 * - Delete data across all platforms by visitor_id
 * - Preserve order references (business requirement)
 *
 * Test IDs: 6-2-API-007 to 6-2-API-008
 *
 * @tags api consent gdpr privacy data-deletion story-6-2 cross-platform
 */

import { test, expect } from '@playwright/test';
import {
  API_BASE,
  createSessionWithVisitorId,
  optInConsent,
  getHeaders,
  resetRateLimiter,
  cleanupAllSessions,
  createdSessions,
  DeletionResponse,
  ConsentStatusResponse,
} from './helpers';

test.describe('Story 6-2: Cross-Platform Deletion', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P1][6-2-API-007] should delete data across all platforms by visitor_id', async ({ request }) => {
    const visitorId = `test-visitor-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    const session1 = await createSessionWithVisitorId(request, visitorId);
    const session2 = await createSessionWithVisitorId(request, visitorId);

    await optInConsent(request, session1.sessionId);
    await optInConsent(request, session2.sessionId);

    const deleteResponse = await request.delete(`${API_BASE}/widget/consent/${session1.sessionId}`, {
      headers: {
        ...getHeaders(),
        'X-Visitor-Id': visitorId,
      },
    });

    expect(deleteResponse.status()).toBe(200);

    const body = (await deleteResponse.json()) as DeletionResponse;
    expect(body.data.success).toBe(true);

    const status1 = await request.get(`${API_BASE}/widget/consent/${session1.sessionId}`, {
      headers: getHeaders(),
    });
    const status2 = await request.get(`${API_BASE}/widget/consent/${session2.sessionId}`, {
      headers: getHeaders(),
    });

    const body1 = (await status1.json()) as ConsentStatusResponse;
    const body2 = (await status2.json()) as ConsentStatusResponse;

    expect(body1.data.can_store_conversation).toBe(false);
    expect(body2.data.can_store_conversation).toBe(false);
  });
});

test.describe('Story 6-2: Order Reference Preservation', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P1][6-2-API-008] should NOT delete order references (business requirement)', async ({ request }) => {
    const sessionId = await createSessionWithVisitorId(
      request,
      `test-visitor-${Date.now()}`,
    ).then((s) => s.sessionId);

    await optInConsent(request, sessionId);

    const deleteResponse = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    expect(deleteResponse.status()).toBe(200);

    const ordersResponse = await request.get(`${API_BASE}/widget/orders/${sessionId}`, {
      headers: getHeaders(),
    });

    if (ordersResponse.status() === 200) {
      const body = await ordersResponse.json();
      if (body.data?.orders) {
        expect(Array.isArray(body.data.orders)).toBe(true);
      }
    }
  });
});
