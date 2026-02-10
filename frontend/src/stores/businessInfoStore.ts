/**
 * Business Info & FAQ Store - Zustand state management for business info and FAQ configuration
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Manages business info and FAQ configuration state including:
 * - Business information (name, description, hours)
 * - FAQ items array with CRUD operations
 * - Loading and error states
 * - Fetching and updating configuration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  businessInfoApi,
  BusinessInfoError,
  type BusinessInfoResponse,
  type BusinessInfoUpdateRequest,
  type FaqResponse,
  type FaqCreateRequest,
  type FaqUpdateRequest,
} from '../services/businessInfo';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * FAQ item interface for store
 */
export interface FaqItem {
  id: number;
  question: string;
  answer: string;
  keywords: string | null;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

/**
 * Business Info Store State
 */
export interface BusinessInfoState {
  // Business info data
  businessName: string | null;
  businessDescription: string | null;
  businessHours: string | null;

  // FAQ data
  faqs: FaqItem[];

  // UI state
  loadingState: LoadingState;
  faqsLoadingState: LoadingState;
  error: string | null;
  isDirty: boolean; // True when local changes haven't been saved

  // Actions - Business info management
  fetchBusinessInfo: () => Promise<void>;
  updateBusinessInfo: (update: BusinessInfoUpdateRequest) => Promise<void>;
  setBusinessName: (name: string) => void;
  setBusinessDescription: (description: string) => void;
  setBusinessHours: (hours: string) => void;

  // Actions - FAQ management
  fetchFaqs: () => Promise<void>;
  createFaq: (faq: FaqCreateRequest) => Promise<FaqItem>;
  updateFaq: (faqId: number, update: FaqUpdateRequest) => Promise<void>;
  deleteFaq: (faqId: number) => Promise<void>;
  reorderFaqs: (faqIds: number[]) => Promise<void>;

