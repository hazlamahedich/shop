/**
 * Bot Config Store - Zustand state management for bot configuration
 *
 * Story 1.12: Bot Naming
 *
 * Manages bot configuration state including:
 * - Bot name
 * - Personality type
 * - Custom greeting
 * - Loading and error states
 * - Fetching and updating configuration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  botConfigApi,
  BotConfigError,
  type BotConfigResponse,
  type BotNameUpdateRequest,
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

  // UI state
  loadingState: LoadingState;
  error: string | null;
  isDirty: boolean; // True when local changes haven't been saved

  // Actions - Bot config management
  fetchBotConfig: () => Promise<void>;
  updateBotName: (update: BotNameUpdateRequest) => Promise<void>;
  setBotName: (name: string) => void;

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
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });
      },
    }),
    {
      name: 'bot-config-store',
      // Persist configuration but not loading/error states
      partialize: (state) => ({
        botName: state.botName,
        personality: state.personality,
        customGreeting: state.customGreeting,
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
export const selectBotConfigLoading = (state: BotConfigState) =>
  state.loadingState === 'loading';
export const selectBotConfigError = (state: BotConfigState) => state.error;
export const selectBotConfigIsDirty = (state: BotConfigState) => state.isDirty;
