/**
 * Story 6-2: Data Deletion API Test Helpers
 *
 * Shared utilities for testing the widget data deletion API.
 * Provides session creation, consent management, and cleanup functionality.
 *
 * @module story-6-2/helpers
 */

import { APIRequestContext } from '@playwright/test';

export const API_BASE = 'http://localhost:8000/api/v1';

/**
 * Response structure for successful deletion operations.
 *
 * @interface DeletionResponse
 */
export interface DeletionResponse {
  data: {
    success: boolean;
    clear_visitor_id?: boolean;
    deletion_summary?: {
      conversations_deleted: number;
      messages_deleted: number;
      redis_keys_cleared: number;
      audit_log_id?: number;
    };
  };
}

/**
 * Response structure for consent status queries.
 *
 * @interface ConsentStatusResponse
 */
export interface ConsentStatusResponse {
  data: {
    status: 'pending' | 'opted_in' | 'opted_out';
    can_store_conversation: boolean;
    consent_message_shown: boolean;
    visitor_id?: string;
  };
}

/**
 * Response structure for audit log queries.
 *
 * @interface AuditLogResponse
 */
export interface AuditLogResponse {
  data: {
    id: number;
    session_id: string;
    visitor_id?: string;
    merchant_id: number;
    conversations_deleted: number;
    messages_deleted: number;
    redis_keys_cleared: number;
    requested_at: string;
    completed_at?: string;
  };
}

/**
 * Response structure for error responses.
 *
 * @interface ErrorResponse
 */
export interface ErrorResponse {
  error_code: number;
  message: string;
  details?: Record<string, unknown>;
}

/**
 * Array tracking all created sessions for cleanup.
 * Cleared before each test and cleaned up after each test.
 *
 * @internal
 */
export const createdSessions: string[] = [];

/**
 * Creates a new widget session for testing.
 *
 * Automatically tracks the session for cleanup in afterEach hooks.
 * Uses X-Test-Mode header to indicate test traffic.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @returns Promise resolving to the session ID of the created session
 * @throws Error if session creation fails (non-200/201 response)
 *
 * @example
 * ```typescript
 * const sessionId = await createSession(request);
 * // Session is automatically tracked for cleanup
 * // Use sessionId for subsequent API calls
 * ```
 */
export async function createSession(request: APIRequestContext): Promise<string> {
  const response = await request.post(`${API_BASE}/widget/session`, {
    data: { merchant_id: 1 },
    headers: {
      'Content-Type': 'application/json',
      'X-Test-Mode': 'true',
    },
  });

  if (response.status() === 200 || response.status() === 201) {
    const body = await response.json();
    const sessionId = body.data?.sessionId || body.data?.session_id || body.session?.session_id;
    createdSessions.push(sessionId);
    return sessionId;
  }

  throw new Error(`Failed to create session: ${response.status()}`);
}

/**
 * Creates a new widget session with a specific visitor ID.
 *
 * Used for testing cross-platform deletion where multiple sessions
 * share the same visitor ID.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @param visitorId - The visitor ID to associate with the session
 * @returns Promise resolving to an object containing sessionId and visitorId
 * @throws Error if session creation fails (non-200/201 response)
 *
 * @example
 * ```typescript
 * const visitorId = 'test-visitor-123';
 * const { sessionId } = await createSessionWithVisitorId(request, visitorId);
 * ```
 */
export async function createSessionWithVisitorId(
  request: APIRequestContext,
  visitorId: string,
): Promise<{ sessionId: string; visitorId: string }> {
  const response = await request.post(`${API_BASE}/widget/session`, {
    data: { merchant_id: 1, visitor_id: visitorId },
    headers: {
      'Content-Type': 'application/json',
      'X-Test-Mode': 'true',
    },
  });

  if (response.status() === 200 || response.status() === 201) {
    const body = await response.json();
    const sessionId = body.data?.sessionId || body.data?.session_id || body.session?.session_id;
    createdSessions.push(sessionId);
    return { sessionId, visitorId };
  }

  throw new Error(`Failed to create session with visitor_id: ${response.status()}`);
}

/**
 * Opts in consent for a session, enabling conversation storage.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @param sessionId - The session ID to opt in consent for
 * @returns Promise that resolves when consent is opted in
 *
 * @example
 * ```typescript
 * const sessionId = await createSession(request);
 * await optInConsent(request, sessionId);
 * // Session now has consent to store conversations
 * ```
 */
export async function optInConsent(request: APIRequestContext, sessionId: string): Promise<void> {
  await request.post(`${API_BASE}/widget/consent`, {
    data: {
      session_id: sessionId,
      consent_granted: true,
      source: 'widget',
    },
    headers: getHeaders(),
  });
}

/**
 * Returns standard headers for API requests.
 *
 * Includes Content-Type and X-Test-Mode headers.
 *
 * @returns Object containing standard request headers
 *
 * @example
 * ```typescript
 * const response = await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
 *   headers: getHeaders(),
 * });
 * ```
 */
export function getHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': 'true',
  };
}

/**
 * Cleans up a session by deleting it.
 *
 * Used in afterEach hooks to ensure test isolation.
 * Silently handles errors since the session may already be deleted.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @param sessionId - The session ID to clean up
 * @returns Promise that resolves when cleanup is attempted
 *
 * @example
 * ```typescript
 * test.afterEach(async ({ request }) => {
 *   for (const sessionId of createdSessions) {
 *     await cleanupSession(request, sessionId);
 *   }
 * });
 * ```
 */
export async function cleanupSession(request: APIRequestContext, sessionId: string): Promise<void> {
  try {
    await request.delete(`${API_BASE}/widget/consent/${sessionId}`, {
      headers: { ...getHeaders(), 'X-Cleanup': 'true' },
    });
  } catch {
    // Session may already be deleted
  }
}

/**
 * Resets the rate limiter for testing.
 *
 * Should be called in beforeEach to ensure clean state.
 * Silently handles errors if the endpoint doesn't exist.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @returns Promise that resolves when reset is attempted
 *
 * @example
 * ```typescript
 * test.beforeEach(async ({ request }) => {
 *   createdSessions.length = 0;
 *   await resetRateLimiter(request);
 * });
 * ```
 */
export async function resetRateLimiter(request: APIRequestContext): Promise<void> {
  try {
    await request.post(`${API_BASE}/widget/test/reset-rate-limiter`, {
      headers: { 'X-Test-Mode': 'true' },
    });
  } catch {
    // Ignore if endpoint doesn't exist
  }
}

/**
 * Cleans up all tracked sessions.
 *
 * Iterates through createdSessions array and cleans up each session.
 * Clears the array after cleanup.
 *
 * @param request - Playwright APIRequestContext for making HTTP requests
 * @returns Promise that resolves when all sessions are cleaned up
 *
 * @example
 * ```typescript
 * test.afterEach(async ({ request }) => {
 *   await cleanupAllSessions(request);
 * });
 * ```
 */
export async function cleanupAllSessions(request: APIRequestContext): Promise<void> {
  for (const sessionId of createdSessions) {
    await cleanupSession(request, sessionId);
  }
  createdSessions.length = 0;
}
