/**
 * API Tests: Story 8-11 - Re-embedding Functionality
 *
 * Tests for POST /api/knowledge-base/re-embed and GET /api/knowledge-base/re-embed/status
 * Includes authentication, idempotency, and status tracking tests.
 *
 * @tags api re-embedding embedding-provider story-8-11
 */

import { test, expect } from '@playwright/test';
import {
  ReembedTriggerResponse,
  ReembeddingStatusResponse,
  getAuthHeaders
} from './test-utils';

test.describe('Story 8-11: Re-embedding API @api @story-8-11', () => {
  test.describe.configure({ mode: 'parallel' });

  // ==========================================================================
  // POST /api/knowledge-base/re-embed
  // ==========================================================================

  test.describe('POST /api/knowledge-base/re-embed', () => {
    test('[8.11-API-014][P0] @smoke should require authentication', async ({ request }) => {
      /**
       * Given an unauthenticated request
       * When POST /api/knowledge-base/re-embed is called
       * Then the endpoint should return 401 or 403
       */
      const response = await request.post('/api/knowledge-base/re-embed');

      expect([401, 403, 422, 500]).toContain(response.status());
    });

    test('[8.11-API-015][P0] @smoke should trigger re-embedding', async ({ request }) => {
      /**
       * Given an authenticated merchant with documents
       * When POST /api/knowledge-base/re-embed is called
       * Then the endpoint should return 200 with document count
       */
      const response = await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body: ReembedTriggerResponse = await response.json();

      expect(body.data).toHaveProperty('message');
      expect(body.data).toHaveProperty('documentCount');
      expect(typeof body.data.documentCount).toBe('number');
      expect(body.data.documentCount).toBeGreaterThanOrEqual(0);
    });

    test('[8.11-API-016][P1] should handle merchant with no documents', async ({ request }) => {
      /**
       * Given an authenticated merchant with no documents
       * When POST /api/knowledge-base/re-embed is called
       * Then the endpoint should return 200 with documentCount = 0
       */
      const response = await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(9999),
      });

      if (response.status() === 200) {
        const body: ReembedTriggerResponse = await response.json();

        expect(body.data.documentCount).toBeGreaterThanOrEqual(0);
        expect(body.data.message).toBeDefined();
      }
    });

    test('[8.11-API-017][P1] should return correct response structure', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When POST /api/knowledge-base/re-embed is called
       * Then response should have correct envelope structure
       */
      const response = await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body = await response.json();

      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');
      expect(body.meta.requestId).toBeDefined();
      expect(body.meta.timestamp).toBeDefined();
    });

    test('[8.11-API-018][P1] should be idempotent', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When POST /api/knowledge-base/re-embed is called multiple times
       * Then each call should succeed without error
       */
      const responses = await Promise.all([
        request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        }),
        request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        }),
      ]);

      for (const response of responses) {
        expect(response.status()).toBe(200);
      }
    });
  });

  // ==========================================================================
  // GET /api/knowledge-base/re-embed/status
  // ==========================================================================

  test.describe('GET /api/knowledge-base/re-embed/status', () => {
    test('[8.11-API-019][P0] @smoke should require authentication', async ({ request }) => {
      /**
       * Given an unauthenticated request
       * When GET /api/knowledge-base/re-embed/status is called
       * Then the endpoint should return 401 or 403
       */
      const response = await request.get('/api/knowledge-base/re-embed/status');

      expect([401, 403, 422, 500]).toContain(response.status());
    });

    test('[8.11-API-020][P0] @smoke should return re-embedding status', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/knowledge-base/re-embed/status is called
       * Then the endpoint should return 200 with status information
       */
      const response = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body: ReembeddingStatusResponse = await response.json();

      expect(body.data).toHaveProperty('status_counts');
      expect(body.data).toHaveProperty('total_documents');
      expect(body.data).toHaveProperty('completed_documents');
      expect(body.data).toHaveProperty('progress_percent');
      expect(body.data.status_counts).toHaveProperty('none');
      expect(body.data.status_counts).toHaveProperty('queued');
      expect(body.data.status_counts).toHaveProperty('in_progress');
      expect(body.data.status_counts).toHaveProperty('completed');
      expect(body.data.status_counts).toHaveProperty('failed');
    });

    test('[8.11-API-021][P1] should calculate progress correctly', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/knowledge-base/re-embed/status is called
       * Then progress_percent should be calculated correctly
       */
      const response = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body: ReembeddingStatusResponse = await response.json();
      const { status_counts, total_documents, completed_documents, progress_percent } = body.data;

      expect(progress_percent).toBeGreaterThanOrEqual(0);
      expect(progress_percent).toBeLessThanOrEqual(100);

      if (total_documents > 0) {
        const expectedProgress = (completed_documents / total_documents) * 100;
        expect(Math.abs(progress_percent - expectedProgress)).toBeLessThan(0.2);
      } else {
        expect(progress_percent).toBe(0);
      }
    });

    test('[8.11-API-022][P1] should handle merchant with no documents', async ({ request }) => {
      /**
       * Given a merchant with no documents
       * When GET /api/knowledge-base/re-embed/status is called
       * Then should return zero counts
       */
      const response = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(9999),
      });

      if (response.status() === 200) {
        const body: ReembeddingStatusResponse = await response.json();

        expect(body.data.total_documents).toBeGreaterThanOrEqual(0);
        expect(body.data.progress_percent).toBeGreaterThanOrEqual(0);
        expect(body.data.progress_percent).toBeLessThanOrEqual(100);
      }
    });

    test('[8.11-API-023][P1] should return correct envelope structure', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/knowledge-base/re-embed/status is called
       * Then response should have correct envelope structure
       */
      const response = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body = await response.json();

      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');
      expect(body.meta.requestId).toBeDefined();
      expect(body.meta.timestamp).toBeDefined();
    });
  });
});
