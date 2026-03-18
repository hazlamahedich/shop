/**
 * Cost Tracking Service Tests
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { costTrackingService } from './costTracking';
import type { ConversationCost, CostSummary } from '../types/cost';

describe('Cost Tracking Service', () => {
  beforeEach(() => {
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    global.localStorage = localStorageMock as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getConversationCost', () => {
    it('should fetch conversation cost from API', async () => {
      const mockResponse: ConversationCost = {
        conversationId: 'conv-123',
        totalCostUsd: 0.0456,
        totalTokens: 1500,
        requestCount: 3,
        avgCostPerRequest: 0.0152,
        provider: 'openai',
        model: 'gpt-4o-mini',
        requests: [
          {
            id: 1,
            requestTimestamp: '2026-02-08T10:00:00Z',
            provider: 'openai',
            model: 'gpt-4o-mini',
            promptTokens: 500,
            completionTokens: 250,
            totalTokens: 750,
            inputCostUsd: 0.000075,
            outputCostUsd: 0.00015,
            totalCostUsd: 0.000225,
          },
          {
            id: 2,
            requestTimestamp: '2026-02-08T10:01:00Z',
            provider: 'openai',
            model: 'gpt-4o-mini',
            promptTokens: 400,
            completionTokens: 350,
            totalTokens: 750,
            inputCostUsd: 0.00006,
            outputCostUsd: 0.00021,
            totalCostUsd: 0.00027,
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: mockResponse,
          meta: { requestId: 'cost-conv-123' },
        }),
      });

      const result = await costTrackingService.getConversationCost('conv-123');

      expect(fetch).toHaveBeenCalledWith(
        '/api/costs/conversation/conv-123',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );

      expect(result.data).toEqual(mockResponse);
      expect(result.meta.requestId).toBe('cost-conv-123');
    });

    it('should include auth token if available', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('fake-jwt-token');

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            conversationId: 'conv-123',
            totalCostUsd: 0,
            totalTokens: 0,
            requestCount: 0,
            avgCostPerRequest: 0,
            provider: 'openai',
            model: 'gpt-4o-mini',
            requests: [],
          },
          meta: { requestId: 'test' },
        }),
      });

      await costTrackingService.getConversationCost('conv-123');

      expect(fetch).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer fake-jwt-token',
          }),
        })
      );
    });

    it('should handle API errors', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({
          message: 'Cost data not found',
          error_code: 'LLM_COST_NOT_FOUND',
        }),
      });

      await expect(
        costTrackingService.getConversationCost('non-existent')
      ).rejects.toThrow('Cost data not found');
    });

    it('should handle structured error responses', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({
          error_code: 'VALIDATION_ERROR',
          details: {
            message: 'Invalid conversation ID format',
          },
        }),
      });

      await expect(
        costTrackingService.getConversationCost('invalid-id')
      ).rejects.toThrow('Invalid conversation ID format');
    });

    it('should handle network errors', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

      await expect(
        costTrackingService.getConversationCost('conv-123')
      ).rejects.toThrow('Network error');
    });
  });

  describe('getCostSummary', () => {
    it('should fetch cost summary without parameters', async () => {
      const mockResponse: CostSummary = {
        totalCostUsd: 1.23,
        totalTokens: 50000,
        requestCount: 100,
        avgCostPerRequest: 0.0123,
        topConversations: [
          {
            conversationId: 'conv-1',
            totalCostUsd: 0.50,
            requestCount: 20,
          },
          {
            conversationId: 'conv-2',
            totalCostUsd: 0.35,
            requestCount: 15,
          },
        ],
        costsByProvider: {
          openai: { costUsd: 0.80, requests: 60 },
          ollama: { costUsd: 0.00, requests: 30 },
          anthropic: { costUsd: 0.43, requests: 10 },
        },
        dailyBreakdown: [
          {
            date: '2026-02-08',
            totalCostUsd: 0.65,
            requestCount: 55,
          },
          {
            date: '2026-02-07',
            totalCostUsd: 0.58,
            requestCount: 45,
          },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: mockResponse,
          meta: { requestId: 'cost-summary' },
        }),
      });

      const result = await costTrackingService.getCostSummary();

      expect(fetch).toHaveBeenCalledWith('/api/costs/summary', expect.anything());
      expect(result.data).toEqual(mockResponse);
    });

    it('should include date range parameters', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            totalCostUsd: 0,
            totalTokens: 0,
            requestCount: 0,
            avgCostPerRequest: 0,
            topConversations: [],
            costsByProvider: {},
            dailyBreakdown: [],
          },
          meta: { requestId: 'test' },
        }),
      });

      await costTrackingService.getCostSummary({
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
      });

      expect(fetch).toHaveBeenCalledWith(
        '/api/costs/summary?date_from=2026-02-01&date_to=2026-02-28',
        expect.anything()
      );
    });

    it('should handle only dateFrom parameter', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            totalCostUsd: 0,
            totalTokens: 0,
            requestCount: 0,
            avgCostPerRequest: 0,
            topConversations: [],
            costsByProvider: {},
            dailyBreakdown: [],
          },
          meta: { requestId: 'test' },
        }),
      });

      await costTrackingService.getCostSummary({
        dateFrom: '2026-02-01',
      });

      expect(fetch).toHaveBeenCalledWith(
        '/api/costs/summary?date_from=2026-02-01',
        expect.anything()
      );
    });

    it('should handle only dateTo parameter', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            totalCostUsd: 0,
            totalTokens: 0,
            requestCount: 0,
            avgCostPerRequest: 0,
            topConversations: [],
            costsByProvider: {},
            dailyBreakdown: [],
          },
          meta: { requestId: 'test' },
        }),
      });

      await costTrackingService.getCostSummary({
        dateTo: '2026-02-28',
      });

      expect(fetch).toHaveBeenCalledWith(
        '/api/costs/summary?date_to=2026-02-28',
        expect.anything()
      );
    });

    it('should handle API errors for summary', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({
          message: 'Authentication required',
          error_code: 'AUTH_FAILED',
        }),
      });

      await expect(
        costTrackingService.getCostSummary()
      ).rejects.toThrow('Authentication required');
    });
  });
});
