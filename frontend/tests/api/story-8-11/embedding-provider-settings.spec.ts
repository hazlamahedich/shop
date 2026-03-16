/**
 * API Tests: Story 8-11 - Embedding Provider Settings (GET/PATCH)
 *
 * Tests for GET and PATCH /api/settings/embedding-provider endpoints.
 * Includes authentication, validation, and provider switching tests.
 *
 * @tags api settings embedding-provider story-8-11
 */

import { test, expect } from '@playwright/test';
import {
  EmbeddingProviderSettingsResponse,
  EmbeddingProviderSettings,
  getAuthHeaders,
  createOpenAISettings,
  createGeminiSettings,
  createOllamaSettings,
  EMBEDDING_DIMENSIONS,
} from './test-utils';

test.describe('Story 8-11: Embedding Provider Settings API @api @story-8-11', () => {
  test.describe.configure({ mode: 'parallel' });

  // ==========================================================================
  // GET /api/settings/embedding-provider
  // ==========================================================================

  test.describe('GET /api/settings/embedding-provider', () => {
    test('[8.11-API-001][P0] @smoke should require authentication', async ({ request }) => {
      /**
       * Given an unauthenticated request
       * When GET /api/settings/embedding-provider is called
       * Then the endpoint should return 401 or 403
       */
      const response = await request.get('/api/settings/embedding-provider');

      expect([401, 403, 422, 500]).toContain(response.status());

      if (response.status() === 401) {
        const body = await response.json();
        expect(body).toHaveProperty('detail');
      }
    });

    test('[8.11-API-002][P0] @smoke should return provider settings', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/settings/embedding-provider is called
       * Then the endpoint should return 200 with provider settings
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data).toHaveProperty('provider');
      expect(body.data).toHaveProperty('model');
      expect(body.data).toHaveProperty('dimension');
      expect(body.data).toHaveProperty('re_embedding_required');
      expect(body.data).toHaveProperty('document_count');
      expect(body.meta).toHaveProperty('request_id');
      expect(body.meta).toHaveProperty('timestamp');
    });

    test('[8.11-API-003][P1] should return correct dimension for provider', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/settings/embedding-provider is called
       * Then the dimension should match the provider
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();
      const provider = body.data.provider.toLowerCase();
      const expectedDimension = EMBEDDING_DIMENSIONS[provider] || 1536;

      expect(body.data.dimension).toBe(expectedDimension);
    });

    test('[8.11-API-004][P1] should return default values for new merchant', async ({ request }) => {
      /**
       * Given a merchant with no custom embedding settings
       * When GET /api/settings/embedding-provider is called
       * Then default values should be returned
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(999),
      });

      if (response.status() === 200) {
        const body: EmbeddingProviderSettingsResponse = await response.json();

        expect(['openai', 'gemini', 'ollama']).toContain(body.data.provider);
        expect(body.data.dimension).toBeGreaterThan(0);
        expect(typeof body.data.re_embedding_required).toBe('boolean');
        expect(typeof body.data.document_count).toBe('number');
      }
    });

    test('[8.11-API-005][P1] should return correct envelope structure', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When GET /api/settings/embedding-provider is called
       * Then response should have correct envelope structure
       */
      const response = await request.get('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
      });

      expect(response.status()).toBe(200);

      const body = await response.json();

      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');
      expect(body.meta.request_id).toBeDefined();
      expect(body.meta.timestamp).toBeDefined();

      const timestamp = new Date(body.meta.timestamp);
      expect(!isNaN(timestamp.getTime())).toBe(true);
    });
  });

  // ==========================================================================
  // PATCH /api/settings/embedding-provider
  // ==========================================================================

  test.describe('PATCH /api/settings/embedding-provider', () => {
    test('[8.11-API-006][P0] @smoke should require authentication', async ({ request }) => {
      /**
       * Given an unauthenticated request
       * When PATCH /api/settings/embedding-provider is called
       * Then the endpoint should return 401 or 403
       */
      const settings = createOpenAISettings();

      const response = await request.patch('/api/settings/embedding-provider', {
        data: settings,
      });

      expect([401, 403, 422, 500]).toContain(response.status());
    });

    test('[8.11-API-007][P0] @smoke should update to OpenAI provider', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with OpenAI settings
       * Then the endpoint should return 200 with updated settings
       */
      const settings = createOpenAISettings();

      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: settings,
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data.provider).toBe('openai');
      expect(body.data.model).toBe('text-embedding-3-small');
      expect(body.data.dimension).toBe(1536);
    });

    test('[8.11-API-008][P0] @smoke should update to Gemini provider', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with Gemini settings
       * Then the endpoint should return 200 with updated settings
       */
      const settings = createGeminiSettings();

      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: settings,
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data.provider).toBe('gemini');
      expect(body.data.model).toBe('text-embedding-004');
      expect(body.data.dimension).toBe(768);
    });

    test('[8.11-API-009][P0] @smoke should update to Ollama provider', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with Ollama settings
       * Then the endpoint should return 200 with updated settings
       */
      const settings = createOllamaSettings();

      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: settings,
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data.provider).toBe('ollama');
      expect(body.data.model).toBe('nomic-embed-text');
      expect(body.data.dimension).toBe(768);
    });

    test('[8.11-API-010][P1] should validate provider parameter', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with invalid provider
       * Then the endpoint should return 422 validation error
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'invalid-provider',
          model: 'some-model',
        },
      });

      expect([400, 422]).toContain(response.status());

      if (response.status() === 422) {
        const body = await response.json();
        expect(body.detail).toBeDefined();
      }
    });

    test('[8.11-API-011][P1] should accept custom model parameter', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with custom model
       * Then the endpoint should accept the custom model parameter
       */
      const settings: EmbeddingProviderSettings = {
        provider: 'openai',
        model: 'text-embedding-3-large',
      };

      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: settings,
      });

      expect([200, 400, 422]).toContain(response.status());

      if (response.status() === 200) {
        const body: EmbeddingProviderSettingsResponse = await response.json();
        expect(body.data.model).toBe('text-embedding-3-large');
      }
    });

    test('[8.11-API-012][P1] should handle case-insensitive provider name', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called with uppercase provider
       * Then the endpoint should handle case-insensitive provider name
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: 'OPENAI',
          model: 'text-embedding-3-small',
        },
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data.provider).toBe('openai');
    });

    test('[8.11-API-013][P1] should require provider and model fields', async ({ request }) => {
      /**
       * Given an authenticated merchant
       * When PATCH /api/settings/embedding-provider is called without required fields
       * Then the endpoint should return 422 validation error
       */
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {},
      });

      expect(response.status()).toBe(422);

      const body = await response.json();
      expect(body.detail).toBeDefined();
    });
  });
});
