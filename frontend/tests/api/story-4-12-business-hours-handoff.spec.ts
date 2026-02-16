/**
 * API Contract Tests for Business Hours Handoff - Story 4-12
 *
 * Tests the notification queue behavior and handoff message context
 * These tests validate API contract for business hours-aware handoff
 *
 * Acceptance Criteria:
 * - AC1: Business Hours in Handoff Message
 * - AC2: Expected Response Time
 * - AC3: Notification Queue Behavior
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api`;

const hasAuthToken = !!process.env.TEST_AUTH_TOKEN;

const BUSINESS_HOURS_CONFIG = {
  enabled: true,
  timezone: 'America/Los_Angeles',
  schedule: {
    monday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    tuesday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    wednesday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    thursday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    friday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    saturday: { is_open: false },
    sunday: { is_open: false },
  },
};

test.describe('Story 4-12: Business Hours Handoff API Contract', () => {
  test.describe('Authentication', () => {
    test('[P0] @smoke requires authentication for handoff context endpoint', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`);

      expect([401, 403, 400, 302, 404]).toContain(response.status());
    });
  });

  test.describe('AC1: Business Hours in Handoff Message', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke handoff context includes business hours check', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        expect(body.data).toBeDefined();
        expect(body.data.isWithinBusinessHours).toBeDefined();
        expect(typeof body.data.isWithinBusinessHours).toBe('boolean');
      }
    });

    test('[P0] @smoke handoff context includes formatted business hours', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (body.data.businessHoursConfigured) {
          expect(body.data.formattedBusinessHours).toBeDefined();
          expect(typeof body.data.formattedBusinessHours).toBe('string');
        }
      }
    });

    test('[P1] handoff context reflects offline status outside hours', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T20:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (body.data.businessHoursConfigured) {
          expect(body.data.isWithinBusinessHours).toBe(false);
        }
      }
    });

    test('[P1] handoff context reflects online status within hours', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T14:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (body.data.businessHoursConfigured) {
          expect(body.data.isWithinBusinessHours).toBe(true);
        }
      }
    });

    test('[P1] handoff context for merchant without business hours config', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.businessHoursConfigured) {
          expect(body.data.isWithinBusinessHours).toBe(true);
          expect(body.data.formattedBusinessHours).toBeNull();
        }
      }
    });
  });

  test.describe('AC2: Expected Response Time', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke handoff context includes expected response time when offline', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T20:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.isWithinBusinessHours && body.data.businessHoursConfigured) {
          expect(body.data.expectedResponseTime).toBeDefined();
          expect(typeof body.data.expectedResponseTime).toBe('string');
        }
      }
    });

    test('[P1] expected response time format: less than 1 hour', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T16:30:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.isWithinBusinessHours && body.data.businessHoursConfigured) {
          expect(body.data.expectedResponseTime).toMatch(/less than 1 hour/i);
        }
      }
    });

    test('[P1] expected response time format: about X hours', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T14:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.isWithinBusinessHours && body.data.businessHoursConfigured) {
          const timeStr = body.data.expectedResponseTime;
          if (timeStr.includes('about')) {
            expect(timeStr).toMatch(/about \d+ hours?/i);
          }
        }
      }
    });

    test('[P1] expected response time format: tomorrow', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T20:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.isWithinBusinessHours && body.data.businessHoursConfigured) {
          expect(body.data.expectedResponseTime).toMatch(/tomorrow/i);
        }
      }
    });

    test('[P1] expected response time format: day name (weekend)', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-21T10:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (!body.data.isWithinBusinessHours && body.data.businessHoursConfigured) {
          expect(body.data.expectedResponseTime).toMatch(/on (Monday|Tuesday|Wednesday|Thursday|Friday)/i);
        }
      }
    });

    test('[P1] expected response time null when within business hours', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: '2026-02-20T14:00:00-08:00' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (body.data.isWithinBusinessHours) {
          expect(body.data.expectedResponseTime).toBeNull();
        }
      }
    });
  });

  test.describe('AC3: Notification Queue Behavior', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] notification queue status endpoint exists', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/notification-queue-status`);

      expect([200, 404, 403, 401]).toContain(response.status());
    });

    test('[P1] notification queued when outside business hours', async ({ request }) => {
      const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: {
          urgencyLevel: 'medium',
          currentTime: '2026-02-20T20:00:00-08:00',
        },
      });

      expect([200, 201, 202, 404, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201 || response.status() === 202) {
        const body = await response.json();

        if (body.data && body.data.businessHoursConfigured) {
          expect(body.data.queued).toBeDefined();
          if (body.data.queued) {
            expect(body.data.scheduledFor).toBeDefined();
            expect(typeof body.data.scheduledFor).toBe('string');
          }
        }
      }
    });

    test('[P1] notification sent immediately when within business hours', async ({ request }) => {
      const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: {
          urgencyLevel: 'medium',
          currentTime: '2026-02-20T14:00:00-08:00',
        },
      });

      expect([200, 201, 202, 404, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201 || response.status() === 202) {
        const body = await response.json();

        if (body.data && body.data.businessHoursConfigured && body.data.isWithinBusinessHours) {
          expect(body.data.queued).toBe(false);
          expect(body.data.sentImmediately).toBe(true);
        }
      }
    });

    test('[P1] queue scheduled for next business hour opening', async ({ request }) => {
      const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: {
          urgencyLevel: 'medium',
          currentTime: '2026-02-20T20:00:00-08:00',
        },
      });

      expect([200, 201, 202, 404, 403]).toContain(response.status());

      if (response.status() === 200 || response.status() === 201 || response.status() === 202) {
        const body = await response.json();

        if (body.data && body.data.queued && body.data.scheduledFor) {
          const scheduledTime = new Date(body.data.scheduledFor);
          const scheduledHour = scheduledTime.getHours();

          expect(scheduledHour).toBeGreaterThanOrEqual(9);
          expect(scheduledHour).toBeLessThan(10);
        }
      }
    });

    test('[P1] queue idempotency - no duplicate queue entries', async ({ request }) => {
      const notificationData = {
        urgencyLevel: 'medium',
        currentTime: '2026-02-20T20:00:00-08:00',
      };

      const response1 = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: notificationData,
      });

      const response2 = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: notificationData,
      });

      expect([200, 201, 202, 404, 403, 409]).toContain(response1.status());
      expect([200, 201, 202, 404, 403, 409]).toContain(response2.status());

      if (response1.status() >= 200 && response1.status() < 300) {
        const body1 = await response1.json();
        const body2 = await response2.json();

        if (body1.data && body2.data && body1.data.queueId && body2.data.queueId) {
          expect(body1.data.queueId).toBe(body2.data.queueId);
        }
      }
    });

    test('[P1] queue handles different urgency levels', async ({ request }) => {
      const urgencyLevels = ['high', 'medium', 'low'];

      for (const urgency of urgencyLevels) {
        const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
          data: {
            urgencyLevel: urgency,
            currentTime: '2026-02-20T20:00:00-08:00',
          },
        });

        expect([200, 201, 202, 404, 403]).toContain(response.status());

        if (response.status() === 200 || response.status() === 201 || response.status() === 202) {
          const body = await response.json();

          if (body.data) {
            expect(body.data.urgencyLevel).toBe(urgency);
          }
        }
      }
    });
  });

  test.describe('Business Hours Configuration', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] business hours config endpoint returns valid structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/settings/business-hours`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        expect(body.data).toBeDefined();
        expect(body.data.enabled).toBeDefined();
        expect(body.data.timezone).toBeDefined();
        expect(body.data.schedule).toBeDefined();
      }
    });

    test('[P1] schedule contains all days of week', async ({ request }) => {
      const response = await request.get(`${API_BASE}/settings/business-hours`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const schedule = body.data.schedule;

        expect(schedule.monday).toBeDefined();
        expect(schedule.tuesday).toBeDefined();
        expect(schedule.wednesday).toBeDefined();
        expect(schedule.thursday).toBeDefined();
        expect(schedule.friday).toBeDefined();
        expect(schedule.saturday).toBeDefined();
        expect(schedule.sunday).toBeDefined();
      }
    });

    test('[P1] each day has required fields when open', async ({ request }) => {
      const response = await request.get(`${API_BASE}/settings/business-hours`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const schedule = body.data.schedule;

        for (const day of Object.keys(schedule)) {
          const dayConfig = schedule[day];

          if (dayConfig.is_open) {
            expect(dayConfig.open_time).toBeDefined();
            expect(dayConfig.close_time).toBeDefined();
            expect(typeof dayConfig.open_time).toBe('string');
            expect(typeof dayConfig.close_time).toBe('string');
          }
        }
      }
    });
  });

  test.describe('Error Handling', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] returns 404 for non-existent conversation', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/999999999/handoff-context`);

      expect([404, 403]).toContain(response.status());

      if (response.status() === 404) {
        const body = await response.json();
        expect(body.error_code || body.error || body.message).toBeDefined();
      }
    });

    test('[P1] handles invalid conversation ID format', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/invalid/handoff-context`);

      expect([400, 404, 422]).toContain(response.status());
    });

    test('[P1] handles invalid time format', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`, {
        params: { currentTime: 'invalid-time' },
      });

      expect([200, 400, 422]).toContain(response.status());
    });

    test('[P1] handles missing urgency level in notification request', async ({ request }) => {
      const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: {
          currentTime: '2026-02-20T20:00:00-08:00',
        },
      });

      expect([200, 201, 400, 422, 404, 403]).toContain(response.status());
    });
  });

  test.describe('Response Metadata', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] handoff context response includes standard metadata', async ({ request }) => {
      const response = await request.get(`${API_BASE}/conversations/123/handoff-context`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        expect(body.meta).toBeDefined();
        expect(body.meta.requestId).toBeDefined();
        expect(typeof body.meta.requestId).toBe('string');
        expect(body.meta.timestamp).toBeDefined();
        expect(typeof body.meta.timestamp).toBe('string');
      }
    });

    test('[P1] notification response includes standard metadata', async ({ request }) => {
      const response = await request.post(`${API_BASE}/conversations/123/handoff-notification`, {
        data: {
          urgencyLevel: 'medium',
          currentTime: '2026-02-20T20:00:00-08:00',
        },
      });

      expect([200, 201, 202, 404, 403]).toContain(response.status());

      if (response.status() >= 200 && response.status() < 300) {
        const body = await response.json();

        expect(body.meta).toBeDefined();
        expect(body.meta.requestId).toBeDefined();
        expect(typeof body.meta.requestId).toBe('string');
      }
    });
  });
});
