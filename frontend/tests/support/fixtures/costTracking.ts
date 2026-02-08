/**
 * Cost Tracking Fixtures
 *
 * Reusable test fixtures for cost tracking tests.
 * Provides mock API responses and test data with auto-cleanup.
 *
 * Usage:
 * ```ts
 * import { mockCostSummary, mockConversationCost } from '@/tests/support/fixtures/costTracking';
 * ```
 */

import type { ConversationCost, CostSummary, ApiEnvelope } from '@/types/cost';
import { createConversationCost, createCostSummary } from '@/tests/support/factories/costFactory';

/**
 * Mock API response envelope factory
 */
function createApiEnvelope<T>(data: T): ApiEnvelope<T> {
  return {
    data,
    meta: {
      requestId: `test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Mock conversation cost response
 * @param overrides - Optional overrides for default values
 * @returns Mock conversation cost API response
 */
export function mockConversationCostResponse(
  overrides: Partial<ConversationCost> = {}
): ApiEnvelope<ConversationCost> {
  const conversationCost = createConversationCost(overrides);
  return createApiEnvelope(conversationCost);
}

/**
 * Mock cost summary response
 * @param overrides - Optional overrides for default values
 * @returns Mock cost summary API response
 */
export function mockCostSummaryResponse(
  overrides: Partial<CostSummary> = {}
): ApiEnvelope<CostSummary> {
  const costSummary = createCostSummary(overrides);
  return createApiEnvelope(costSummary);
}

/**
 * Mock empty cost summary response (no data)
 * @returns Mock empty cost summary API response
 */
export function mockEmptyCostSummaryResponse(): ApiEnvelope<CostSummary> {
  return createApiEnvelope({
    totalCostUsd: 0,
    totalTokens: 0,
    requestCount: 0,
    avgCostPerRequest: 0,
    topConversations: [],
    costsByProvider: {},
    dailyBreakdown: [],
  });
}

/**
 * Mock API error response
 * @param statusCode - HTTP status code
 * @param message - Error message
 * @param errorCode - Optional error code
 * @returns Mock error response
 */
export function mockErrorResponse(
  statusCode: number,
  message: string,
  errorCode?: string
): { status: number; json: () => Promise<any> } {
  const body = errorCode
    ? { error_code: errorCode, details: { message } }
    : { message };

  return {
    status: statusCode,
    ok: false,
    json: async () => body,
  } as unknown as Response;
}

/**
 * Mock successful fetch response
 * @param data - Response data
 * @returns Mock fetch response
 */
export function mockSuccessResponse<T>(data: T): Response {
  return {
    ok: true,
    status: 200,
    json: async () => createApiEnvelope(data),
  } as unknown as Response;
}

/**
 * Pre-configured mock responses for common scenarios
 */
export const mockResponses = {
  /** Successful conversation cost response */
  conversationCost: mockConversationCostResponse(),

  /** Successful cost summary response */
  costSummary: mockCostSummaryResponse(),

  /** Empty cost summary (no data) */
  emptySummary: mockEmptyCostSummaryResponse(),

  /** Not found error (404) */
  notFound: mockErrorResponse(404, 'Cost data not found', 'LLM_COST_NOT_FOUND'),

  /** Authentication error (401) */
  unauthorized: mockErrorResponse(401, 'Authentication required', 'LLM_AUTH_REQUIRED'),

  /** Invalid date format error (400) */
  invalidDate: mockErrorResponse(
    400,
    'Invalid date format',
    'LLM_INVALID_DATE_RANGE'
  ),

  /** Internal server error (500) */
  serverError: mockErrorResponse(500, 'Internal server error'),

  /** Network error (for throw scenarios) */
  networkError: new Error('Network error'),
} as const;

/**
 * Mock fetch implementation for cost tracking service
 * @param response - Response to return
 * @returns Mock fetch function
 */
export function mockCostTrackingFetch(response: Response | Error) {
  if (response instanceof Error) {
    return jest.fn().mockRejectedValue(response);
  }
  return jest.fn().mockResolvedValue(response);
}

/**
 * Setup mock localStorage for auth token
 * @param token - Auth token to store
 */
export function mockAuthToken(token: string = 'test-auth-token') {
  localStorage.setItem('auth_token', token);
}

/**
 * Clear mock localStorage
 */
export function clearMockAuth() {
  localStorage.removeItem('auth_token');
  localStorage.clear();
}

/**
 * Type guard for API error responses
 */
export function isApiError(response: any): response is { error_code: string; details: { message: string } } {
  return response && typeof response === 'object' && 'error_code' in response;
}
