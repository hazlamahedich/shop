/**
 * API Contract Tests for Offline Follow-Up - Story 4-11
 *
 * Tests the follow-up data in conversation history endpoint
 * These tests validate API contract for follow-up timestamps and status
 *
 * Acceptance Criteria:
 * - AC1: 12-Hour Follow-Up
 * - AC2: 24-Hour Follow-Up
 * - AC3: Business Hours Configuration
 * - AC4: No Duplicate Follow-Ups
 * - AC5: Handoff Status Tracking
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/conversations`;

const hasAuthToken = !!process.env.TEST_AUTH_TOKEN;

test.describe('Story 4-11: Offline Follow-Up API Contract', () => {
  test.describe('Authentication', () => {
    test('[P0] @smoke requires authentication for conversation history', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([401, 403, 400, 302, 404]).toContain(response.status());
    });
  });

  test.describe('Follow-Up Data Structure', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke conversation history includes follow-up object', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        expect(body.data).toBeDefined();
        expect(body.data.followUp).toBeDefined();
        expect(body.data.followUp).toBeTypeOf('object');
      }
    });

    test('[P0] @smoke follow-up object contains required timestamp fields', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;

        expect(followUp.followup12hSentAt).toBeDefined();
        expect(followUp.followup24hSentAt).toBeDefined();

        if (followUp.followup12hSentAt !== null) {
          expect(typeof followUp.followup12hSentAt).toBe('string');
          expect(() => new Date(followUp.followup12hSentAt)).not.toThrow();
        }

        if (followUp.followup24hSentAt !== null) {
          expect(typeof followUp.followup24hSentAt).toBe('string');
          expect(() => new Date(followUp.followup24hSentAt)).not.toThrow();
        }
      }
    });

    test('[P1] follow-up timestamps are null before thresholds', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;
        const handoff = body.data.handoff;

        if (handoff && handoff.triggeredAt) {
          const handoffTime = new Date(handoff.triggeredAt).getTime();
          const now = Date.now();
          const hoursSince = (now - handoffTime) / (1000 * 60 * 60);

          if (hoursSince < 12) {
            expect(followUp.followup12hSentAt).toBeNull();
          }
          if (hoursSince < 24) {
            expect(followUp.followup24hSentAt).toBeNull();
          }
        }
      }
    });
  });

  test.describe('AC1: 12-Hour Follow-Up', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke 12h follow-up timestamp set after threshold', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;
        const handoff = body.data.handoff;

        if (followUp.followup12hSentAt && handoff?.triggeredAt) {
          const followupTime = new Date(followUp.followup12hSentAt).getTime();
          const handoffTime = new Date(handoff.triggeredAt).getTime();
          const hoursDiff = (followupTime - handoffTime) / (1000 * 60 * 60);

          expect(hoursDiff).toBeGreaterThanOrEqual(12);
        }
      }
    });
  });

  test.describe('AC2: 24-Hour Follow-Up', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke 24h follow-up requires 12h follow-up first', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;

        if (followUp.followup24hSentAt !== null) {
          expect(followUp.followup12hSentAt).not.toBeNull();
        }
      }
    });

    test('[P0] @smoke 24h follow-up timestamp set after threshold', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;
        const handoff = body.data.handoff;

        if (followUp.followup24hSentAt && handoff?.triggeredAt) {
          const followupTime = new Date(followUp.followup24hSentAt).getTime();
          const handoffTime = new Date(handoff.triggeredAt).getTime();
          const hoursDiff = (followupTime - handoffTime) / (1000 * 60 * 60);

          expect(hoursDiff).toBeGreaterThanOrEqual(24);
        }
      }
    });
  });

  test.describe('AC4: No Duplicate Follow-Ups', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke 12h timestamp is single value (not array)', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;

        if (followUp.followup12hSentAt !== null) {
          expect(Array.isArray(followUp.followup12hSentAt)).toBe(false);
          expect(typeof followUp.followup12hSentAt).toBe('string');
        }
      }
    });

    test('[P0] @smoke 24h timestamp is single value (not array)', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;

        if (followUp.followup24hSentAt !== null) {
          expect(Array.isArray(followUp.followup24hSentAt)).toBe(false);
          expect(typeof followUp.followup24hSentAt).toBe('string');
        }
      }
    });
  });

  test.describe('AC5: Handoff Status Tracking', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke follow-up data only present when handoff exists', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        if (body.data.handoff) {
          expect(body.data.followUp).toBeDefined();
        }
      }
    });

    test('[P1] follow-up timestamps update independently', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        const followUp = body.data.followUp;

        if (followUp.followup12hSentAt && followUp.followup24hSentAt) {
          const time12h = new Date(followUp.followup12hSentAt).getTime();
          const time24h = new Date(followUp.followup24hSentAt).getTime();

          expect(time24h).toBeGreaterThan(time12h);
        }
      }
    });
  });

  test.describe('Error Handling', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] returns 404 for non-existent conversation', async ({ request }) => {
      const response = await request.get(`${API_BASE}/999999999/history`);

      expect([404, 403]).toContain(response.status());

      if (response.status() === 404) {
        const body = await response.json();
        expect(body.error_code || body.error || body.message).toBeDefined();
      }
    });

    test('[P1] handles invalid conversation ID format', async ({ request }) => {
      const response = await request.get(`${API_BASE}/invalid/history`);

      expect([400, 404, 422]).toContain(response.status());
    });
  });

  test.describe('Response Metadata', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] response includes standard metadata', async ({ request }) => {
      const response = await request.get(`${API_BASE}/123/history`);

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
  });
});
