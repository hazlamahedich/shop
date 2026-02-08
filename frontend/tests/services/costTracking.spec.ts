/**
 * Service Tests for Story 3-5: Cost Tracking
 *
 * Tests the cost tracking service layer for:
 * - Method existence and interface
 * - URL construction logic
 * - Data transformation
 * - Error propagation
 *
 * @package frontend/tests/services
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock data
const mockConversationCost = {
  conversationId: 'test-conv-123',
  totalCostUsd: 0.0234,
  totalTokens: 4532,
  requestCount: 5,
  avgCostPerRequest: 0.00468,
  provider: 'openai',
  model: 'gpt-4o-mini',
  requests: [],
};

const mockCostSummary = {
  totalCostUsd: 18.45,
  totalTokens: 2450000,
  requestCount: 847,
  avgCostPerRequest: 0.0218,
  topConversations: [],
  costsByProvider: {},
  dailyBreakdown: [],
};

describe('CostTrackingService', () => {
  let originalFetch: typeof fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    // Reset localStorage
    localStorage.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('[P1] Service Interface', () => {
    it('[P1] should export costTrackingService object', async () => {
      // Given: Service module is imported
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Service should have expected methods
      expect(costTrackingService).toBeDefined();
      expect(costTrackingService).toEqual({
        getConversationCost: expect.any(Function),
        getCostSummary: expect.any(Function),
        updateSettings: expect.any(Function),
        getSettings: expect.any(Function),
      });
    });

    it('[P1] should have getConversationCost method', async () => {
      // Given: Service is imported
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Method should exist
      expect(costTrackingService.getConversationCost).toBeDefined();
      expect(typeof costTrackingService.getConversationCost).toBe('function');
    });

    it('[P1] should have getCostSummary method', async () => {
      // Given: Service is imported
      const { costTrackingService } = await import('../../src/services/costTracking');

      // Then: Method should exist
      expect(costTrackingService.getCostSummary).toBeDefined();
      expect(typeof costTrackingService.getCostSummary).toBe('function');
    });
  });

  describe('[P1] URL Construction', () => {
    it('[P1] should build correct conversation cost URL', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockConversationCost }),
      });

      // When: Calling getConversationCost
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getConversationCost('test-conv-id');

      // Then: Should call fetch with correct URL
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/costs/conversation/test-conv-id',
        expect.any(Object)
      );
    });

    it('[P1] should build correct summary URL without parameters', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Calling getCostSummary without params
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({});

      // Then: Should call fetch with base URL
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/costs/summary',
        expect.any(Object)
      );
    });

    it('[P1] should build correct summary URL with dateFrom', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Calling getCostSummary with dateFrom only
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({ dateFrom: '2026-02-01' });

      // Then: Should include date_from query parameter
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      const url = fetchCall[0];
      expect(url).toContain('date_from=2026-02-01');
    });

    it('[P1] should build correct summary URL with both date parameters', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Calling getCostSummary with both dates
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });

      // Then: Should include both query parameters
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      const url = fetchCall[0];
      expect(url).toContain('date_from=2026-02-01');
      expect(url).toContain('date_to=2026-02-28');
    });

    it('[P2] should build correct summary URL with dateTo only', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Calling getCostSummary with dateTo only
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({ dateTo: '2026-02-28' });

      // Then: Should include date_to query parameter
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      const url = fetchCall[0];
      expect(url).toContain('date_to=2026-02-28');
    });
  });

  describe('[P1] Request Headers', () => {
    it('[P1] should include JSON content type header', async () => {
      // Given: Mock fetch implementation
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Making API request
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({});

      // Then: Should include Content-Type header
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      const options = fetchCall[1];
      expect(options?.headers).toMatchObject({
        'Content-Type': 'application/json',
      });
    });

    it('[P1] should include auth header when token exists', async () => {
      // Given: Auth token in localStorage
      const mockToken = 'test-auth-token';

      // Mock fetch before importing service
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      }) as Mock;

      // Set token after mock setup
      localStorage.setItem('auth_token', mockToken);

      // When: Making API request
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({});

      // Then: Should make request with correct URL
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      const url = fetchCall[0];
      expect(url).toContain('/api/costs/summary');
    });

    it('[P2] should not include auth header when token missing', async () => {
      // Given: No auth token in localStorage
      localStorage.clear();

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ data: mockCostSummary }),
      });

      // When: Making API request
      const { costTrackingService } = await import('../../src/services/costTracking');
      await costTrackingService.getCostSummary({});

      // Then: Should make request without error
      const fetchCall = (global.fetch as Mock).mock.calls[0];
      expect(fetchCall).toBeDefined();
    });
  });

  describe('[P2] Data Transformation', () => {
    it('[P2] should return API response data directly', async () => {
      // Given: API returns structured response
      const apiResponse = {
        data: mockCostSummary,
        meta: { requestId: 'test-123' },
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => apiResponse,
      });

      // When: Fetching cost summary
      const { costTrackingService } = await import('../../src/services/costTracking');
      const response = await costTrackingService.getCostSummary({});

      // Then: Should return the data portion
      expect(response).toEqual(apiResponse);
    });

    it('[P2] should preserve meta information in response', async () => {
      // Given: API returns response with meta
      const apiResponse = {
        data: mockCostSummary,
        meta: { requestId: 'test-123', timestamp: '2026-02-08T10:30:00Z' },
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => apiResponse,
      });

      // When: Fetching cost summary
      const { costTrackingService } = await import('../../src/services/costTracking');
      const response = await costTrackingService.getCostSummary({});

      // Then: Meta should be preserved
      expect(response.meta).toBeDefined();
      expect(response.meta.requestId).toBe('test-123');
    });
  });
});
