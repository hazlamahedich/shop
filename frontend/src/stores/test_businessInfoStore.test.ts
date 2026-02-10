/**
 * Tests for Business Info Store
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests business info and FAQ store functionality including:
 * - State management
 * - Business info CRUD operations
 * - FAQ CRUD operations
 * - Error handling
 * - Loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from 'react';
import { useBusinessInfoStore } from './businessInfoStore';
import * as businessInfoService from '../services/businessInfo';

// Mock the business info service
vi.mock('../services/businessInfo', () => ({
  businessInfoApi: {
    getBusinessInfo: vi.fn(),
    updateBusinessInfo: vi.fn(),
    getFaqs: vi.fn(),
    createFaq: vi.fn(),
    updateFaq: vi.fn(),
    deleteFaq: vi.fn(),
    reorderFaqs: vi.fn(),
  },
  BusinessInfoError: class extends Error {
    constructor(message: string, public code?: number, public status?: number) {
      super(message);
      this.name = 'BusinessInfoError';
    }
  },
}));

describe('BusinessInfoStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useBusinessInfoStore.getState().reset();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useBusinessInfoStore.getState();

      expect(state.businessName).toBeNull();
      expect(state.businessDescription).toBeNull();
      expect(state.businessHours).toBeNull();
      expect(state.faqs).toEqual([]);
      expect(state.loadingState).toBe('idle');
      expect(state.faqsLoadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });
  });

  describe('Business Info Operations', () => {
    describe('fetchBusinessInfo', () => {
      it('should fetch and set business info', async () => {
        const mockData = {
          business_name: 'Test Business',
          business_description: 'Test Description',
          business_hours: '9-5',
        };
        vi.mocked(businessInfoService.businessInfoApi.getBusinessInfo).mockResolvedValue(mockData);

        await act(async () => {
          await useBusinessInfoStore.getState().fetchBusinessInfo();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.businessName).toBe('Test Business');
        expect(state.businessDescription).toBe('Test Description');
        expect(state.businessHours).toBe('9-5');
        expect(state.loadingState).toBe('success');
        expect(state.isDirty).toBe(false);
      });

      it('should handle fetch errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.getBusinessInfo).mockRejectedValue(
          new Error('Network error')
        );

        await act(async () => {
          await expect(
            useBusinessInfoStore.getState().fetchBusinessInfo()
          ).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.loadingState).toBe('error');
        expect(state.error).toBe('Network error');
      });
    });

    describe('updateBusinessInfo', () => {
      it('should update business info', async () => {
        const mockData = {
          business_name: 'Updated Business',
          business_description: 'Updated Description',
          business_hours: '10-6',
        };
        vi.mocked(businessInfoService.businessInfoApi.updateBusinessInfo).mockResolvedValue(mockData);

        await act(async () => {
          await useBusinessInfoStore.getState().updateBusinessInfo({
            business_name: 'Updated Business',
            business_description: 'Updated Description',
            business_hours: '10-6',
          });
        });

        const state = useBusinessInfoStore.getState();
        expect(state.businessName).toBe('Updated Business');
        expect(state.businessDescription).toBe('Updated Description');
        expect(state.businessHours).toBe('10-6');
        expect(state.loadingState).toBe('success');
        expect(state.isDirty).toBe(false);
      });

      it('should handle update errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.updateBusinessInfo).mockRejectedValue(
          new Error('Update failed')
        );

        await act(async () => {
          await expect(
            useBusinessInfoStore.getState().updateBusinessInfo({ business_name: 'Test' })
          ).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.loadingState).toBe('error');
        expect(state.error).toBe('Update failed');
      });
    });

    describe('Local state setters', () => {
      it('should set business name locally', () => {
        act(() => {
          useBusinessInfoStore.getState().setBusinessName('Local Business');
        });

        const state = useBusinessInfoStore.getState();
        expect(state.businessName).toBe('Local Business');
        expect(state.isDirty).toBe(true);
      });

      it('should trim whitespace from business name', () => {
        act(() => {
          useBusinessInfoStore.getState().setBusinessName('  Test  ');
        });

        expect(useBusinessInfoStore.getState().businessName).toBe('Test');
      });

      it('should set to null if empty string', () => {
        act(() => {
          useBusinessInfoStore.getState().setBusinessName('   ');
        });

        expect(useBusinessInfoStore.getState().businessName).toBeNull();
      });

      it('should set business description locally', () => {
        act(() => {
          useBusinessInfoStore.getState().setBusinessDescription('Local Description');
        });

        const state = useBusinessInfoStore.getState();
        expect(state.businessDescription).toBe('Local Description');
        expect(state.isDirty).toBe(true);
      });

      it('should set business hours locally', () => {
        act(() => {
          useBusinessInfoStore.getState().setBusinessHours('9-5');
        });

        const state = useBusinessInfoStore.getState();
        expect(state.businessHours).toBe('9-5');
        expect(state.isDirty).toBe(true);
      });
    });
  });

  describe('FAQ Operations', () => {
    const mockFaqResponse = {
      id: 1,
      question: 'Test Question',
      answer: 'Test Answer',
      keywords: 'test',
      orderIndex: 0,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    };

    describe('fetchFaqs', () => {
      it('should fetch and set FAQs', async () => {
        const mockFaqs = [mockFaqResponse, { ...mockFaqResponse, id: 2 }];
        vi.mocked(businessInfoService.businessInfoApi.getFaqs).mockResolvedValue(mockFaqs);

        await act(async () => {
          await useBusinessInfoStore.getState().fetchFaqs();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqs).toHaveLength(2);
        expect(state.faqsLoadingState).toBe('success');
      });

      it('should handle fetch errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.getFaqs).mockRejectedValue(
          new Error('Fetch failed')
        );

        await act(async () => {
          await expect(useBusinessInfoStore.getState().fetchFaqs()).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqsLoadingState).toBe('error');
        expect(state.error).toBe('Fetch failed');
      });
    });

    describe('createFaq', () => {
      it('should create and add FAQ', async () => {
        vi.mocked(businessInfoService.businessInfoApi.createFaq).mockResolvedValue(mockFaqResponse);

        let result;
        await act(async () => {
          result = await useBusinessInfoStore.getState().createFaq({
            question: 'Test Question',
            answer: 'Test Answer',
            keywords: 'test',
          });
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqs).toHaveLength(1);
        expect(state.faqs[0].question).toBe('Test Question');
        expect(state.faqsLoadingState).toBe('success');
        expect(result).toEqual(mockFaqResponse);
      });

      it('should handle create errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.createFaq).mockRejectedValue(
          new Error('Create failed')
        );

        await act(async () => {
          await expect(
            useBusinessInfoStore.getState().createFaq({
              question: 'Test',
              answer: 'Test',
            })
          ).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqsLoadingState).toBe('error');
      });
    });

    describe('updateFaq', () => {
      it('should update existing FAQ', async () => {
        const updatedFaq = { ...mockFaqResponse, question: 'Updated Question' };
        vi.mocked(businessInfoService.businessInfoApi.updateFaq).mockResolvedValue(updatedFaq);

        // First add an FAQ
        useBusinessInfoStore.setState({ faqs: [mockFaqResponse] });

        await act(async () => {
          await useBusinessInfoStore.getState().updateFaq(1, { question: 'Updated Question' });
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqs[0].question).toBe('Updated Question');
        expect(state.faqsLoadingState).toBe('success');
      });

      it('should handle update errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.updateFaq).mockRejectedValue(
          new Error('Update failed')
        );

        useBusinessInfoStore.setState({ faqs: [mockFaqResponse] });

        await act(async () => {
          await expect(
            useBusinessInfoStore.getState().updateFaq(1, { question: 'Test' })
          ).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqsLoadingState).toBe('error');
      });
    });

    describe('deleteFaq', () => {
      it('should delete FAQ', async () => {
        vi.mocked(businessInfoService.businessInfoApi.deleteFaq).mockResolvedValue(undefined);

        useBusinessInfoStore.setState({ faqs: [mockFaqResponse] });

        await act(async () => {
          await useBusinessInfoStore.getState().deleteFaq(1);
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqs).toHaveLength(0);
        expect(state.faqsLoadingState).toBe('success');
      });

      it('should handle delete errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.deleteFaq).mockRejectedValue(
          new Error('Delete failed')
        );

        useBusinessInfoStore.setState({ faqs: [mockFaqResponse] });

        await act(async () => {
          await expect(useBusinessInfoStore.getState().deleteFaq(1)).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqsLoadingState).toBe('error');
      });
    });

    describe('reorderFaqs', () => {
      it('should reorder FAQs', async () => {
        const faq1 = { ...mockFaqResponse, id: 1, orderIndex: 0 };
        const faq2 = { ...mockFaqResponse, id: 2, orderIndex: 1 };

        // Reorder: swap positions
        const reordered = [
          { ...faq2, orderIndex: 0 },
          { ...faq1, orderIndex: 1 },
        ];

        vi.mocked(businessInfoService.businessInfoApi.reorderFaqs).mockResolvedValue(reordered);

        useBusinessInfoStore.setState({ faqs: [faq1, faq2] });

        await act(async () => {
          await useBusinessInfoStore.getState().reorderFaqs([2, 1]);
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqs[0].id).toBe(2);
        expect(state.faqs[1].id).toBe(1);
        expect(state.faqsLoadingState).toBe('success');
      });

      it('should handle reorder errors', async () => {
        vi.mocked(businessInfoService.businessInfoApi.reorderFaqs).mockRejectedValue(
          new Error('Reorder failed')
        );

        await act(async () => {
          await expect(useBusinessInfoStore.getState().reorderFaqs([1, 2])).rejects.toThrow();
        });

        const state = useBusinessInfoStore.getState();
        expect(state.faqsLoadingState).toBe('error');
      });
    });
  });

  describe('Utility Methods', () => {
    it('should clear error', () => {
      useBusinessInfoStore.setState({ error: 'Test error' });

      act(() => {
        useBusinessInfoStore.getState().clearError();
      });

      expect(useBusinessInfoStore.getState().error).toBeNull();
    });

    it('should reset store', () => {
      const mockFaq = {
        id: 1,
        question: 'Test question?',
        answer: 'Test answer',
        keywords: 'test',
        orderIndex: 0,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };

      useBusinessInfoStore.setState({
        businessName: 'Test',
        businessDescription: 'Test',
        businessHours: '9-5',
        faqs: [mockFaq],
        loadingState: 'success',
        error: 'Test error',
        isDirty: true,
      });

      act(() => {
        useBusinessInfoStore.getState().reset();
      });

      const state = useBusinessInfoStore.getState();
      expect(state.businessName).toBeNull();
      expect(state.businessDescription).toBeNull();
      expect(state.businessHours).toBeNull();
      expect(state.faqs).toEqual([]);
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });

    it('should discard changes (clear dirty flag)', () => {
      useBusinessInfoStore.setState({ isDirty: true });

      act(() => {
        useBusinessInfoStore.getState().discardChanges();
      });

      expect(useBusinessInfoStore.getState().isDirty).toBe(false);
    });

    it('should report unsaved changes', () => {
      useBusinessInfoStore.setState({ isDirty: true });

      expect(useBusinessInfoStore.getState().hasUnsavedChanges()).toBe(true);
    });
  });
});
