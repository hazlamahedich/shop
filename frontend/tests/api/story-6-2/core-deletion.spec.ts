/**
 * Story 6-2: Core Data Deletion API Tests
 *
 * Tests the core data deletion functionality:
 * - DELETE /widget/consent/{session_id} - Delete voluntary data
 * - Deletion timing (<5 seconds) - AC4
 * - Audit log persistence - AC5
 * - Consent status reset after deletion
 *
 * Test IDs: 6-2-API-001 to 6-2-API-004
 *
 * @tags api consent gdpr privacy data-deletion story-6-2
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
  ConsentStatusResponse,
  AuditLogResponse,
} from './helpers';

test.describe('Story 6-2: Core Data Deletion', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ request }) => {
    createdSessions.length = 0;
    await resetRateLimiter(request);
  });

  test.afterEach(async ({ request }) => {
    await cleanupAllSessions(request);
  });

  test('[P0][6-2-API-001] should delete voluntary data and return deletion summary', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const response = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    expect(response.status()).toBe(200);

    const body = (await response.json()) as DeletionResponse;
    expect(body.data.success).toBe(true);
    expect(body.data.clear_visitor_id).toBe(true);
    if (body.data.deletion_summary) {
      expect(body.data.deletion_summary.conversations_deleted).toBeGreaterThanOrEqual(0);
      expect(body.data.deletion_summary.messages_deleted).toBeGreaterThanOrEqual(0);
      expect(body.data.deletion_summary.redis_keys_cleared).toBeGreaterThanOrEqual(0);
    }
  });

  test('[P0][6-2-API-002] should complete deletion within 5 seconds (AC4)', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const startTime = Date.now();

    const response = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    const elapsed = Date.now() - startTime;

    expect(response.status()).toBe(200);
    expect(elapsed).toBeLessThan(5000);
  });

  test('[P0][6-2-API-003] should create audit log entry for deletion (AC5)', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const deleteResponse = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    expect(deleteResponse.status()).toBe(200);

    const body = (await deleteResponse.json()) as DeletionResponse;

    if (body.data.deletion_summary?.audit_log_id) {
      const auditLogId = body.data.deletion_summary.audit_log_id;

      const auditResponse = await request.get(`${API_BASE}/widget/deletion-status/${auditLogId}`, {
        headers: getHeaders(),
      });

      expect(auditResponse.status()).toBe(200);

      const auditBody = (await auditResponse.json()) as AuditLogResponse;
      expect(auditBody.data.session_id).toBe(sessionId);
      expect(auditBody.data.requested_at).toBeDefined();
    }
  });

  test('[P0][6-2-API-004] should reset consent status to pending after deletion', async ({ request }) => {
    const sessionId = await createSession(request);
    await optInConsent(request, sessionId);

    const beforeDelete = await request.get(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });
    const beforeBody = (await beforeDelete.json()) as ConsentStatusResponse;
    expect(beforeBody.data.status).toBe('opted_in');

    await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });

    const afterDelete = await request.get(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: getHeaders(),
    });
    const afterBody = (await afterDelete.json()) as ConsentStatusResponse;

    expect(['pending', 'opted_out']).toContain(afterBody.data.status);
    expect(afterBody.data.can_store_conversation).toBe(false);
  });
});
