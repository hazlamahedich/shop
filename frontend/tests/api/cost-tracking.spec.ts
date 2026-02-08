/**
 * API Tests for Story 3-5: Cost Tracking
 *
 * Tests the cost tracking API service layer for:
 * - HTTP client methods
 * - Request formation and authentication
 * - Error handling
 * - URL parameter construction
 *
 * @package frontend/tests/api
 */

import { test, expect } from '@playwright/test';

// Mock fetch for testing
type FetchParams = Parameters<typeof fetch>;
type MockResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<any>;
};

// Test data
const mockConversationCost = {
  conversationId: 'test-conv-123',
  totalCostUsd: 0.0234,
  totalTokens: 4532,
  requestCount: 5,
  avgCostPerRequest: 0.00468,
  provider: 'openai',
  model: 'gpt-4o-mini',
  requests: [
    {
      id: 1,
      requestTimestamp: '2026-02-08T10:30:00Z',
      provider: 'openai',
      model: 'gpt-4o-mini',
      promptTokens: 250,
      completionTokens: 150,
      totalTokens: 400,
      inputCostUsd: 0.000375,
      outputCostUsd: 0.00009,
      totalCostUsd: 0.000465,
      processingTimeMs: 1250,
    },
  ],
};

const mockCostSummary = {
  totalCostUsd: 18.45,
  totalTokens: 2450000,
  requestCount: 847,
  avgCostPerRequest: 0.0218,
  topConversations: [
    {
      conversationId: 'fb-psid-456',
      totalCostUsd: 2.34,
      requestCount: 15,
    },
  ],
  costsByProvider: {
    openai: { costUsd: 12.50, requests: 500 },
    ollama: { costUsd: 0.00, requests: 347 },
  },
  dailyBreakdown: [
    {
      date: '2026-02-01',
      totalCostUsd: 5.23,
      requestCount: 234,
    },
  ],
};

