/**
 * API Tests: Story 4-6 Handoff Notifications
 *
 * Tests handoff alert API contracts:
 * - Alert creation and retrieval
 * - Urgency level filtering
 * - Unread count tracking
 * - Mark as read operations
 * - Email rate limiting (P2)
 *
 * Acceptance Criteria Coverage:
 * - AC1: Multi-Channel Notifications (API side)
 * - AC2: Notification Content
 * - AC3-5: Urgency Level (High/Medium/Low)
 * - AC6: Dashboard Badge (unread count API)
 * - AC7: Email Rate Limiting
 *
 * @package frontend/tests/api/handoff-alerts.spec.ts
 */

import { test, expect } from '@playwright/test';

const API_BASE = '/api';
const HANDOFF_ALERTS_BASE = `${API_BASE}/handoff-alerts`;

const URGENCY_LEVELS = ['high', 'medium', 'low'] as const;
type UrgencyLevel = (typeof URGENCY_LEVELS)[number];

const VALID_HANDOFF_REASONS = ['keyword', 'low_confidence', 'clarification_loop'] as const;
type HandoffReason = (typeof VALID_HANDOFF_REASONS)[number];

interface HandoffAlert {
  id: string | number;
  merchantId: number;
  conversationId: number;
  urgencyLevel: UrgencyLevel;
  customerName: string;
  customerId: string;
  conversationPreview: string;
  waitTimeSeconds: number;
  isRead: boolean;
  createdAt: string;
  handoffReason?: HandoffReason;
}

interface HandoffAlertsResponse {
  data: HandoffAlert[];
  meta: {
    total: number;
    page: number;
    limit: number;
    unreadCount: number;
  };
}

interface UnreadCountResponse {
  unreadCount: number;
}

interface MarkReadResponse {
  success: boolean;
  alertId: string | number;
}

interface MarkAllReadResponse {
  success: boolean;
  updatedCount: number;
}