  // Actions - State checks
  hasUnsavedChanges: () => boolean;
  discardChanges: () => void;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
}

/**
 * Convert API response to store FAQ item
 */
function apiFaqToStoreFaq(faq: FaqResponse): FaqItem {
  return {
    id: faq.id,
    question: faq.question,
    answer: faq.answer,
    keywords: faq.keywords,
    orderIndex: faq.orderIndex,
    createdAt: faq.createdAt,
    updatedAt: faq.updatedAt,
  };
}

/**
 * Business Info store using Zustand
 *
 * Manages business info and FAQ state with optimistic updates
 * and automatic error recovery.
 */
export const useBusinessInfoStore = create<BusinessInfoState>()(
  persist(
    (set, get) => ({
      // Initial state
      businessName: null,
      businessDescription: null,
      businessHours: null,
      faqs: [],
      loadingState: 'idle',
      faqsLoadingState: 'idle',
      error: null,
      isDirty: false,

      /**
       * Fetch the current business information from the server
       *
       * Always fetches fresh configuration and clears any unsaved local changes.
       */
      fetchBusinessInfo: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const info: BusinessInfoResponse = await businessInfoApi.getBusinessInfo();

          set({
            businessName: info.business_name,
            businessDescription: info.business_description,
            businessHours: info.business_hours,
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch business information';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Update business information on the server
       *
       * Sends changes to the server and updates local state on success.
       *
       * @param update - Configuration update with optional fields
       */
      updateBusinessInfo: async (update: BusinessInfoUpdateRequest) => {
        set({ loadingState: 'loading', error: null });

        try {
          const info: BusinessInfoResponse = await businessInfoApi.updateBusinessInfo(update);

          set({
            businessName: info.business_name,
            businessDescription: info.business_description,
            businessHours: info.business_hours,
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to update business information';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Set the business name locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updateBusinessInfo to persist changes.
       *
       * @param name - The new business name
       */
      setBusinessName: (name: string) => {
        set({
          businessName: name.trim() || null,
          isDirty: true,
        });
      },

      /**
       * Set the business description locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updateBusinessInfo to persist changes.
       *
       * @param description - The new business description
       */
      setBusinessDescription: (description: string) => {
        set({
          businessDescription: description.trim() || null,
          isDirty: true,
        });
      },

      /**
       * Set the business hours locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updateBusinessInfo to persist changes.
       *
       * @param hours - The new business hours
       */
      setBusinessHours: (hours: string) => {
        set({
          businessHours: hours.trim() || null,
          isDirty: true,
        });
      },

      /**
       * Fetch FAQ items from the server
       *
       * Always fetches fresh FAQ list and clears any unsaved local changes.
       */
      fetchFaqs: async () => {
        set({ faqsLoadingState: 'loading', error: null });

        try {
          const faqs: FaqResponse[] = await businessInfoApi.getFaqs();

          set({
            faqs: faqs.map(apiFaqToStoreFaq),
            faqsLoadingState: 'success',
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch FAQ items';

          set({
            faqsLoadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Create a new FAQ item
       *
       * @param faq - FAQ creation data
       * @returns Created FAQ item
       */
      createFaq: async (faq: FaqCreateRequest) => {
        set({ faqsLoadingState: 'loading', error: null });

        try {
          const newFaq: FaqResponse = await businessInfoApi.createFaq(faq);
          const storeFaq = apiFaqToStoreFaq(newFaq);

          set({
            faqs: [...get().faqs, storeFaq].sort((a, b) => a.orderIndex - b.orderIndex),
            faqsLoadingState: 'success',
          });

          return storeFaq;
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to create FAQ item';

          set({
            faqsLoadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Update an existing FAQ item
       *
       * @param faqId - ID of the FAQ to update
       * @param update - FAQ update data
       */
      updateFaq: async (faqId: number, update: FaqUpdateRequest) => {
        set({ faqsLoadingState: 'loading', error: null });

        try {
          const updatedFaq: FaqResponse = await businessInfoApi.updateFaq(faqId, update);
          const storeFaq = apiFaqToStoreFaq(updatedFaq);

          set({
            faqs: get().faqs.map((faq) =>
              faq.id === faqId ? storeFaq : faq
            ).sort((a, b) => a.orderIndex - b.orderIndex),
            faqsLoadingState: 'success',
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to update FAQ item';

          set({
            faqsLoadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Delete an FAQ item
       *
       * @param faqId - ID of the FAQ to delete
       */
      deleteFaq: async (faqId: number) => {
        set({ faqsLoadingState: 'loading', error: null });

        try {
          await businessInfoApi.deleteFaq(faqId);

          set({
            faqs: get().faqs.filter((faq) => faq.id !== faqId),
            faqsLoadingState: 'success',
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to delete FAQ item';

          set({
            faqsLoadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Reorder FAQ items
       *
       * @param faqIds - Array of FAQ IDs in the desired display order
       */
      reorderFaqs: async (faqIds: number[]) => {
        set({ faqsLoadingState: 'loading', error: null });

        try {
          const reorderedFaqs: FaqResponse[] = await businessInfoApi.reorderFaqs(faqIds);

          set({
            faqs: reorderedFaqs.map(apiFaqToStoreFaq),
            faqsLoadingState: 'success',
          });
        } catch (error) {
          const errorMessage =
            error instanceof BusinessInfoError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to reorder FAQ items';

          set({
            faqsLoadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Check if there are unsaved changes
       *
       * @returns true if there are local changes that haven't been saved
       */
      hasUnsavedChanges: (): boolean => {
        return get().isDirty;
      },

      /**
       * Discard unsaved changes
       *
       * Resets to the last saved state by clearing the dirty flag.
       * Note: This doesn't revert local changes - use fetchBusinessInfo
       * to reload from the server.
       */
      discardChanges: () => {
        set({ isDirty: false });
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },

      /**
       * Reset store to initial state
       */
      reset: () => {
        set({
          businessName: null,
          businessDescription: null,
          businessHours: null,
          faqs: [],
          loadingState: 'idle',
          faqsLoadingState: 'idle',
          error: null,
          isDirty: false,
        });
      },
    }),
    {
      name: 'business-info-store',
      // Persist configuration but not loading/error states
      partialize: (state) => ({
        businessName: state.businessName,
        businessDescription: state.businessDescription,
        businessHours: state.businessHours,
        faqs: state.faqs,
      }),
    }
  )
);

/**
 * Business Info Hook Helpers
 *
 * Convenience hooks for common business info operations.
 */

/**
 * Initialize business info configuration on mount
 *
 * Usage in components:
 * ```tsx
 * useEffect(() => {
 *   initializeBusinessInfo();
 * }, []);
 * ```
 */
export const initializeBusinessInfo = async (): Promise<void> => {
  try {
    await Promise.all([
      useBusinessInfoStore.getState().fetchBusinessInfo(),
      useBusinessInfoStore.getState().fetchFaqs(),
    ]);
  } catch (error) {
    console.error('Failed to initialize business info configuration:', error);
    throw error;
  }
};

/**
 * Selectors for common state values
 */
export const selectBusinessName = (state: BusinessInfoState) => state.businessName;
export const selectBusinessDescription = (state: BusinessInfoState) => state.businessDescription;
export const selectBusinessHours = (state: BusinessInfoState) => state.businessHours;
export const selectFaqs = (state: BusinessInfoState) => state.faqs;
export const selectBusinessInfoLoading = (state: BusinessInfoState) => state.loadingState === 'loading';
export const selectFaqsLoading = (state: BusinessInfoState) => state.faqsLoadingState === 'loading';
export const selectBusinessInfoError = (state: BusinessInfoState) => state.error;
export const selectBusinessInfoIsDirty = (state: BusinessInfoState) => state.isDirty;
