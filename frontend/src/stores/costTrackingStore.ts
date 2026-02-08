/**
 * Cost Tracking Store - Zustand state management for LLM cost tracking
 * Handles fetching, caching, and real-time polling of cost data
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  ConversationCost,
  CostSummary,
  CostSummaryParams,
  CostTrackingState,
} from '../types/cost';
import { costTrackingService } from '../services/costTracking';

type MerchantSettings = {
  budgetCap?: number;
  budget_cap?: number;
  config: Record<string, unknown>;
};

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// Initial state
const initialState = {
  // Conversation costs
  conversationCosts: {} as Record<string, ConversationCost>,
  conversationCostsLoading: {} as Record<string, boolean>,
  conversationCostsError: {} as Record<string, string | null>,

  // Cost summary
  costSummary: null as CostSummary | null,
  previousPeriodSummary: null as CostSummary | null,
  costSummaryLoading: false,
  costSummaryError: null as string | null,
  costSummaryParams: {} as CostSummaryParams,

  // Merchant settings
  merchantSettings: null as MerchantSettings | null,
  merchantSettingsLoading: false,
  merchantSettingsError: null as string | null,

  // Real-time polling
  isPolling: false,
  pollingInterval: 30000, // 30 seconds default
  lastUpdate: null as string | null,
};

let pollingTimer: ReturnType<typeof setInterval> | null = null;

/**
 * Cost tracking store using Zustand
 */