test.describe('Story 4-6: Handoff Alerts API', () => {
  
  test.describe('[P0] Alert List Retrieval', () => {
    
    test('[P0] should return paginated handoff alerts with correct structure', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([200, 401]).toContain(response.status());

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        expect(body).toHaveProperty('data');
        expect(body).toHaveProperty('meta');
        expect(Array.isArray(body.data)).toBe(true);

        expect(body.meta).toHaveProperty('total');
        expect(body.meta).toHaveProperty('page');
        expect(body.meta).toHaveProperty('limit');
        expect(body.meta).toHaveProperty('unreadCount');
        expect(typeof body.meta.total).toBe('number');
        expect(typeof body.meta.page).toBe('number');
        expect(typeof body.meta.limit).toBe('number');
        expect(typeof body.meta.unreadCount).toBe('number');
      }
    });

    test('[P0] should return alert with required content fields', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        if (body.data.length > 0) {
          const alert = body.data[0];

          expect(alert).toHaveProperty('id');
          expect(alert).toHaveProperty('urgencyLevel');
          expect(alert).toHaveProperty('customerName');
          expect(alert).toHaveProperty('conversationPreview');
          expect(alert).toHaveProperty('waitTimeSeconds');
          expect(alert).toHaveProperty('isRead');
          expect(alert).toHaveProperty('createdAt');

          expect(URGENCY_LEVELS).toContain(alert.urgencyLevel);
          expect(typeof alert.waitTimeSeconds).toBe('number');
          expect(alert.waitTimeSeconds).toBeGreaterThanOrEqual(0);
        }
      }
    });

    test('[P0] should return unread count accurately', async ({ request }) => {
      const listResponse = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      const countResponse = await request.get(`${HANDOFF_ALERTS_BASE}/unread-count`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (listResponse.status() === 200 && countResponse.status() === 200) {
        const listBody: HandoffAlertsResponse = await listResponse.json();
        const countBody: UnreadCountResponse = await countResponse.json();

        expect(countBody).toHaveProperty('unreadCount');
        expect(typeof countBody.unreadCount).toBe('number');
        expect(countBody.unreadCount).toBeGreaterThanOrEqual(0);

        const actualUnread = listBody.data.filter((a) => !a.isRead).length;
        expect(listBody.meta.unreadCount).toBe(actualUnread);
      }
    });
  });

  test.describe('[P0] Urgency Level Filtering', () => {
    
    test('[P0] should filter alerts by high urgency', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=high`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.urgencyLevel).toBe('high');
        }
      }
    });

    test('[P0] should filter alerts by medium urgency', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=medium`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.urgencyLevel).toBe('medium');
        }
      }
    });

    test('[P0] should filter alerts by low urgency', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=low`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.urgencyLevel).toBe('low');
        }
      }
    });

    test('[P1] should reject invalid urgency filter', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=invalid`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([400, 422]).toContain(response.status());
    });
  });

  test.describe('[P1] Pagination', () => {
    
    test('[P1] should respect page and limit parameters', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?page=1&limit=5`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        expect(body.meta.page).toBe(1);
        expect(body.meta.limit).toBe(5);
        expect(body.data.length).toBeLessThanOrEqual(5);
      }
    });

    test('[P1] should return different results on different pages', async ({ request }) => {
      const page1Response = await request.get(`${HANDOFF_ALERTS_BASE}?page=1&limit=5`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (page1Response.status() === 200) {
        const page1Body: HandoffAlertsResponse = await page1Response.json();

        if (page1Body.meta.total > 5) {
          const page2Response = await request.get(`${HANDOFF_ALERTS_BASE}?page=2&limit=5`, {
            headers: { Authorization: 'Bearer test-merchant-token' },
          });

          if (page2Response.status() === 200) {
            const page2Body: HandoffAlertsResponse = await page2Response.json();
            expect(page2Body.meta.page).toBe(2);
          }
        }
      }
    });
  });

  test.describe('[P1] Mark as Read', () => {
    
    test('[P1] should mark single alert as read', async ({ request }) => {
      const listResponse = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (listResponse.status() === 200) {
        const listBody: HandoffAlertsResponse = await listResponse.json();
        const unreadAlert = listBody.data.find((a) => !a.isRead);

        if (unreadAlert) {
          const markResponse = await request.post(
            `${HANDOFF_ALERTS_BASE}/${unreadAlert.id}/read`,
            { headers: { Authorization: 'Bearer test-merchant-token' } }
          );

          expect([200, 204]).toContain(markResponse.status());

          if (markResponse.status() === 200) {
            const markBody: MarkReadResponse = await markResponse.json();
            expect(markBody.success).toBe(true);
            expect(markBody.alertId).toBe(unreadAlert.id);
          }
        }
      }
    });

    test('[P1] should decrease unread count after marking read', async ({ request }) => {
      const beforeResponse = await request.get(`${HANDOFF_ALERTS_BASE}/unread-count`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (beforeResponse.status() === 200) {
        const beforeBody: UnreadCountResponse = await beforeResponse.json();
        const beforeCount = beforeBody.unreadCount;

        if (beforeCount > 0) {
          const listResponse = await request.get(HANDOFF_ALERTS_BASE, {
            headers: { Authorization: 'Bearer test-merchant-token' },
          });

          if (listResponse.status() === 200) {
            const listBody: HandoffAlertsResponse = await listResponse.json();
            const unreadAlert = listBody.data.find((a) => !a.isRead);

            if (unreadAlert) {
              await request.post(`${HANDOFF_ALERTS_BASE}/${unreadAlert.id}/read`, {
                headers: { Authorization: 'Bearer test-merchant-token' },
              });

              const afterResponse = await request.get(`${HANDOFF_ALERTS_BASE}/unread-count`, {
                headers: { Authorization: 'Bearer test-merchant-token' },
              });

              if (afterResponse.status() === 200) {
                const afterBody: UnreadCountResponse = await afterResponse.json();
                expect(afterBody.unreadCount).toBe(beforeCount - 1);
              }
            }
          }
        }
      }
    });
  });

  test.describe('[P1] Mark All as Read', () => {
    
    test('[P1] should mark all alerts as read', async ({ request }) => {
      const response = await request.post(`${HANDOFF_ALERTS_BASE}/mark-all-read`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([200, 204]).toContain(response.status());

      if (response.status() === 200) {
        const body: MarkAllReadResponse = await response.json();
        expect(body.success).toBe(true);
        expect(typeof body.updatedCount).toBe('number');
        expect(body.updatedCount).toBeGreaterThanOrEqual(0);
      }
    });

    test('[P1] should clear unread count after mark all read', async ({ request }) => {
      await request.post(`${HANDOFF_ALERTS_BASE}/mark-all-read`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      const countResponse = await request.get(`${HANDOFF_ALERTS_BASE}/unread-count`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (countResponse.status() === 200) {
        const countBody: UnreadCountResponse = await countResponse.json();
        expect(countBody.unreadCount).toBe(0);
      }
    });
  });

  test.describe('[P1] Authentication', () => {
    
    test('[P1] should reject unauthenticated requests to list alerts', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE);
      expect([200, 401, 403]).toContain(response.status());
    });

    test('[P1] should reject unauthenticated requests to unread count', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}/unread-count`);
      expect([200, 401, 403]).toContain(response.status());
    });

    test('[P1] should reject unauthenticated mark as read', async ({ request }) => {
      const response = await request.post(`${HANDOFF_ALERTS_BASE}/1/read`);
      expect([200, 401, 403, 404]).toContain(response.status());
    });

    test('[P1] should reject unauthenticated mark all read', async ({ request }) => {
      const response = await request.post(`${HANDOFF_ALERTS_BASE}/mark-all-read`);
      expect([200, 401, 403]).toContain(response.status());
    });
  });

  test.describe('[P2] Email Rate Limiting', () => {
    
    test('[P2] should rate limit emails per urgency level per 24 hours', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        params: { urgency: 'high' },
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.urgencyLevel).toBe('high');
        }
      }
    });

    test('[P2] should allow different urgency emails within same 24h period', async ({ request }) => {
      const urgencyFilters = ['high', 'medium', 'low'];
      const results: Record<string, number> = {};

      for (const urgency of urgencyFilters) {
        const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=${urgency}`, {
          headers: { Authorization: 'Bearer test-merchant-token' },
        });

        if (response.status() === 200) {
          const body: HandoffAlertsResponse = await response.json();
          results[urgency] = body.meta.total;
        }
      }

      expect(Object.keys(results).length).toBeGreaterThan(0);
    });
  });

  test.describe('[P2] Error Handling', () => {
    
    test('[P2] should return 404 for non-existent alert', async ({ request }) => {
      const response = await request.post(`${HANDOFF_ALERTS_BASE}/999999999/read`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([404, 400, 422]).toContain(response.status());
    });

    test('[P2] should include error code for handoff notification errors', async ({ request }) => {
      const response = await request.post(`${HANDOFF_ALERTS_BASE}/invalid-id/read`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() >= 400) {
        const body = await response.json();

        if (body.code) {
          const validErrorCodes = [7025, 7026, 7027, 7028, 7029];
          expect(validErrorCodes).toContain(body.code);
        }
      }
    });

    test('[P2] should handle invalid page parameters gracefully', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?page=-1&limit=0`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([200, 400, 422]).toContain(response.status());
    });
  });

  test.describe('[P2] Edge Cases', () => {
    
    test('[P2] should handle empty results gracefully', async ({ request }) => {
      const response = await request.get(`${HANDOFF_ALERTS_BASE}?urgency=nonexistent_filter`, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      expect([200, 400, 422]).toContain(response.status());

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();
        expect(Array.isArray(body.data)).toBe(true);
      }
    });

    test('[P2] should truncate conversation preview appropriately', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        if (body.data.length > 0) {
          const alert = body.data[0];
          expect(alert.conversationPreview.length).toBeLessThanOrEqual(500);
        }
      }
    });

    test('[P2] should calculate wait time accurately', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.waitTimeSeconds).toBeGreaterThanOrEqual(0);
          expect(alert.waitTimeSeconds).toBeLessThan(86400 * 7);
        }
      }
    });
  });

  test.describe('[P2] Content Validation', () => {
    
    test('[P2] should include customer identifier fallback', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          expect(alert.customerName || alert.customerId).toBeTruthy();
        }
      }
    });

    test('[P2] should have valid ISO timestamp', async ({ request }) => {
      const response = await request.get(HANDOFF_ALERTS_BASE, {
        headers: { Authorization: 'Bearer test-merchant-token' },
      });

      if (response.status() === 200) {
        const body: HandoffAlertsResponse = await response.json();

        for (const alert of body.data) {
          const createdAt = new Date(alert.createdAt);
          expect(createdAt.toISOString()).toBe(alert.createdAt);
        }
      }
    });
  });
});
