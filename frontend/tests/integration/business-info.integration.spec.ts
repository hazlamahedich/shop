/**
 * Business Info & FAQ Integration Tests
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Integration tests covering:
 * - Business info store integration with API
 * - FAQ store integration with API
 * - State persistence and synchronization
 * - Error handling and recovery
 * - Optimistic updates behavior
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useBusinessInfoStore } from '../../src/stores/businessInfoStore';

// Mock fetch for integration tests
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Business Info Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();

    // Reset store
    useBusinessInfoStore.getState().reset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Business info API integration', () => {
    it('should fetch and store business info', async () => {
      const mockResponse = {
        data: {
          businessName: "Alex's Athletic Gear",
          businessDescription: 'Premium athletic apparel and equipment for serious athletes.',
          businessHours: '9 AM - 6 PM PST, Mon-Sat',
        },
        meta: {
          requestId: 'req-123',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Fetch business info
      await act(async () => {
        await useBusinessInfoStore.getState().fetchBusinessInfo();
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.businessName).toBe("Alex's Athletic Gear");
      expect(state.businessDescription).toBe('Premium athletic apparel and equipment for serious athletes.');
      expect(state.businessHours).toBe('9 AM - 6 PM PST, Mon-Sat');
      expect(state.loadingState).toBe('success');
      expect(state.isDirty).toBe(false);
    });

    it('should update business info via API', async () => {
      const mockResponse = {
        data: {
          businessName: 'Updated Store Name',
          businessDescription: 'New description',
          businessHours: '8 AM - 8 PM PST',
        },
        meta: {
          requestId: 'req-456',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Update business info
      await act(async () => {
        await useBusinessInfoStore.getState().updateBusinessInfo({
          business_name: 'Updated Store Name',
          business_description: 'New description',
          business_hours: '8 AM - 8 PM PST',
        });
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.businessName).toBe('Updated Store Name');
      expect(state.businessDescription).toBe('New description');
      expect(state.businessHours).toBe('8 AM - 8 PM PST');
      expect(state.isDirty).toBe(false);
    });

    it('should handle partial updates correctly', async () => {
      // First, set initial state
      useBusinessInfoStore.setState({
        businessName: 'Original Name',
        businessDescription: 'Original Description',
        businessHours: '9 AM - 5 PM',
        isDirty: false,
      });

      const mockResponse = {
        data: {
          businessName: 'Original Name',
          businessDescription: 'Original Description',
          businessHours: '8 AM - 9 PM',
        },
        meta: {},
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Update only hours
      await act(async () => {
        await useBusinessInfoStore.getState().updateBusinessInfo({
          business_hours: '8 AM - 9 PM',
        });
      });

      const state = useBusinessInfoStore.getState();
      expect(state.businessName).toBe('Original Name'); // Unchanged
      expect(state.businessDescription).toBe('Original Description'); // Unchanged
      expect(state.businessHours).toBe('8 AM - 9 PM'); // Updated
    });

    it('should handle API errors gracefully', async () => {
      const apiError = new Error('Internal server error');
      (apiError as any).status = 500;
      (apiError as any).details = {
        error_code: 1000,
        message: 'Internal server error',
      };

      mockFetch.mockRejectedValueOnce(apiError);

      // Attempt to fetch
      await act(async () => {
        await expect(useBusinessInfoStore.getState().fetchBusinessInfo()).rejects.toThrow();
      });

      const state = useBusinessInfoStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBeTruthy();
    });
  });

  describe('Optimistic updates', () => {
    it('should set local state optimistically without API call', async () => {
      useBusinessInfoStore.setState({
        businessName: null,
        isDirty: false,
      });

      // Set business name locally
      act(() => {
        useBusinessInfoStore.getState().setBusinessName('  Test Store  ');
      });

      const state = useBusinessInfoStore.getState();
      expect(state.businessName).toBe('Test Store'); // Trimmed
      expect(state.isDirty).toBe(true);

      // No API call should have been made
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should set description optimistically', () => {
      useBusinessInfoStore.setState({
        businessDescription: null,
        isDirty: false,
      });

      act(() => {
        useBusinessInfoStore.getState().setBusinessDescription('New description');
      });

      const state = useBusinessInfoStore.getState();
      expect(state.businessDescription).toBe('New description');
      expect(state.isDirty).toBe(true);
    });

    it('should set hours optimistically', () => {
      useBusinessInfoStore.setState({
        businessHours: null,
        isDirty: false,
      });

      act(() => {
        useBusinessInfoStore.getState().setBusinessHours('9 AM - 5 PM');
      });

      const state = useBusinessInfoStore.getState();
      expect(state.businessHours).toBe('9 AM - 5 PM');
      expect(state.isDirty).toBe(true);
    });
  });

  describe('Unsaved changes detection', () => {
    it('should track unsaved changes', () => {
      useBusinessInfoStore.setState({ isDirty: false });

      act(() => {
        useBusinessInfoStore.getState().setBusinessName('Test');
      });

      expect(useBusinessInfoStore.getState().hasUnsavedChanges()).toBe(true);
    });

    it('should clear dirty flag after successful update', async () => {
      useBusinessInfoStore.setState({
        businessName: 'Test',
        isDirty: true,
      });

      const mockResponse = {
        data: {
          businessName: 'Test',
          businessDescription: null,
          businessHours: null,
        },
        meta: {},
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await act(async () => {
        await useBusinessInfoStore.getState().updateBusinessInfo({
          business_name: 'Test',
        });
      });

      expect(useBusinessInfoStore.getState().hasUnsavedChanges()).toBe(false);
    });

    it('should allow discarding changes', () => {
      useBusinessInfoStore.setState({
        businessName: 'Test',
        isDirty: true,
      });

      act(() => {
        useBusinessInfoStore.getState().discardChanges();
      });

      expect(useBusinessInfoStore.getState().hasUnsavedChanges()).toBe(false);
    });
  });
});

describe('FAQ Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();

    // Reset store
    useBusinessInfoStore.getState().reset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('FAQ API integration', () => {
    it('should fetch and store FAQ list', async () => {
      const mockResponse = {
        data: [
          {
            id: 1,
            question: 'What are your hours?',
            answer: '9 AM - 6 PM PST',
            keywords: 'hours,time',
            orderIndex: 0,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            question: 'Do you offer returns?',
            answer: 'Yes, within 30 days',
            keywords: 'returns,refund',
            orderIndex: 1,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
        meta: {
          requestId: 'req-789',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Fetch FAQs
      await act(async () => {
        await useBusinessInfoStore.getState().fetchFaqs();
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.faqs).toHaveLength(2);
      expect(state.faqs[0].question).toBe('What are your hours?');
      expect(state.faqs[1].question).toBe('Do you offer returns?');
      expect(state.faqsLoadingState).toBe('success');
    });

    it('should create new FAQ via API', async () => {
      const mockResponse = {
        data: {
          id: 1,
          question: 'What payment methods do you accept?',
          answer: 'Visa, MasterCard, and PayPal',
          keywords: 'payment,methods',
          orderIndex: 0,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
        meta: {
          requestId: 'req-101',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
      });

      // Create FAQ
      const result = await act(async () => {
        return await useBusinessInfoStore.getState().createFaq({
          question: 'What payment methods do you accept?',
          answer: 'Visa, MasterCard, and PayPal',
          keywords: 'payment,methods',
        });
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.faqs).toHaveLength(1);
      expect(state.faqs[0].question).toBe('What payment methods do you accept?');
      expect(state.faqsLoadingState).toBe('success');
    });

    it('should update FAQ via API', async () => {
      // Set initial FAQ
      useBusinessInfoStore.setState({
        faqs: [
          {
            id: 1,
            question: 'Original question?',
            answer: 'Original answer',
            keywords: null,
            orderIndex: 0,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
      });

      const mockResponse = {
        data: {
          id: 1,
          question: 'Updated question?',
          answer: 'Updated answer',
          keywords: 'test',
          orderIndex: 0,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T01:00:00Z',
        },
        meta: {
          requestId: 'req-202',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Update FAQ
      await act(async () => {
        await useBusinessInfoStore.getState().updateFaq(1, {
          question: 'Updated question?',
          answer: 'Updated answer',
          keywords: 'test',
        });
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.faqs[0].question).toBe('Updated question?');
      expect(state.faqs[0].answer).toBe('Updated answer');
      expect(state.faqs[0].keywords).toBe('test');
    });

    it('should delete FAQ via API', async () => {
      // Set initial FAQs
      useBusinessInfoStore.setState({
        faqs: [
          {
            id: 1,
            question: 'To be deleted?',
            answer: 'Will be deleted',
            keywords: null,
            orderIndex: 0,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            question: 'Keep this?',
            answer: 'Keep this',
            keywords: null,
            orderIndex: 1,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
      });

      // Mock successful delete response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({}),
      });

      // Delete FAQ
      await act(async () => {
        await useBusinessInfoStore.getState().deleteFaq(1);
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.faqs).toHaveLength(1);
      expect(state.faqs[0].id).toBe(2);
    });

    it('should reorder FAQs via API', async () => {
      // Set initial FAQs
      useBusinessInfoStore.setState({
        faqs: [
          {
            id: 1,
            question: 'First?',
            answer: 'First',
            keywords: null,
            orderIndex: 0,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            question: 'Second?',
            answer: 'Second',
            keywords: null,
            orderIndex: 1,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 3,
            question: 'Third?',
            answer: 'Third',
            keywords: null,
            orderIndex: 2,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
      });

      const mockResponse = {
        data: [
          {
            id: 3,
            question: 'Third?',
            answer: 'Third',
            keywords: null,
            orderIndex: 0,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 1,
            question: 'First?',
            answer: 'First',
            keywords: null,
            orderIndex: 1,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            question: 'Second?',
            answer: 'Second',
            keywords: null,
            orderIndex: 2,
            createdAt: '2024-01-01T00:00:00Z',
            updatedAt: '2024-01-01T00:00:00Z',
          },
        ],
        meta: {
          requestId: 'req-303',
          timestamp: '2024-01-01T00:00:00Z',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      // Reorder FAQs
      await act(async () => {
        await useBusinessInfoStore.getState().reorderFaqs([3, 1, 2]);
      });

      // Verify state is updated
      const state = useBusinessInfoStore.getState();
      expect(state.faqs[0].id).toBe(3);
      expect(state.faqs[1].id).toBe(1);
      expect(state.faqs[2].id).toBe(2);
      expect(state.faqs[0].orderIndex).toBe(0);
      expect(state.faqs[1].orderIndex).toBe(1);
      expect(state.faqs[2].orderIndex).toBe(2);
    });
  });

  describe('FAQ error handling', () => {
    it('should handle fetch errors gracefully', async () => {
      const apiError = new Error('Failed to fetch FAQs');
      (apiError as any).status = 500;
      (apiError as any).details = {
        error_code: 1000,
        message: 'Failed to fetch FAQs',
      };

      mockFetch.mockRejectedValueOnce(apiError);

      await act(async () => {
        await expect(useBusinessInfoStore.getState().fetchFaqs()).rejects.toThrow();
      });

      const state = useBusinessInfoStore.getState();
      expect(state.faqsLoadingState).toBe('error');
      expect(state.error).toBeTruthy();
    });

    it('should handle create errors gracefully', async () => {
      const apiError = new Error('Validation error');
      (apiError as any).status = 422;
      (apiError as any).details = {
        error_code: 3000,
        message: 'Validation error',
      };

      mockFetch.mockRejectedValueOnce(apiError);

      await act(async () => {
        await expect(
          useBusinessInfoStore.getState().createFaq({
            question: '',
            answer: '',
          })
        ).rejects.toThrow();
      });

      const state = useBusinessInfoStore.getState();
      expect(state.faqsLoadingState).toBe('error');
    });

    it('should clear error on clearError call', async () => {
      const apiError = new Error('Error');
      (apiError as any).status = 500;
      (apiError as any).details = {
        error_code: 1000,
        message: 'Error',
      };

      mockFetch.mockRejectedValueOnce(apiError);

      await act(async () => {
        await expect(useBusinessInfoStore.getState().fetchBusinessInfo()).rejects.toThrow();
      });

      expect(useBusinessInfoStore.getState().error).toBeTruthy();

      act(() => {
        useBusinessInfoStore.getState().clearError();
      });

      expect(useBusinessInfoStore.getState().error).toBeNull();
    });
  });
});
