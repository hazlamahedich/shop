/**
 * Personality Configuration Store - Zustand state management for bot personality
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Manages personality configuration state including:
 * - Current personality selection (friendly, professional, enthusiastic)
 * - Custom greeting message
 * - Loading and error states
 * - Fetching and updating configuration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  merchantConfigApi,
  PersonalityConfigError,
  type PersonalityConfigResponse,
  type PersonalityConfigUpdateRequest,
} from '../services/merchantConfig';
import type { PersonalityType } from '../types/enums';
import {
  PersonalityDefaultGreetings,
} from '../types/enums';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Personality Store State
 */
export interface PersonalityState {
  // Configuration data
  personality: PersonalityType | null;
  customGreeting: string | null;

  // UI state
  loadingState: LoadingState;
  error: string | null;
  isDirty: boolean; // True when local changes haven't been saved

  // Actions - Configuration management
  fetchPersonalityConfig: () => Promise<void>;
  updatePersonalityConfig: (update: PersonalityConfigUpdateRequest) => Promise<void>;
  setPersonality: (personality: PersonalityType) => void;
  setCustomGreeting: (greeting: string) => void;
  resetToDefault: () => void;

  // Actions - State checks
  getDefaultGreeting: (personality: PersonalityType) => string;
  hasUnsavedChanges: () => boolean;
  discardChanges: () => void;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
}

/**
 * Personality store using Zustand
 *
 * Manages personality configuration state with optimistic updates
 * and automatic error recovery.
 */
export const usePersonalityStore = create<PersonalityState>()(
  persist(
    (set, get) => ({
      // Initial state
      personality: null,
      customGreeting: null,
      loadingState: 'idle',
      error: null,
      isDirty: false,

      /**
       * Fetch the current personality configuration from the server
       *
       * Always fetches fresh configuration and clears any unsaved local changes.
       */
      fetchPersonalityConfig: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: PersonalityConfigResponse = await merchantConfigApi.getPersonalityConfig();

          set({
            personality: config.personality,
            customGreeting: config.custom_greeting,
            loadingState: 'success',
            isDirty: false, // Clear dirty state on successful fetch
          });
        } catch (error) {
          const errorMessage =
            error instanceof PersonalityConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch personality configuration';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Update personality configuration on the server
       *
       * Sends changes to the server and updates local state on success.
       *
       * @param update - Configuration update with optional personality and custom_greeting
       */
      updatePersonalityConfig: async (update: PersonalityConfigUpdateRequest) => {
        set({ loadingState: 'loading', error: null });

        try {
          const config: PersonalityConfigResponse = await merchantConfigApi.updatePersonalityConfig(update);

          set({
            personality: config.personality,
            customGreeting: config.custom_greeting,
            loadingState: 'success',
            isDirty: false, // Clear dirty state on successful save
          });
        } catch (error) {
          const errorMessage =
            error instanceof PersonalityConfigError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to update personality configuration';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Set the personality type locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updatePersonalityConfig to persist changes.
       *
       * @param personality - The new personality type
       */
      setPersonality: (personality: PersonalityType) => {
        set({
          personality,
          isDirty: true,
        });
      },

      /**
       * Set the custom greeting locally (optimistic update)
       *
       * This updates the local state immediately but doesn't save to the server.
       * Call updatePersonalityConfig to persist changes.
       *
       * @param greeting - The new custom greeting (empty string clears it)
       */
      setCustomGreeting: (greeting: string) => {
        set({
          customGreeting: greeting.trim() || null,
          isDirty: true,
        });
      },

      /**
       * Reset custom greeting to the default for the current personality
       *
       * Clears the custom greeting, which will cause the bot to use
       * the personality's default greeting template.
       */
      resetToDefault: () => {
        const { personality } = get();
        if (personality) {
          set({
            customGreeting: null,
            isDirty: true,
          });
        }
      },

      /**
       * Get the default greeting for a given personality type
       *
       * @param personality - The personality type
       * @returns The default greeting for that personality
       */
      getDefaultGreeting: (personality: PersonalityType): string => {
        return PersonalityDefaultGreetings[personality];
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
       * Note: This doesn't revert local changes - use fetchPersonalityConfig
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
          personality: null,
          customGreeting: null,
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });
      },
    }),
    {
      name: 'personality-store',
      // Persist configuration but not loading/error states
      partialize: (state) => ({
        personality: state.personality,
        customGreeting: state.customGreeting,
      }),
    }
  )
);

/**
 * Personality Hook Helpers
 *
 * Convenience hooks for common personality operations.
 */

/**
 * Initialize personality configuration on mount
 *
 * Usage in components:
 * ```tsx
 * useEffect(() => {
 *   initializePersonality();
 * }, []);
 * ```
 */
export const initializePersonality = async (): Promise<void> => {
  try {
    await usePersonalityStore.getState().fetchPersonalityConfig();
  } catch (error) {
    console.error('Failed to initialize personality configuration:', error);
    throw error;
  }
};

/**
 * Selectors for common state values
 */
export const selectPersonality = (state: PersonalityState) => state.personality;
export const selectCustomGreeting = (state: PersonalityState) => state.customGreeting;
export const selectPersonalityLoading = (state: PersonalityState) => state.loadingState === 'loading';
export const selectPersonalityError = (state: PersonalityState) => state.error;
export const selectPersonalityIsDirty = (state: PersonalityState) => state.isDirty;
export const selectEffectiveGreeting = (state: PersonalityState) => {
  // Return custom greeting if set, otherwise use default for current personality
  if (state.customGreeting) {
    return state.customGreeting;
  }
  if (state.personality) {
    return PersonalityDefaultGreetings[state.personality];
  }
  return '';
};
