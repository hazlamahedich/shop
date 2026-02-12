/**
 * Bot Config Store - Zustand state management for bot configuration
 *
 * Story 1.12: Bot Naming
 * Story 1.14: Smart Greeting Templates
 * Story 1.15: Product Highlight Pins
 *
 * Manages bot configuration state including:
 * - Bot name
 * - Personality type
 * - Custom greeting
 * - Greeting configuration (template, use_custom_greeting)
 * - Product pin state (products, search, filters)
 * - Loading and error states
 * - Fetching and updating configuration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  botConfigApi,
  productPinApi,
  BotConfigError,
  type BotConfigResponse,
  type BotNameUpdateRequest,
  type GreetingConfigResponse,
  type GreetingConfigUpdateRequest,
  type ProductPinItem,
  type PaginationMeta,
  type ProductPinsResponse,
} from '../services/botConfig';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Bot Config Store State
 */
export interface BotConfigState {
  // Bot config data
  botName: string | null;
  personality: string | null;
  customGreeting: string | null;

  // Story 1.14: Greeting config data
  greetingTemplate: string | null;
  useCustomGreeting: boolean;
  defaultTemplate: string | null;
  availableVariables: string[];

  // Story 1.15: Product pin data
  productPins: ProductPinItem[];
  productsLoading: boolean;
  productsError: string | null;
  searchQuery: string;
  pinnedOnly: boolean;
  pagination?: PaginationMeta;
  pinLimitInfo: {
    pinLimit: number;
    pinnedCount: number;
  } | null;

  // UI state
  loadingState: LoadingState;
  error: string | null;
  isDirty: boolean; // True when local changes haven't been saved

  // Actions - Bot config management
  fetchBotConfig: () => Promise<void>;
  fetchGreetingConfig: () => Promise<void>;
  updateBotName: (update: BotNameUpdateRequest) => Promise<void>;
  updateGreetingConfig: (update: GreetingConfigUpdateRequest) => Promise<void>;
  resetGreetingToDefault: () => Promise<void>;
  setBotName: (name: string) => void;

  // Actions - Story 1.15: Product pin management
  fetchProductPins: (options?: {
    search?: string;
    pinnedOnly?: boolean;
    page?: number;
    limit?: number;
  }) => Promise<void>;
  pinProduct: (productId: string) => Promise<void>;
  unpinProduct: (productId: string) => Promise<void>;
  setSearchQuery: (query: string) => void;
  togglePinnedOnly: () => void;
  clearProductsError: () => void;

  // Actions - State checks
  hasUnsavedChanges: () => boolean;
  discardChanges: () => void;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
}

/**
 * Bot Config store using Zustand
 *
 * Manages bot configuration state with optimistic updates
 * and automatic error recovery.
 */
