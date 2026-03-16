/**
 * Shared Test Utilities for Story 8-11 API Tests
 *
 * Common types, factories, and helpers used across all API test files.
 * This file should be imported by all test files in this directory.
 */

import { APIRequestContext } from '@playwright/test';
import { faker } from '@faker-js/faker';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export type EmbeddingProvider = 'openai' | 'gemini' | 'ollama';

export interface EmbeddingProviderSettings {
  provider: EmbeddingProvider;
  model: string;
}

export interface EmbeddingProviderSettingsData {
  provider: string;
  model: string;
  dimension: number;
  re_embedding_required: boolean;
  document_count: number;
}

export interface EmbeddingProviderSettingsResponse {
  data: EmbeddingProviderSettingsData;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

export interface ReembeddingStatusData {
  status_counts: {
    none: number;
    queued: number;
    in_progress: number;
    completed: number;
    failed: number;
  };
  total_documents: number;
  completed_documents: number;
  progress_percent: number;
}

export interface ReembeddingStatusResponse {
  data: ReembeddingStatusData;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

export interface ReembedTriggerResponse {
  data: {
    message: string;
    documentCount: number;
  };
  meta: {
    requestId: string;
    timestamp: string;
  };
}

// ============================================================================
// TEST CONFIGURATION
// ============================================================================

export const API_URL = process.env.API_URL || 'http://localhost:8000';
export const AUTH_TOKEN = process.env.TEST_AUTH_TOKEN || 'test-token';

export const EMBEDDING_PROVIDERS = {
  OPENAI: 'openai',
  GEMINI: 'gemini',
  OLLAMA: 'ollama',
} as const;

export const EMBEDDING_DIMENSIONS: Record<string, number> = {
  openai: 1536,
  gemini: 768,
  ollama: 768,
};

export const EMBEDDING_MODELS: Record<string, string> = {
  openai: 'text-embedding-3-small',
  gemini: 'text-embedding-004',
  ollama: 'nomic-embed-text',
};

// ============================================================================
// DATA FACTORIES
// ============================================================================

/**
 * Factory: Create embedding provider settings with random provider
 */
export function createEmbeddingProviderSettings(
  overrides: Partial<EmbeddingProviderSettings> = {}
): EmbeddingProviderSettings {
  const providers: EmbeddingProvider[] = ['openai', 'gemini', 'ollama'];
  const defaultProvider = faker.helpers.arrayElement(providers);

  return {
    provider: defaultProvider,
    model: EMBEDDING_MODELS[defaultProvider],
    ...overrides,
  };
}

/**
 * Factory: Create OpenAI settings
 */
export function createOpenAISettings(): EmbeddingProviderSettings {
  return {
    provider: 'openai',
    model: 'text-embedding-3-small',
  };
}

/**
 * Factory: Create Gemini settings
 */
export function createGeminiSettings(): EmbeddingProviderSettings {
  return {
    provider: 'gemini',
    model: 'text-embedding-004',
  };
}

/**
 * Factory: Create Ollama settings
 */
export function createOllamaSettings(): EmbeddingProviderSettings {
  return {
    provider: 'ollama',
    model: 'nomic-embed-text',
  };
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Helper: Get authenticated request headers
 */
export function getAuthHeaders(merchantId: number = 1): Record<string, string> {
  return {
    Authorization: `Bearer ${AUTH_TOKEN}`,
    'Content-Type': 'application/json',
    'X-Test-Mode': 'true',
    'X-Merchant-Id': String(merchantId),
  };
}

/**
 * Helper: Create authenticated API context
 */
export async function createAuthenticatedContext(
  playwright: any
): Promise<APIRequestContext> {
  return await playwright.request.newContext({
    baseURL: API_URL,
  });
}

/**
 * Helper: Dispose API context safely
 */
export async function disposeContext(context: APIRequestContext | undefined): Promise<void> {
  if (context) {
    await context.dispose();
  }
}
