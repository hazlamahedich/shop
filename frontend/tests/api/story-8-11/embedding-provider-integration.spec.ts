/**
 * API Tests: Story 8-11 - Integration and Performance Tests
 *
 * Tests for integration scenarios and performance benchmarks,
 * and cross-endpoint data consistency checks.
 *
 * @tags api integration performance embedding-provider story-8-11
 */

import { test, expect } from '@playwright/test';
import {
  EmbeddingProviderSettingsResponse
  ReembeddingStatusResponse
  getAuthHeaders
  createOpenAISettings
  createGeminiSettings
  EMBEDDING_MODELS
} from './test-utils';

test.describe('Story 8-11: Integration & Performance @api @story-8-11', () => {
  test.describe.configure({ mode: 'parallel' });

  // ==========================================================================
  // INTEGRATION TESTS
  // ==========================================================================

  test.describe('Integration Tests', () => {
    test('[8.11-API-048][P1] should switch provider and trigger re-embedding', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When switching provider and triggering re-embedding
       * Then both operations should complete successfully
       */
      const switchResponse = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: createGeminiSettings(),
      });

      expect(switchResponse.status()).toBe(200);

      const reembedResponse = await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(),
      });

      expect(reembedResponse.status()).toBe(200);
    });

    test('[8.11-API-047][P1] should trigger re-embedding and check status', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When triggering re-embedding and checking status
       * Then status should reflect the triggered re-embedding
       */
      await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(),
      });

      const statusResponse = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(),
      });

      expect(statusResponse.status()).toBe(200);

      const body: ReembeddingStatusResponse = await statusResponse.json();

      expect(body.data).toHaveProperty('status_counts');
      expect(body.data).toHaveProperty('progress_percent');
    });

    test('[8.11-API-048][P1] should get updated settings after switch', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When switching provider and getting settings
       * Then GET should return updated settings
       */
      await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'ollama',
          model: EMBEDDING_MODELS.ollama,
        },
      });

      const getResponse = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
      });

      expect(getResponse.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await getResponse.json();

      expect(body.data.provider).toBe('ollama');
      expect(body.data.model).toBe(EMBEDDING_MODELS.ollama);
    });

    test('[8.11-API-049][P2] should complete full embedding workflow', async ({ request }) => {
      /**
       * Given an authenticated merchant with documents
       * When completing full workflow (switch → trigger → check status)
       * Then all operations should succeed
       */
      const providers: EmbeddingProvider[] = ['openai', 'gemini'];

      for (const provider of providers) {
        const switchResponse = await request.patch('/api/settings/embedding-provider', {
          headers: getAuthHeaders(),
          data: {
            provider,
            model: EMBEDDING_MODELS[provider],
          },
        });
        expect(switchResponse.status()).toBe(200);

        const getResponse = await request.get('/api/settings/embedding-provider', {
          headers: getAuthHeaders(),
        });
        expect(getResponse.status()).toBe(200);

        const triggerResponse = await request.post('/api/knowledge-base/re-embed', {
          headers: getAuthHeaders(),
        });
        expect(triggerResponse.status()).toBe(200);

        const statusResponse = await request.get('/api/knowledge-base/re-embed/status', {
          headers: getAuthHeaders(),
        });
        expect(statusResponse.status()).toBe(200);
      }
    });
  });

  // ==========================================================================
  // PERFORMANCE TESTS
  // ==========================================================================

  test.describe('Performance Tests', () => {
    test('[8.11-API-050][P2] should respond within acceptable time for GET', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/settings/embedding-provider is called
       * Then response should be under 500ms
       */
      const start = Date.now();

      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
      });

      const duration = Date.now() - start;

      expect(response.status()).toBe(200);
      expect(duration).toBeLessThan(500);
    });

    test('[8.11-API-051][P2] should respond within acceptable time for PATCH', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called
       * Then response should be under 1000ms
       */
      const start = Date.now();

      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: createOpenAISettings(),
      });

      const duration = Date.now() - start;

      expect(response.status()).toBe(200);
      expect(duration).toBeLessThan(1000);
    });

    test('[8.11-API-052][P2] should respond within acceptable time for status', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/knowledge-base/re-embed/status is called
       * Then response should be under 500ms
       */
      const start = Date.now();

      const response = await request.get('/api/knowledge-base/re-embed/status', {
        headers: getAuthHeaders(),
      });

      const duration = Date.now() - start;

      expect(response.status()).toBe(200);
      expect(duration).toBeLessThan(500);
    });

    test('[8.11-API-053][P2] should respond within acceptable time for re-embed trigger', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When POST /api/knowledge-base/re-embed is called
       * Then response should be under 1000ms
       */
      const start = Date.now();

      const response = await request.post('/api/knowledge-base/re-embed', {
        headers: getAuthHeaders(),
      });

      const duration = Date.now() - start;

      expect(response.status()).toBe(200);
      expect(duration).toBeLessThan(1000);
    });
  });
});