export const useBotConfigStore = create<BotConfigState>()(
  persist(
    (set, get) => ({
      // Initial state
      botName: null,
      personality: null,
      customGreeting: null,
      // Story 1.14: Greeting config initial state
      greetingTemplate: null,
      useCustomGreeting: false,
      defaultTemplate: null,
      availableVariables: ['bot_name', 'business_name', 'business_hours'],
      // Story 1.15: Product pin initial state
      productPins: [],
      productsLoading: false,
      productsError: null,
      searchQuery: '',
      pinnedOnly: false,
      pagination: undefined,
      pinLimitInfo: null,
      // General UI state
      loadingState: 'idle',
      error: null,
      isDirty: false,

      /**
       * Fetch the current bot configuration from the server
       *
       * Always fetches fresh configuration and clears any unsaved local changes.
       */
      fetchBotConfig: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: BotConfigResponse = await botConfigApi.getBotConfig();

          set({
            botName: config.botName,
            personality: config.personality,
            customGreeting: config.customGreeting,
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch bot configuration';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Update bot name on the server
       *
       * Sends changes to the server and updates local state on success.
       *
       * @param update - Configuration update with optional bot_name field
       */
      updateBotName: async (update: BotNameUpdateRequest) => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: BotConfigResponse = await botConfigApi.updateBotName(update);

          set({
            botName: config.botName,
            personality: config.personality,
            customGreeting: config.customGreeting,
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to update bot name';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Set the bot name locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updateBotName to persist changes.
       *
       * @param name - The new bot name
       */
      setBotName: (name: string) => {
        set({
          botName: name.trim() || null,
          isDirty: true,
        });
      },

      /**
       * Fetch greeting configuration from server (Story 1.14)
       *
       * Always fetches fresh configuration and clears any unsaved local changes.
       */
      fetchGreetingConfig: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: GreetingConfigResponse = await botConfigApi.fetchGreetingConfig();

          set({
            greetingTemplate: config.greetingTemplate,
            useCustomGreeting: config.useCustomGreeting,
            defaultTemplate: config.defaultTemplate,
            availableVariables: config.availableVariables || [],
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch greeting configuration';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Update greeting configuration on server (Story 1.14)
       *
       * Sends changes to server and updates local state on success.
       *
       * @param update - Configuration update with optional greeting fields
       */
      updateGreetingConfig: async (update: GreetingConfigUpdateRequest) => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: GreetingConfigResponse = await botConfigApi.updateGreetingConfig(update);

          set({
            greetingTemplate: config.greetingTemplate,
            useCustomGreeting: config.useCustomGreeting,
            defaultTemplate: config.defaultTemplate,
            availableVariables: config.availableVariables || [],
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to update greeting configuration';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Reset greeting to personality default (Story 1.14)
       *
       * Clears custom greeting and disables custom greeting mode.
       */
      resetGreetingToDefault: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: GreetingConfigResponse = await botConfigApi.updateGreetingConfig({
            greeting_template: '',
            use_custom_greeting: false,
          });

          set({
            greetingTemplate: config.greetingTemplate,
            useCustomGreeting: config.useCustomGreeting,
            defaultTemplate: config.defaultTemplate,
            availableVariables: config.availableVariables || [],
            loadingState: 'success',
            isDirty: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to reset greeting configuration';

          set({
            loadingState: 'error',
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
       * Note: This doesn't revert local changes - use fetchBotConfig
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
          botName: null,
          personality: null,
          customGreeting: null,
          // Story 1.14: Reset greeting config
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: ['bot_name', 'business_name', 'business_hours'],
          // Story 1.15: Reset product pin state
          productPins: [],
          productsLoading: false,
          productsError: null,
          searchQuery: '',
          pinnedOnly: false,
          pagination: undefined,
          pinLimitInfo: null,
          // General UI state
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });
      },

      // Story 1.15: Product Pin Actions

      /**
       * Fetch products with pin status
       *
       * @param options - Optional search, pinned_only filter, pagination
       */
      fetchProductPins: async (options = {}) => {
        const {
          search = get().searchQuery,
          pinnedOnly = get().pinnedOnly,
          page = 1,
          limit = 20,
        } = options;

        set({
          productsLoading: true,
          productsError: null,
          ...(search !== undefined && { searchQuery: search }),
          ...(pinnedOnly !== undefined && { pinnedOnly }),
        });

        try {
          const response: ProductPinsResponse = await productPinApi.fetchProductsWithPinStatus(
            search,
            pinnedOnly,
            page,
            limit
          );

          set({
            productPins: response.products || [],
            pagination: response.pagination,
            pinLimitInfo: {
              pinLimit: response.pinLimit,
              pinnedCount: response.pinnedCount,
            },
            productsLoading: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch products';

          set({
            productsLoading: false,
            productsError: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Pin a product
       *
       * @param productId - Shopify product ID to pin
       */
      pinProduct: async (productId: string) => {
        set({ productsLoading: true, productsError: null });

        try {
          await productPinApi.pinProduct(productId);

          // Optimistically update the product in the list
          set({
            productPins: get().productPins.map(p =>
              p.productId === productId
                ? { ...p, isPinned: true }
                : p
            ),
            productsLoading: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to pin product';

          set({
            productsLoading: false,
            productsError: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Unpin a product
       *
       * @param productId - Shopify product ID to unpin
       */
      unpinProduct: async (productId: string) => {
        set({ productsLoading: true, productsError: null });

        try {
          await productPinApi.unpinProduct(productId);

          // Optimistically update the product in the list
          set({
            productPins: get().productPins.map(p =>
              p.productId === productId
                ? { ...p, isPinned: false, pinnedOrder: undefined, pinnedAt: undefined }
                : p
            ),
            productsLoading: false,
          });
        } catch (error) {
          const errorMessage =
            error instanceof BotConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to unpin product';

          set({
            productsLoading: false,
            productsError: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Set search query for products
       *
       * @param query - Search query string
       */
      setSearchQuery: (query: string) => {
        set({ searchQuery: query });
      },

      /**
       * Toggle between showing all products or only pinned products
       */
      togglePinnedOnly: () => {
        const current = get().pinnedOnly;
        set({ pinnedOnly: !current });
      },

      /**
       * Clear products error state
       */
      clearProductsError: () => {
        set({ productsError: null });
      },
    }),
    {
      name: 'bot-config-store',
      // Persist configuration but not loading/error states
      partialize: (state) => ({
        botName: state.botName,
        personality: state.personality,
        customGreeting: state.customGreeting,
        // Story 1.14: Persist greeting config
        greetingTemplate: state.greetingTemplate,
        useCustomGreeting: state.useCustomGreeting,
        defaultTemplate: state.defaultTemplate,
        availableVariables: state.availableVariables,
        // Story 1.15: Persist product pin config
        searchQuery: state.searchQuery,
        pinnedOnly: state.pinnedOnly,
      }),
    }
  )
);

/**
 * Bot Config Hook Helpers
 *
 * Convenience hooks for common bot config operations.
 */

/**
 * Initialize bot configuration on mount
 *
 * Usage in components:
 * ```tsx
 * useEffect(() => {
 *   initializeBotConfig();
 * }, []);
 * ```
 */
export const initializeBotConfig = async (): Promise<void> => {
  try {
    await useBotConfigStore.getState().fetchBotConfig();
  } catch (error) {
    console.error('Failed to initialize bot configuration:', error);
    throw error;
  }
};

/**
 * Selectors for common state values
 */
export const selectBotName = (state: BotConfigState) => state.botName;
export const selectPersonality = (state: BotConfigState) => state.personality;
export const selectCustomGreeting = (state: BotConfigState) => state.customGreeting;
// Story 1.14: Greeting config selectors
export const selectGreetingTemplate = (state: BotConfigState) => state.greetingTemplate;
export const selectUseCustomGreeting = (state: BotConfigState) => state.useCustomGreeting;
export const selectDefaultTemplate = (state: BotConfigState) => state.defaultTemplate;
export const selectAvailableVariables = (state: BotConfigState) => state.availableVariables;
// Story 1.15: Product pin selectors
export const selectProductPins = (state: BotConfigState) => state.productPins;
export const selectProductsLoading = (state: BotConfigState) => state.productsLoading;
export const selectProductsError = (state: BotConfigState) => state.productsError;
export const selectSearchQuery = (state: BotConfigState) => state.searchQuery;
export const selectPinnedOnly = (state: BotConfigState) => state.pinnedOnly;
export const selectPagination = (state: BotConfigState) => state.pagination;
export const selectPinLimitInfo = (state: BotConfigState) => state.pinLimitInfo;
// General selectors
export const selectBotConfigLoading = (state: BotConfigState) =>
  state.loadingState === 'loading';
export const selectBotConfigError = (state: BotConfigState) => state.error;
export const selectBotConfigIsDirty = (state: BotConfigState) => state.isDirty;