export const useCostTrackingStore = create<CostTrackingState>()(
  persist(
    (set, get) => ({
      ...initialState,

      /**
       * Fetch cost breakdown for a specific conversation
       */
      fetchConversationCost: async (conversationId: string) => {
        set((state) => ({
          conversationCostsLoading: {
            ...state.conversationCostsLoading,
            [conversationId]: true,
          },
          conversationCostsError: {
            ...state.conversationCostsError,
            [conversationId]: null,
          },
        }));

        try {
          const response = await costTrackingService.getConversationCost(conversationId);

          // Backend returns raw object, not envelope
          const rawData = response as any;
          const data = rawData.data || rawData;

          set((state) => ({
            conversationCosts: {
              ...state.conversationCosts,
              [conversationId]: data,
            },
            conversationCostsLoading: {
              ...state.conversationCostsLoading,
              [conversationId]: false,
            },
            lastUpdate: new Date().toISOString(),
          }));
        } catch (error) {
          set((state) => ({
            conversationCostsLoading: {
              ...state.conversationCostsLoading,
              [conversationId]: false,
            },
            conversationCostsError: {
              ...state.conversationCostsError,
              [conversationId]:
                error instanceof Error ? error.message : 'Failed to fetch conversation cost',
            },
          }));
        }
      },

      /**
       * Clear cached conversation cost
       */
      clearConversationCost: (conversationId: string) => {
        set((state) => {
          const newConversationCosts = { ...state.conversationCosts };
          const newConversationCostsLoading = { ...state.conversationCostsLoading };
          const newConversationCostsError = { ...state.conversationCostsError };

          delete newConversationCosts[conversationId];
          delete newConversationCostsLoading[conversationId];
          delete newConversationCostsError[conversationId];

          return {
            conversationCosts: newConversationCosts,
            conversationCostsLoading: newConversationCostsLoading,
            conversationCostsError: newConversationCostsError,
          };
        });
      },

      /**
       * Fetch cost summary with optional date range
       */
      fetchCostSummary: async (params: CostSummaryParams = {}) => {
        const currentState = get();
        const mergedParams = { ...currentState.costSummaryParams, ...params };

        set({
          costSummaryLoading: true,
          costSummaryError: null,
          costSummaryParams: mergedParams,
        });

        try {
          const response = await costTrackingService.getCostSummary(mergedParams);

          // Backend returns raw object, not envelope
          const rawData = response as any;
          const data = rawData.data || rawData;

          set({
            costSummary: data,
            previousPeriodSummary: data.previousPeriodSummary || null,
            costSummaryLoading: false,
            lastUpdate: new Date().toISOString(),
          });
        } catch (error) {
          set({
            costSummaryLoading: false,
            costSummaryError:
              error instanceof Error ? error.message : 'Failed to fetch cost summary',
          });
        }
      },

      /**
       * Set cost summary query parameters (without fetching)
       */
      setCostSummaryParams: (params: CostSummaryParams) => {
        set((state) => ({
          costSummaryParams: { ...state.costSummaryParams, ...params },
        }));
      },

      /**
       * Start real-time polling for cost updates
       * Polls both conversation costs (if conversationId provided) and cost summary
       */
      startPolling: (conversationId?: string, interval?: number) => {
        const state = get();

        // Clear existing timer if any
        if (pollingTimer) {
          clearInterval(pollingTimer);
        }

        // Update interval if provided
        if (interval !== undefined) {
          set({ pollingInterval: interval });
        }

        // Set polling state
        set({ isPolling: true });

        // Initial fetch
        if (conversationId) {
          get().fetchConversationCost(conversationId);
        }
        get().fetchCostSummary();

        // Set up polling interval
        const pollingMs = interval ?? state.pollingInterval;
        pollingTimer = setInterval(() => {
          if (conversationId) {
            get().fetchConversationCost(conversationId);
          }
          get().fetchCostSummary();
        }, pollingMs);
      },

      /**
       * Stop real-time polling
       */
      stopPolling: () => {
        if (pollingTimer) {
          clearInterval(pollingTimer);
          pollingTimer = null;
        }
        set({ isPolling: false });
      },

      /**
       * Set polling interval (restarts polling if active)
       */
      setPollingInterval: (interval: number) => {
        const state = get();
        set({ pollingInterval: interval });

        // Restart polling if active
        if (state.isPolling) {
          // Stop and restart will use new interval
          get().stopPolling();
          get().startPolling();
        }
      },

      /**
       * Clear all errors
       */
      clearErrors: () => {
        set({
          costSummaryError: null,
          conversationCostsError: {},
        });
      },

      /**
       * Update merchant settings (e.g., budget cap)
       */
      updateMerchantSettings: async (budgetCap?: number) => {
        set({
          merchantSettingsLoading: true,
          merchantSettingsError: null,
        });

        try {
          const response = await costTrackingService.updateSettings(budgetCap);

          // Backend returns raw object, not envelope
          const rawData = response as any;

          // Map API response to store format
          const settings: MerchantSettings = {
            budgetCap:
              rawData.budget_cap ??
              rawData.budgetCap ??
              rawData.data?.budget_cap ??
              rawData.data?.budgetCap,
            config: rawData.config ?? rawData.data?.config ?? {},
          };

          set({
            merchantSettings: settings,
            merchantSettingsLoading: false,
          });
        } catch (error) {
          set({
            merchantSettingsLoading: false,
            merchantSettingsError:
              error instanceof Error ? error.message : 'Failed to update merchant settings',
          });
          throw error;
        }
      },

      /**
       * Get merchant settings
       */
      getMerchantSettings: async () => {
        set({
          merchantSettingsLoading: true,
          merchantSettingsError: null,
        });

        try {
          const response = await costTrackingService.getSettings();

          // Backend returns raw object, not envelope
          const rawData = response as any;

          // Map API response to store format
          const settings: MerchantSettings = {
            budgetCap:
              rawData.budget_cap ??
              rawData.budgetCap ??
              rawData.data?.budget_cap ??
              rawData.data?.budgetCap,
            config: rawData.config ?? rawData.data?.config ?? {},
          };

          set({
            merchantSettings: settings,
            merchantSettingsLoading: false,
          });
        } catch (error) {
          set({
            merchantSettingsLoading: false,
            merchantSettingsError:
              error instanceof Error ? error.message : 'Failed to get merchant settings',
          });
        }
      },

      /**
       * Reset store to initial state
       * Also stops any active polling
       */
      reset: () => {
        if (pollingTimer) {
          clearInterval(pollingTimer);
          pollingTimer = null;
        }
        set(initialState);
      },
    }),
    {
      name: 'cost-tracking-store',
      partialize: (state) => ({
        pollingInterval: state.pollingInterval,
        costSummaryParams: state.costSummaryParams,
      }),
    }
  )
);

/**
 * Hook to auto-start polling on mount and clean up on unmount
 * Useful for components that need real-time updates
 */
export function useCostTrackingPolling(conversationId?: string, interval?: number) {
  const startPolling = useCostTrackingStore((state) => state.startPolling);
  const stopPolling = useCostTrackingStore((state) => state.stopPolling);

  // Start polling on mount (works in browser and test/jsdom environments)
  if (typeof window !== 'undefined' || typeof globalThis.window !== 'undefined') {
    startPolling(conversationId, interval);

    // Cleanup on unmount
    return () => {
      stopPolling();
    };
  }

  return () => {}; // No-op for SSR
}

/**
 * Export for testing: get the current polling timer (for cleanup in tests)
 */
export function _getPollingTimer() {
  return pollingTimer;
}

/**
 * Export for testing: clear polling timer directly
 */
export function _clearPollingTimer() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}
