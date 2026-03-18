/**
 * Tests for Business Info Service
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests business info and FAQ API service including:
 * - API call methods
 * - Request/response handling
 * - Error handling
 * - Type safety
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { businessInfoApi, BusinessInfoError, BusinessInfoErrorCode } from './businessInfo';

// Mock the API client
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from './api';

describe('BusinessInfo Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getBusinessInfo', () => {
    it('should fetch business info successfully', async () => {
      const mockData = {
        business_name: 'Test Business',
        business_description: 'Test Description',
        business_hours: '9-5',
      };

      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockData,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.getBusinessInfo();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/merchant/business-info');
      expect(result).toEqual(mockData);
    });

    it('should handle errors', async () => {
      const error = new Error('Network error');
      (error as any).status = 500;
      vi.mocked(apiClient.get).mockRejectedValue(error);

      await expect(businessInfoApi.getBusinessInfo()).rejects.toThrow(BusinessInfoError);
    });

    it('should handle error with status code', async () => {
      const error = new Error('Not found');
      (error as any).status = 404;
      vi.mocked(apiClient.get).mockRejectedValue(error);

      await expect(businessInfoApi.getBusinessInfo()).rejects.toThrow('Not found');
    });
  });

  describe('updateBusinessInfo', () => {
    it('should update business info successfully', async () => {
      const mockUpdate = {
        business_name: 'Updated Business',
        business_description: 'Updated Description',
      };
      const mockResponse = {
        business_name: 'Updated Business',
        business_description: 'Updated Description',
        business_hours: null,
      };

      vi.mocked(apiClient.put).mockResolvedValue({
        data: mockResponse,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.updateBusinessInfo(mockUpdate);

      expect(apiClient.put).toHaveBeenCalledWith('/api/v1/merchant/business-info', mockUpdate);
      expect(result).toEqual(mockResponse);
    });

    it('should handle update errors', async () => {
      const error = new Error('Update failed');
      (error as any).status = 400;
      (error as any).details = { error_code: BusinessInfoErrorCode.INVALID_BUSINESS_NAME };
      vi.mocked(apiClient.put).mockRejectedValue(error);

      await expect(businessInfoApi.updateBusinessInfo({ business_name: '' }))
        .rejects.toThrow(BusinessInfoError);
    });

    it('should extract error code from response', async () => {
      const error = new Error('Validation error');
      (error as any).status = 422;
      (error as any).details = { error_code: BusinessInfoErrorCode.BUSINESS_DESCRIPTION_TOO_LONG };
      vi.mocked(apiClient.put).mockRejectedValue(error);

      try {
        await businessInfoApi.updateBusinessInfo({ business_description: 'a'.repeat(600) });
        expect(true).toBe(false); // Should not reach here
      } catch (e) {
        expect(e).toBeInstanceOf(BusinessInfoError);
        expect((e as BusinessInfoError).code).toBe(BusinessInfoErrorCode.BUSINESS_DESCRIPTION_TOO_LONG);
      }
    });
  });

  describe('getFaqs', () => {
    it('should fetch all FAQs successfully', async () => {
      const mockFaqs = [
        {
          id: 1,
          question: 'Q1',
          answer: 'A1',
          keywords: 'test',
          orderIndex: 0,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ];

      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockFaqs,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.getFaqs();

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/merchant/faqs');
      expect(result).toEqual(mockFaqs);
    });

    it('should handle FAQ fetch errors', async () => {
      const error = new Error('Fetch failed');
      (error as any).status = 500;
      vi.mocked(apiClient.get).mockRejectedValue(error);

      await expect(businessInfoApi.getFaqs()).rejects.toThrow(BusinessInfoError);
    });
  });

  describe('createFaq', () => {
    it('should create FAQ successfully', async () => {
      const mockFaq = {
        question: 'Test Question',
        answer: 'Test Answer',
        keywords: 'test',
        order_index: 0,
      };

      const mockResponse = {
        id: 1,
        question: 'Test Question',
        answer: 'Test Answer',
        keywords: 'test',
        orderIndex: 0,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };

      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockResponse,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.createFaq(mockFaq);

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/merchant/faqs', mockFaq);
      expect(result).toEqual(mockResponse);
    });

    it('should handle create errors', async () => {
      const error = new Error('Question required');
      (error as any).status = 422;
      (error as any).details = { error_code: BusinessInfoErrorCode.QUESTION_REQUIRED };
      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(businessInfoApi.createFaq({ question: '', answer: '' }))
        .rejects.toThrow(BusinessInfoError);
    });

    it('should handle answer too long error', async () => {
      const error = new Error('Answer too long');
      (error as any).status = 422;
      (error as any).details = { error_code: BusinessInfoErrorCode.ANSWER_TOO_LONG };
      vi.mocked(apiClient.post).mockRejectedValue(error);

      try {
        await businessInfoApi.createFaq({
          question: 'Test',
          answer: 'a'.repeat(2000),
        });
        expect(true).toBe(false);
      } catch (e) {
        expect(e).toBeInstanceOf(BusinessInfoError);
        expect((e as BusinessInfoError).code).toBe(BusinessInfoErrorCode.ANSWER_TOO_LONG);
      }
    });
  });

  describe('updateFaq', () => {
    it('should update FAQ successfully', async () => {
      const mockUpdate = {
        question: 'Updated Question',
        answer: 'Updated Answer',
      };

      const mockResponse = {
        id: 1,
        question: 'Updated Question',
        answer: 'Updated Answer',
        keywords: null,
        orderIndex: 0,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };

      vi.mocked(apiClient.put).mockResolvedValue({
        data: mockResponse,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.updateFaq(1, mockUpdate);

      expect(apiClient.put).toHaveBeenCalledWith('/api/v1/merchant/faqs/1', mockUpdate);
      expect(result).toEqual(mockResponse);
    });

    it('should handle FAQ not found error', async () => {
      const error = new Error('FAQ not found');
      (error as any).status = 404;
      (error as any).details = { error_code: BusinessInfoErrorCode.FAQ_NOT_FOUND };
      vi.mocked(apiClient.put).mockRejectedValue(error);

      await expect(businessInfoApi.updateFaq(999, { question: 'Test' }))
        .rejects.toThrow(BusinessInfoError);
    });
  });

  describe('deleteFaq', () => {
    it('should delete FAQ successfully', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({
        data: { success: true },
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      await businessInfoApi.deleteFaq(1);

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/merchant/faqs/1');
    });

    it('should handle delete errors', async () => {
      const error = new Error('Delete failed');
      (error as any).status = 403;
      (error as any).details = { error_code: BusinessInfoErrorCode.FAQ_ACCESS_DENIED };
      vi.mocked(apiClient.delete).mockRejectedValue(error);

      await expect(businessInfoApi.deleteFaq(1)).rejects.toThrow(BusinessInfoError);
    });
  });

  describe('reorderFaqs', () => {
    it('should reorder FAQs successfully', async () => {
      const mockReordered = [
        {
          id: 2,
          question: 'Q2',
          answer: 'A2',
          keywords: null,
          orderIndex: 0,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
        {
          id: 1,
          question: 'Q1',
          answer: 'A1',
          keywords: null,
          orderIndex: 1,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ];

      vi.mocked(apiClient.put).mockResolvedValue({
        data: mockReordered,
        meta: { request_id: '123', timestamp: '2024-01-01T00:00:00Z' },
      });

      const result = await businessInfoApi.reorderFaqs([2, 1]);

      expect(apiClient.put).toHaveBeenCalledWith('/api/v1/merchant/faqs/reorder', {
        faq_ids: [2, 1],
      });
      expect(result).toEqual(mockReordered);
    });

    it('should handle reorder errors', async () => {
      const error = new Error('Reorder failed');
      (error as any).status = 404;
      vi.mocked(apiClient.put).mockRejectedValue(error);

      await expect(businessInfoApi.reorderFaqs([1, 2]))
        .rejects.toThrow(BusinessInfoError);
    });
  });

  describe('BusinessInfoError', () => {
    it('should create error with message', () => {
      const error = new BusinessInfoError('Test error');

      expect(error.message).toBe('Test error');
      expect(error.name).toBe('BusinessInfoError');
      expect(error.code).toBeUndefined();
      expect(error.status).toBeUndefined();
    });

    it('should create error with code and status', () => {
      const error = new BusinessInfoError(
        'Test error',
        BusinessInfoErrorCode.QUESTION_REQUIRED,
        422
      );

      expect(error.message).toBe('Test error');
      expect(error.code).toBe(BusinessInfoErrorCode.QUESTION_REQUIRED);
      expect(error.status).toBe(422);
    });

    it('should be instanceof Error', () => {
      const error = new BusinessInfoError('Test');

      expect(error instanceof Error).toBe(true);
      expect(error instanceof BusinessInfoError).toBe(true);
    });
  });
});
