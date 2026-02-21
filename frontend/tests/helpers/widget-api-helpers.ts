/**
 * Widget API Test Helpers
 *
 * Shared utilities for Story 5-10 API tests.
 * Provides common headers, session management, and constants.
 *
 * @see tests/helpers/widget-test-helpers.ts for E2E helpers
 */

import { APIRequestContext } from '@playwright/test';

export const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
export const TEST_MERCHANT_ID = 1;

export function getWidgetHeaders(testMode = true): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

export async function createTestSession(request: APIRequestContext): Promise<string | null> {
  const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
    data: { merchant_id: TEST_MERCHANT_ID },
    headers: getWidgetHeaders(),
  });

  if (response.status() === 200 || response.status() === 201) {
    const body = await response.json();
    return body.data?.sessionId || body.data?.session_id || body.session?.session_id;
  }
  console.warn(`[TEA] Session creation failed: ${response.status()}`);
  return null;
}

export async function cleanupSession(request: APIRequestContext, sessionId: string): Promise<void> {
  try {
    await request.delete(`${API_BASE}/api/v1/widget/session/${sessionId}`, {
      headers: getWidgetHeaders(),
    });
  } catch {
    // Ignore cleanup errors
  }
}
