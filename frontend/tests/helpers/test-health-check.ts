/**
 * Test Health Check Helpers
 * 
 * Prevention utilities from TEA Test Review (Story 5-10)
 * 
 * WHAT THIS PROVIDES:
 * - healthCheck: Pre-flight check to fail fast if backend is down
 * - safeCleanup: Safe session cleanup with error logging
 * - createSessionOrThrow: Create session that throws on failure (no silent skips)
 * 
 * @see _bmad-output/test-reviews/test-review-story-5-10-2026-02-21.md
 */

import { APIRequestContext } from '@playwright/test';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Pre-flight health check - fail fast if backend is down
 * Call in test.beforeAll() to prevent silent failures
 * 
 * @example
 * test.beforeAll(async ({ request }) => {
 *   await healthCheck(request);
 * });
 */
export async function healthCheck(request: APIRequestContext): Promise<void> {
  try {
    const response = await request.get(`${API_BASE}/health`, {
      timeout: 5000,
    });
    if (response.status() !== 200) {
      throw new Error(`Backend unhealthy: HTTP ${response.status()}`);
    }
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Backend health check failed: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Safe session cleanup with error logging
 * Use in test.afterEach() instead of raw request.delete()
 * 
 * @example
 * test.afterEach(async ({ request }) => {
 *   await safeCleanup(request, sessionId);
 * });
 */
export async function safeCleanup(
  request: APIRequestContext,
  sessionId: string | null
): Promise<void> {
  if (!sessionId) return;

  try {
    const response = await request.delete(
      `${API_BASE}/api/v1/widget/session/${sessionId}`,
      {
        timeout: 5000,
      }
    );
    if (!response.ok()) {
      console.warn(
        `[TEA] Cleanup warning: Session ${sessionId} deletion returned ${response.status()}`
      );
    }
  } catch (error) {
    console.warn(`[TEA] Cleanup error for session ${sessionId}:`, error);
  }
}

/**
 * Create session with explicit failure
 * Throws error instead of returning null to prevent silent skips
 * 
 * @example
 * test.beforeEach(async ({ request }) => {
 *   sessionId = await createSessionOrThrow(request);
 * });
 */
export async function createSessionOrThrow(
  request: APIRequestContext,
  merchantId: number = 1
): Promise<string> {
  const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
    data: { merchant_id: merchantId },
    headers: {
      'Content-Type': 'application/json',
      'X-Test-Mode': 'true',
    },
    timeout: 10000,
  });

  if (response.status() !== 200 && response.status() !== 201) {
    throw new Error(
      `Session creation failed: HTTP ${response.status()} - check backend health`
    );
  }

  const body = await response.json();
  const sessionId =
    body.data?.sessionId ||
    body.data?.session_id ||
    body.session?.session_id;

  if (!sessionId) {
    throw new Error(
      'Session creation succeeded but no session ID returned - API schema may have changed'
    );
  }

  return sessionId;
}

/**
 * Get widget headers with test mode flag
 */
export function getWidgetHeaders(testMode = true): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

/**
 * Create a unique test variant ID to avoid collisions
 */
export function createTestVariantId(prefix = 'test'): string {
  return `${prefix}-variant-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