test.describe('Cost Tracking API Tests', () => {
  let originalFetch: typeof fetch;

  test.beforeEach(() => {
    originalFetch = global.fetch;
  });

  test.afterEach(() => {
    global.fetch = originalFetch;
  });

  test.describe('[P1] getConversationCost', () => {
    test('[P1] should fetch conversation cost successfully', async () => {
      // Given: API returns successful response
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockConversationCost,
          meta: { requestId: 'cost-test-conv-123' },
        }),
      } as unknown as Response);

      // When: Fetching conversation cost
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should return conversation cost data
      const response = await costTrackingService.costTrackingService.getConversationCost('test-conv-123');

      expect(response.data).toEqual(mockConversationCost);
    });

    test('[P1] should include auth header in request', async () => {
      // Given: Auth token is available
      const mockToken = 'test-auth-token';
      localStorage.setItem('auth_token', mockToken);

      let capturedHeaders: Record<string, string> = {};
      global.fetch = jest.fn().mockImplementation((url: string, options?: RequestInit) => {
        capturedHeaders = options?.headers as Record<string, string>;
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            data: mockConversationCost,
            meta: { requestId: 'cost-test-conv-123' },
          }),
        }) as unknown as Response;
      });

      // When: Fetching conversation cost
      const { costTrackingService } = await import('../../src/services/costTracking');

      await costTrackingService.costTrackingService.getConversationCost('test-conv-123');

      // Then: Should include Authorization header
      expect(capturedHeaders['Authorization']).toBe(`Bearer ${mockToken}`);
    });

    test('[P2] should handle 404 not found error', async () => {
      // Given: API returns 404
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ message: 'Cost data not found' }),
      } as unknown as Response);

      // When: Fetching non-existent conversation
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should throw error with message
      await expect(
        costTrackingService.costTrackingService.getConversationCost('non-existent')
      ).rejects.toThrow('Cost data not found');
    });

    test('[P1] should handle network error', async () => {
      // Given: Network request fails
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

      // When: Fetching conversation cost
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should throw network error
      await expect(
        costTrackingService.costTrackingService.getConversationCost('test-conv-123')
      ).rejects.toThrow('Network error');
    });
  });

  test.describe('[P0] getCostSummary', () => {
    test('[P0] should fetch cost summary without filters', async () => {
      // Given: API returns summary data
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockCostSummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching cost summary without parameters
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should return summary data
      const response = await costTrackingService.costTrackingService.getCostSummary({});

      expect(response.data).toEqual(mockCostSummary);
    });

    test('[P0] should fetch cost summary with date range filters', async () => {
      // Given: API returns filtered summary data
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockCostSummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching cost summary with date parameters
      const { costTrackingService } = await import('../../src/services/costTracking');

      const params = { dateFrom: '2026-02-01', dateTo: '2026-02-28' };
      await costTrackingService.costTrackingService.getCostSummary(params);

      // Then: Should include query parameters in request
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('date_from=2026-02-01'),
        expect.any(Object) // options object
      );
    });

    test('[P2] should handle authentication failure', async () => {
      // Given: API returns 401 unauthorized
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ message: 'Authentication required' }),
      } as unknown as Response);

      // When: Fetching cost summary without auth
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should throw authentication error
      await expect(
        costTrackingService.costTrackingService.getCostSummary({})
      ).rejects.toThrow('Authentication required');
    });

    test('[P2] should handle empty summary response', async () => {
      // Given: API returns empty summary (no costs)
      const emptySummary = {
        totalCostUsd: 0,
        totalTokens: 0,
        requestCount: 0,
        avgCostPerRequest: 0,
        topConversations: [],
        costsByProvider: {},
        dailyBreakdown: [],
      };

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: emptySummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching cost summary for period with no costs
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should return empty summary
      const response = await costTrackingService.costTrackingService.getCostSummary({});

      expect(response.data.totalCostUsd).toBe(0);
      expect(response.data.requestCount).toBe(0);
    });
  });

  test.describe('[P2] URL Parameter Construction', () => {
    test('[P2] should build correct URL with both date parameters', async () => {
      // Given: API endpoint
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockCostSummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching with both date parameters
      const { costTrackingService } = await import('../../src/services/costTracking');

      await costTrackingService.costTrackingService.getCostSummary({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });

      // Then: URL should include both query parameters
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('date_from=2026-02-01'),
        expect.any(Object)
      );
    });

    test('[P2] should build correct URL with only dateFrom parameter', async () => {
      // Given: API endpoint
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockCostSummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching with only dateFrom
      const { costTrackingService } = await import('../../src/services/costTracking');

      await costTrackingService.costTrackingService.getCostSummary({
        dateFrom: '2026-02-01',
      });

      // Then: URL should include only date_from parameter
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('date_from=2026-02-01'),
        expect.any(Object)
      );
    });

    test('[P2] should build correct URL with no date parameters', async () => {
      // Given: API endpoint
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          data: mockCostSummary,
          meta: { requestId: 'cost-summary' },
        }),
      } as unknown as Response);

      // When: Fetching without date parameters
      const { costTrackingService } = await import('../../src/services/costTracking');

      await costTrackingService.costTrackingService.getCostSummary({});

      // Then: URL should be base endpoint without query string
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/costs/summary',
        expect.any(Object)
      );
    });
  });

  test.describe('[P2] Error Response Handling', () => {
    test('[P2] should handle structured error response', async () => {
      // Given: API returns structured error
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          error_code: 'LLM_INVALID_DATE_RANGE',
          details: { message: 'Invalid date format' },
        }),
      } as unknown as Response);

      // When: Fetching with invalid date format
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should throw error with details message
      await expect(
        costTrackingService.costTrackingService.getCostSummary({
          dateFrom: 'invalid-date',
        })
      ).rejects.toThrow('Invalid date format');
    });

    test('[P2] should handle unknown error response', async () => {
      // Given: API returns generic error
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Internal server error' }),
      } as unknown as Response);

      // When: Fetching cost summary
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Should throw error with message
      await expect(
        costTrackingService.costTrackingService.getCostSummary({})
      ).rejects.toThrow('Internal server error');
    });
  });
});
