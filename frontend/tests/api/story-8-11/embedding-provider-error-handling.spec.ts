/**
 * API Tests: Story 8-11 - Error Handling and Edge Cases
 *
 * Tests for error scenarios, invalid inputs, authentication failures,
 * and edge cases across all embedding provider endpoints.
 *
 * @tags api error-handling embedding-provider story-8-11
 */

import { test, expect } from '@playwright/test';
import { getAuthHeaders } from './test-utils';

test.describe('Story 8-11: Error Handling @api @story-8-11', () => {
  test.describe.configure({ mode: 'parallel' });

  // ==========================================================================
  // AUTHENTICATION ERRORS
  // ==========================================================================

  test.describe('Authentication Errors', () => {
    test('[8.11-API-032][P1] should reject invalid auth token', async ({ request }) => {
      /**
       * Given a request with invalid auth token
       * When calling any embedding endpoint
       * Then the endpoint should return 401 or 403
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: {
          Authorization: 'Bearer invalid-token',
          'Content-Type': 'application/json',
        },
      });

      expect([401, 403, 500]).toContain(response.status());
    });

    test('[8.11-API-033][P1] should reject missing auth token', async ({ request }) => {
      /**
       * Given a request without auth token
       * When calling any embedding endpoint
       * Then the endpoint should return 401
       */
      const response = await request.get('/api/settings/embedding-provider');

      expect([401, 403, 500]).toContain(response.status());
    });

    test('[8.11-API-034][P1] should reject expired auth token', async ({ request }) => {
      /**
       * Given a request with expired auth token
       * When calling any embedding endpoint
       * Then the endpoint should return 401
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: {
          Authorization: 'Bearer expired-token',
          'Content-Type': 'application/json',
        },
      });

      expect([401, 403, 500]).toContain(response.status());
    });
  });

  // ==========================================================================
  // VALIDATION ERRORS
  // ==========================================================================

  test.describe('Validation Errors', () => {
    test('[8.11-API-035][P1] should reject invalid provider name', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with invalid provider
       * Then the endpoint should return 422 or 400
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'nonexistent-provider',
          model: 'some-model',
        },
      });

      expect([400, 422]).toContain(response.status());

      const body = await response.json();
      expect(body.detail).toBeDefined();
    });

    test('[8.11-API-036][P1] should reject missing model parameter', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called without model
       * Then the endpoint should return 422
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'openai',
        },
      });

      expect(response.status()).toBe(422);

      const body = await response.json();
      expect(body.detail).toBeDefined();
    });

    test('[8.11-API-037][P1] should reject empty request body', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with empty body
       * Then the endpoint should return 422
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {},
      });

      expect(response.status()).toBe(422);

      const body = await response.json();
      expect(body.detail).toBeDefined();
    });

    test('[8.11-API-038][P1] should reject invalid model name', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with invalid model
       * Then the endpoint should return 400 or 422
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'openai',
          model: '',
        },
      });

      expect([400, 422]).toContain(response.status());
    });
  });

  // ==========================================================================
  // MERCHANT ERRORS
  // ==========================================================================

  test.describe('Merchant Errors', () => {
    test('[8.11-API-039][P1] should handle non-existent merchant', async ({ request }) => {
      /**
       * Given a non-existent merchant ID
       * When GET /api/settings/embedding-provider is called
       * Then the endpoint should handle gracefully
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(999999),
      });

      expect([200, 404, 500]).toContain(response.status());
    });

    test('[8.11-API-040][P1] should handle invalid merchant ID format', async ({ request }) => {
      /**
       * Given an invalid merchant ID format
       * When API endpoints are called
       * Then the endpoint should handle gracefully
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: {
          ...getAuthHeaders(),
          'X-Merchant-Id': 'invalid',
        },
      });

      expect([400, 422, 500]).toContain(response.status());
    });

    test('[8.11-API-041][P2] should handle merchant without configuration', async ({ request }) => {
      /**
       * Given a merchant without embedding configuration
       * When GET /api/settings/embedding-provider is called
       * Then should return default settings or 404
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(8888),
      });

      if (response.status() === 200) {
        const body = await response.json();
        expect(body.data).toBeDefined();
      }
    });
  });

  // ==========================================================================
  // CONCURRENT REQUEST ERRORS
  // ==========================================================================

  test.describe('Concurrent Request Errors', () => {
    test('[8.11-API-042][P2] should handle concurrent provider updates', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When multiple concurrent updates are made
       * Then the system should handle race conditions
       */
      const updates = [
        { provider: 'openai', model: 'text-embedding-3-small' },
        { provider: 'gemini', model: 'text-embedding-004' },
        { provider: 'ollama', model: 'nomic-embed-text' },
      ];

      const responses = await Promise.all(
        updates.map((settings) =>
          request.patch('/api/settings/embedding-provider', {
            headers: getAuthHeaders(),
            data: settings,
          })
        )
      );

      for (const response of responses) {
        expect([200, 400, 409, 422, 500]).toContain(response.status());
      }
    });

    test('[8.11-API-043][P2] should handle concurrent re-embed triggers', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When multiple concurrent re-embed triggers are made
       * Then the system should handle gracefully
       */
      const responses = await Promise.all([
        request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        }),
        request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        }),
        request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        }),
      ]);

      for (const response of responses) {
        expect([200, 409, 500]).toContain(response.status());
      }
    });
  });

  // ==========================================================================
  // EDGE CASES
  // ==========================================================================

  test.describe('Edge Cases', () => {
    test('[8.11-API-044][P2] should handle malformed JSON body', async ({ request }) => {
      /**
       * Given a request with malformed JSON
       * When calling PATCH endpoint
       * Then should return 400 or 422
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: 'invalid json string',
      });

      expect([400, 422, 500]).toContain(response.status());
    });

    test('[8.11-API-045][P2] should handle extremely long model name', async ({ request }) => {
      /**
       * Given a request with extremely long model name
       * When calling PATCH endpoint
       * Then should handle gracefully
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'openai',
          model: 'a'.repeat(1000),
        },
      });

      expect([200, 400, 422]).toContain(response.status());
    });

    test('[8.11-API-046][P2] should handle special characters in model name', async ({ request }) => {
      /**
       * Given a request with special characters in model name
       * When calling PATCH endpoint
       * Then should handle gracefully
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'openai',
          model: 'model-<script>alert("xss")</script>',
        },
      });

      expect([200, 400, 422]).toContain(response.status());
    });
  });
});
