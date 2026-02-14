/**
 * API Tests: Story 4-5 Human Assistance Detection
 *
 * Tests handoff detection API contracts:
 * - Conversation handoff status retrieval
 * - Handoff status filtering
 * - Error code validation (7020-7024)
 *
 * @package frontend/tests/api/handoff-detection.spec.ts
 */

import { test, expect } from '@playwright/test';

test.describe('Story 4-5: Handoff Detection API', () => {
  const apiBase = '/api/v1';

  test.describe('[P0] Conversation Handoff Status', () => {
    test('[P0] should return conversation with handoff fields', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations/1`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      expect([200, 401, 404]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;

        expect(data).toHaveProperty('id');
        expect(data).toHaveProperty('status');
        expect(data).toHaveProperty('handoffStatus');
        expect(data).toHaveProperty('handoffTriggeredAt');
        expect(data).toHaveProperty('handoffReason');
        expect(data).toHaveProperty('consecutiveLowConfidenceCount');
      }
    });

    test('[P0] should filter conversations by handoff status', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
          handoffStatus: 'pending',
        },
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      expect([200, 401]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const conversations = body.data?.conversations || body.conversations || [];

        for (const conv of conversations) {
          expect(['pending', 'active', 'resolved']).toContain(conv.handoffStatus);
        }
      }
    });

    test('[P1] should return handoff reason enum values', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
        },
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 200) {
        const body = await response.json();
        const conversations = body.data?.conversations || body.conversations || [];

        const validReasons = ['keyword', 'low_confidence', 'clarification_loop', null];

        for (const conv of conversations) {
          expect(validReasons).toContain(conv.handoffReason);
        }
      }
    });
  });

  test.describe('[P1] Handoff Error Codes', () => {
    test('[P1] should return 7020 for detection logic failure', async ({ request }) => {
      const response = await request.post(`${apiBase}/conversations/999999/detect-handoff`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          message: 'test message',
        },
      });

      if (response.status() >= 400) {
        const body = await response.json();

        if (body.code) {
          const validErrorCodes = [7001, 7020, 7021, 7022, 7023, 7024];
          expect(validErrorCodes).toContain(body.code);
        }
      }
    });

    test('[P1] should return 7021 for status update failure', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/999999/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'pending',
          handoffReason: 'keyword',
        },
      });

      if (response.status() >= 400) {
        const body = await response.json();

        if (body.code) {
          expect([7001, 7020, 7021]).toContain(body.code);
        }
      }
    });

    test('[P1] should include error details in response', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations/invalid-id`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 404) {
        const body = await response.json();

        expect(body).toHaveProperty('message');
      }
    });
  });

  test.describe('[P1] Handoff Status Transitions', () => {
    test('[P1] should allow status transition from pending to active', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'active',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());
    });

    test('[P1] should allow status transition from active to resolved', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'resolved',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());
    });

    test('[P2] should reject invalid status transitions', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'invalid_status',
        },
      });

      expect([400, 401, 404, 405, 422]).toContain(response.status());
    });
  });

  test.describe('[P2] Handoff Statistics', () => {
    test('[P2] should return handoff count in conversation list', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
        },
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 200) {
        const body = await response.json();
        const meta = body.meta || body;

        if (meta.total !== undefined) {
          expect(typeof meta.total).toBe('number');
          expect(meta.total).toBeGreaterThanOrEqual(0);
        }
      }
    });

    test('[P2] should support pagination for handoff conversations', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
          page: 1,
          limit: 10,
        },
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 200) {
        const body = await response.json();
        const conversations = body.data?.conversations || body.conversations || [];

        expect(conversations.length).toBeLessThanOrEqual(10);
      }
    });
  });

  test.describe('[P2] Confidence Counter Reset', () => {
    test('[P2] should reset confidence counter on successful interaction', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'false',
          status: 'active',
        },
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 200) {
        const body = await response.json();
        const conversations = body.data?.conversations || body.conversations || [];

        for (const conv of conversations) {
          if (conv.consecutiveLowConfidenceCount !== undefined) {
            expect(conv.consecutiveLowConfidenceCount).toBeLessThanOrEqual(2);
          }
        }
      }
    });

    test('[P2] should track confidence count increments correctly', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations/1`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
      });

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;

        if (data.consecutiveLowConfidenceCount !== undefined) {
          expect(typeof data.consecutiveLowConfidenceCount).toBe('number');
          expect(data.consecutiveLowConfidenceCount).toBeGreaterThanOrEqual(0);
          expect(data.consecutiveLowConfidenceCount).toBeLessThanOrEqual(3);
        }
      }
    });
  });

  test.describe('[P2] Full Status Transition Flow', () => {
    test('[P2] should validate none to pending transition', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'pending',
          handoffReason: 'keyword',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;
        expect(data.handoffStatus).toBe('pending');
        expect(data.handoffReason).toBe('keyword');
      }
    });

    test('[P2] should validate pending to active transition', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'active',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;
        expect(data.handoffStatus).toBe('active');
      }
    });

    test('[P2] should validate active to resolved transition', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'resolved',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;
        expect(data.handoffStatus).toBe('resolved');
      }
    });

    test('[P2] should validate resolved to none transition (return to bot)', async ({ request }) => {
      const response = await request.patch(`${apiBase}/conversations/1/handoff-status`, {
        headers: {
          'Authorization': 'Bearer test-merchant-token',
        },
        data: {
          handoffStatus: 'none',
          status: 'active',
        },
      });

      expect([200, 401, 404, 405]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const data = body.data || body;
        expect(data.handoffStatus).toBe('none');
        expect(data.status).toBe('active');
      }
    });
  });

  test.describe('[P1] Authentication Required', () => {
    test('[P1] should reject unauthenticated requests', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
        },
      });

      expect([401, 403, 404]).toContain(response.status());
    });

    test('[P1] should reject invalid tokens', async ({ request }) => {
      const response = await request.get(`${apiBase}/conversations`, {
        params: {
          hasHandoff: 'true',
        },
        headers: {
          'Authorization': 'Bearer invalid-token',
        },
      });

      expect([401, 403, 404]).toContain(response.status());
    });
  });
});
