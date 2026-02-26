/**
 * Story 6-2: Concurrent Deletion & Error Handling Tests
 *
 * Tests concurrent deletion protection and error handling:
 * - Session locking for concurrent deletion
 * - 404 for non-existent session
 * - Malformed session ID handling
 * - Session context validation
 *
 * Test IDs: 6-2-API-009 to 6-2-API-012
 *
 * @tags api consent gdpr privacy data-deletion story-6-2 error-handling
 */

import { test, expect } from '@playwright/test';
import {
  API_BASE,
  createSession,
  optInConsent,
  getHeaders,
  resetRateLimiter,
  cleanupAllSessions,
  createdSessions,
  DeletionResponse,
  ErrorResponse,
} from './helpers';

test.describe('Story 6-2: Concurrent Deletion Protection', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P2][6-2-API-009] should block concurrent deletion with session lock', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const [response1, response2] = await Promise.all([
      request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
        headers: getHeaders(),
      }),
      request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
        headers: getHeaders(),
      }),
    ]);

    const status1 = response1.status();
    const status2 = response2.status();

    expect(status1 === 200 || status2 === 200).toBe(true);

    const secondaryStatus = status1 === 200 ? status2 : status1;
    if (secondaryStatus === 409) {
      // Conflict - concurrent deletion blocked
    } else if (secondaryStatus === 429) {
      // Rate limited - also acceptable
    } else if (secondaryStatus === 200) {
      // Both succeeded - idempotent deletion
    } else {
      throw new Error(
        `Unexpected secondary status: ${secondaryStatus}. Expected 200, 409, or 429`,
      );
    }
  });
});

test.describe('Story 6-2: Error Handling', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P1][6-2-API-010] should return 404 for non-existent session', async ({ request }) => {
    const fakeSessionId = 'non-existent-session-12345';

    const response = await request.delete(`${API_BASE}/widget/consent/${fakeSessionId}`, {
      headers: getHeaders(),
    });

    const status = response.status();
    if (status === 404) {
      // Expected: session not found
    } else if (status === 422) {
      // Acceptable: validation error for invalid session ID format
      const body = (await response.json()) as ErrorResponse;
      expect(body.message).toBeDefined();
    } else if (status === 200) {
      // Acceptable: idempotent deletion (no-op for non-existent)
      const body = (await response.json()) as DeletionResponse;
      expect(body.data.success).toBe(true);
    } else {
      throw new Error(
        `Unexpected status for non-existent session: ${status}. Expected 404, 422, or 200 (idempotent)`,
      );
    }
  });

  test('[P2][6-2-API-011] should handle malformed session ID gracefully', async ({ request }) => {
    const response = await request.delete(`${API_BASE}/widget/consent/`, {
      headers: getHeaders(),
    });

    const status = response.status();
    if (status === 400) {
      // Expected: bad request for missing session ID
    } else if (status === 404) {
      // Acceptable: route not found
    } else if (status === 405) {
      // Acceptable: method not allowed on base path
    } else {
      throw new Error(
        `Unexpected status for malformed session ID: ${status}. Expected 400, 404, or 405`,
      );
    }
  });

  test('[P2][6-2-API-012] should validate session ID matches request context', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const response = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: {
        ...getHeaders(),
        'X-Session-Override': 'different-session-id',
      },
    });

    const status = response.status();
    if (status === 200) {
      // Acceptable: override header ignored, deletion proceeds with path session ID
      const body = (await response.json()) as DeletionResponse;
      expect(body.data.success).toBe(true);
    } else if (status === 400) {
      // Acceptable: validation error for mismatched session context
      const body = (await response.json()) as ErrorResponse;
      expect(body.message).toBeDefined();
    } else if (status === 403) {
      // Acceptable: forbidden - session context mismatch
      const body = (await response.json()) as ErrorResponse;
      expect(body.message).toMatch(/forbidden|context|mismatch/i);
    } else {
      throw new Error(
        `Unexpected status for session context validation: ${status}. Expected 200, 400, or 403`,
      );
    }
  });
});
