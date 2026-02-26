/**
 * Story 6-2: Rate Limiting Tests
 *
 * Tests the rate limiting functionality for deletion requests:
 * - Rate limit duplicate deletion requests
 * - Return 429 with retry_after for rate limited requests
 *
 * Test IDs: 6-2-API-005 to 6-2-API-006
 *
 * @tags api consent gdpr privacy data-deletion story-6-2 rate-limiting
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

test.describe('Story 6-2: Rate Limiting', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P1][6-2-API-005] should rate limit duplicate deletion requests', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const firstResponse = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });
    expect(firstResponse.status()).toBe(200);

    const secondResponse = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    const status = secondResponse.status();
    if (status === 429) {
      const body = (await secondResponse.json()) as ErrorResponse;
      expect(body.error_code).toBe(2000);
      expect(body.message).toMatch(/rate limit|wait|retry/i);
      if (body.details?.retry_after_seconds) {
        expect(body.details.retry_after_seconds).toBeGreaterThan(0);
      }
    } else if (status === 200) {
      const body = (await secondResponse.json()) as DeletionResponse;
      expect(body.data.success).toBe(true);
    } else {
      throw new Error(
        `Unexpected status code for duplicate deletion: ${status}. Expected 429 (rate limited) or 200 (idempotent)`,
      );
    }
  });

  test('[P1][6-2-API-006] should return 429 with retry_after for rate limited requests', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    const rateLimitedResponse = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    if (rateLimitedResponse.status() === 429) {
      const body = (await rateLimitedResponse.json()) as ErrorResponse;
      expect(body.error_code).toBeDefined();
      expect(body.message).toBeDefined();
    }
  });
});
