/**
 * API Tests: Story 8-11 - Provider Switching Workflow
 *
 * Tests for provider switching scenarios including dimension change detection
 * and re-embedding requirement flag management.
 *
 * @tags api workflow embedding-provider story-8-11
 */

import { test, expect } from '@playwright/test';
import {
  EmbeddingProvider,
  EmbeddingProviderSettingsResponse,
  getAuthHeaders,
  createOpenAISettings,
  createGeminiSettings,
  createOllamaSettings,
  EMBEDDING_MODELS,
  EMBEDDING_DIMENSIONS,
} from './test-utils';

test.describe.serial('Story 8-11: Provider Switching Workflow @api @story-8-11', () => {
  let originalProvider: string | undefined;

  test.beforeAll(async ({ request }) => {
    /**
     * Capture original provider settings for cleanup
     */
    const response = await request.get('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
    });

    if (response.status() === 200) {
      const body: EmbeddingProviderSettingsResponse = await response.json();
      originalProvider = body.data.provider;
    }
  });

  test.afterAll(async ({ request }) => {
    /**
     * Restore original provider settings after all tests
     */
    if (originalProvider) {
      await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider: originalProvider,
          model: EMBEDDING_MODELS[originalProvider] || 'text-embedding-3-small',
        },
      });
    }
  });

  // ==========================================================================
  // PROVIDER SWITCHING TESTS
  // ==========================================================================

  test('[8.11-API-024][P0] should switch from OpenAI to Gemini', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When switching from OpenAI to Gemini
     * Then the provider and dimension should update correctly
     */
    const openaiSettings = createOpenAISettings();

    const response = await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: openaiSettings,
    });

    expect(response.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await response.json();

    expect(body.data.provider).toBe('openai');
    expect(body.data.dimension).toBe(1536);
  });

  test('[8.11-API-025][P0] should switch from OpenAI to Gemini (dimension change)', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When switching from OpenAI (1536) to Gemini (768)
     * Then dimension should change from 1536 to 768
     */
    const geminiSettings = createGeminiSettings();

    const response = await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: geminiSettings,
    });

    expect(response.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await response.json();

    expect(body.data.provider).toBe('gemini');
    expect(body.data.dimension).toBe(768);
  });

  test('[8.11-API-026][P0] should switch from Gemini to Ollama (same dimension)', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When switching from Gemini (768) to Ollama (768)
     * Then dimension should stay at 768
     */
    const ollamaSettings = createOllamaSettings();

    const response = await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: ollamaSettings,
    });

    expect(response.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await response.json();

    expect(body.data.provider).toBe('ollama');
    expect(body.data.dimension).toBe(768);
  });

  test('[8.11-API-027][P1] should set re_embedding_required on dimension change', async ({ request }) => {
    /**
     * Given an authenticated merchant switching from OpenAI (1536) to Gemini (768)
     * When the dimension changes
     * Then re_embedding_required should be true
     */
    const openaiSettings = createOpenAISettings();

    await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: openaiSettings,
    });

    const geminiSettings = createGeminiSettings();

    const response = await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: geminiSettings,
    });

    expect(response.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await response.json();

    expect(body.data.re_embedding_required).toBe(true);
  });

  test('[8.11-API-028][P1] should not require re-embedding for same dimension', async ({ request }) => {
    /**
     * Given an authenticated merchant switching from Gemini to Ollama
     * When the dimension stays the same (768)
     * Then re_embedding_required should be false
     */
    const geminiSettings = createGeminiSettings();

    await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: geminiSettings,
    });

    const ollamaSettings = createOllamaSettings();

    const response = await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: ollamaSettings,
    });

    expect(response.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await response.json();

    expect(body.data.re_embedding_required).toBe(false);
  });

  test('[8.11-API-029][P1] should complete full provider switch cycle', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When switching through all providers
     * Then settings should persist correctly for each provider
     */
    const providers: EmbeddingProvider[] = ['openai', 'gemini', 'ollama'];

    for (const provider of providers) {
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider,
          model: EMBEDDING_MODELS[provider],
        },
      });

      expect(response.status()).toBe(200);

      const body: EmbeddingProviderSettingsResponse = await response.json();

      expect(body.data.provider).toBe(provider);
      expect(body.data.dimension).toBe(EMBEDDING_DIMENSIONS[provider]);
    }
  });

  test('[8.11-API-030][P1] should persist settings after GET', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When switching provider and then getting settings
     * Then GET should return the updated provider settings
     */
    const geminiSettings = createGeminiSettings();

    await request.patch('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
      data: geminiSettings,
    });

    const getResponse = await request.get('/api/settings/embedding-provider', {
      headers: getAuthHeaders(),
    });

    expect(getResponse.status()).toBe(200);

    const body: EmbeddingProviderSettingsResponse = await getResponse.json();

    expect(body.data.provider).toBe('gemini');
    expect(body.data.model).toBe('text-embedding-004');
    expect(body.data.dimension).toBe(768);
  });

  test('[8.11-API-031][P2] should handle rapid provider switches', async ({ request }) => {
    /**
     * Given an authenticated merchant
     * When rapidly switching between multiple providers
     * Then all switches should succeed without error
     */
    const providers: EmbeddingProvider[] = ['openai', 'gemini', 'ollama', 'openai', 'gemini'];

    for (const provider of providers) {
      const response = await request.patch('/api/settings/embedding-provider', {
        headers: getAuthHeaders(),
        data: {
          provider,
          model: EMBEDDING_MODELS[provider],
        },
      });

      expect(response.status()).toBe(200);
    }
  });
});
