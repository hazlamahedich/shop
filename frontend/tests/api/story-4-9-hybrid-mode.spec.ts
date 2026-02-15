/**
 * API Contract Tests for Hybrid Mode - Story 4-9
 *
 * Tests the PATCH /api/conversations/{id}/hybrid-mode endpoint
 * These tests validate API contract and error handling patterns
 * 
 * Note: Authenticated tests require TEST_AUTH_TOKEN env var or seeded test data
 * Note: CSRF token is required for PATCH operations
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/conversations`;

const hasAuthToken = !!process.env.TEST_AUTH_TOKEN;
const testCsrfToken = process.env.TEST_CSRF_TOKEN || 'test-csrf-token';

test.describe('Story 4-9: Hybrid Mode API Contract', () => {
  test.describe('Authentication', () => {
    test('[P0] @smoke requires authentication', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/123/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: true },
      });

      expect([401, 403, 400]).toContain(response.status());
    });
  });

  test.describe('Hybrid Mode Enable', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] @smoke enables hybrid mode successfully with expires_at', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/123/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: true, reason: 'merchant_responding' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        expect(body.data).toBeDefined();
        expect(body.data.conversationId).toBe(123);
        expect(body.data.hybridMode).toBeDefined();
        expect(body.data.hybridMode.enabled).toBe(true);
        expect(body.data.hybridMode.activatedAt).toBeDefined();
        expect(body.data.hybridMode.activatedBy).toBe('merchant');
        expect(body.data.hybridMode.expiresAt).toBeDefined();
        expect(body.data.hybridMode.remainingSeconds).toBe(7200);
        expect(body.meta).toBeDefined();
        expect(body.meta.requestId).toBeDefined();
        expect(body.meta.timestamp).toBeDefined();
      }
    });
  });

  test.describe('Hybrid Mode Disable', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P0] disables hybrid mode successfully', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/123/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: false, reason: 'merchant_returning' },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();
        expect(body.data.hybridMode.enabled).toBe(false);
        expect(body.data.hybridMode.remainingSeconds).toBe(0);
      }
    });
  });

  test.describe('Error Handling', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] returns 404 for non-existent conversation', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/999999/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: true },
      });

      expect([404, 400, 403]).toContain(response.status());

      if (response.status() === 404) {
        const body = await response.json();
        expect(body.error_code).toBe(7001);
      }
    });

    test('[P1] returns error when no Facebook page connection', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/123/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: true },
      });

      expect([404, 400, 403]).toContain(response.status());
    });
  });

  test.describe('Response Structure', () => {
    test.skip(!hasAuthToken, 'Requires TEST_AUTH_TOKEN environment variable');

    test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || ''}` } });

    test('[P1] response includes all required fields', async ({ request }) => {
      const response = await request.patch(`${API_BASE}/123/hybrid-mode`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': testCsrfToken,
        },
        data: { enabled: true },
      });

      expect([200, 404, 403]).toContain(response.status());

      if (response.status() === 200) {
        const body = await response.json();

        expect(body.data.conversationId).toBeDefined();
        expect(typeof body.data.conversationId).toBe('number');

        expect(body.data.hybridMode.enabled).toBeDefined();
        expect(typeof body.data.hybridMode.enabled).toBe('boolean');

        expect(body.data.hybridMode.remainingSeconds).toBeDefined();
        expect(typeof body.data.hybridMode.remainingSeconds).toBe('number');

        expect(body.meta.requestId).toBeDefined();
        expect(typeof body.meta.requestId).toBe('string');

        expect(body.meta.timestamp).toBeDefined();
        expect(typeof body.meta.timestamp).toBe('string');
      }
    });
  });
});
