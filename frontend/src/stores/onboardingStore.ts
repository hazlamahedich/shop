/** Zustand store for onboarding prerequisite checklist.

Story 1.2 (implemented): Syncs prerequisite state with PostgreSQL backend
while keeping localStorage as fallback for offline scenarios.
Story 8.6: Added onboarding mode support for mode-aware prerequisite tracking.

Features:
- Primary storage: PostgreSQL (via API)
- Fallback storage: localStorage (for offline)
- Auto-sync: Changes saved to both backend and localStorage
- Migration: Loads from localStorage and syncs to backend on first load
- Mode-aware: Different prerequisites required based on onboarding mode

Key: shop_onboarding_prerequisites
Schema: { cloudAccount, facebookAccount, shopifyAccess, llmProviderChoice, onboardingMode, updatedAt }
*/

import { create } from "zustand";
import {
  getPrerequisiteState,
  savePrerequisiteState as savePrerequisiteStateApi,
  syncPrerequisiteState as syncPrerequisiteStateApi,
  toBackendFormat,
  fromBackendFormat,
  getOnboardingMode,
  type PrerequisiteSyncRequest,
} from "../services/onboarding";
import { csrfManager } from "../services/csrf";
import {
  OnboardingMode,
  DEFAULT_ONBOARDING_MODE,
  isValidOnboardingMode,
} from "../types/onboarding";

const STORAGE_KEY = "shop_onboarding_prerequisites";
const DEFAULT_MERCHANT_ID = 1;

export type PrerequisiteKey =
  | "cloudAccount"
  | "facebookAccount"
  | "shopifyAccess"
  | "llmProviderChoice";

export interface PrerequisiteState {
  cloudAccount: boolean;
  facebookAccount: boolean;
  shopifyAccess: boolean;
  llmProviderChoice: boolean;
  onboardingMode: OnboardingMode | null;
  updatedAt: string | null;
}

export interface OnboardingStore extends PrerequisiteState {
  // Actions
  togglePrerequisite: (key: PrerequisiteKey) => void;
  setOnboardingMode: (mode: OnboardingMode) => void;
  reset: () => void;
  loadFromStorage: () => void;
  syncToBackend: () => Promise<void>;
  loadFromBackend: () => Promise<void>;
  // Computed values
  isComplete: () => boolean;
  completedCount: () => number;
  totalCount: () => number;
}

const initialState: PrerequisiteState = {
  cloudAccount: false,
  facebookAccount: false,
  shopifyAccess: false,
  llmProviderChoice: false,
  onboardingMode: null,
  updatedAt: null,
};

const loadFromStorage = (): PrerequisiteState => {
  try {
    if (typeof localStorage === "undefined") {
      return initialState;
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as PrerequisiteState;
      return parsed;
    }
  } catch (error) {
    console.warn("Failed to load onboarding state from localStorage:", error);
  }
  return initialState;
};

const saveToStorage = (state: PrerequisiteState): void => {
  try {
    if (typeof localStorage === "undefined") {
      return;
    }
    const toSave = {
      ...state,
      updatedAt: new Date().toISOString(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (error) {
    console.warn("Failed to save onboarding state to localStorage:", error);
  }
};

/**
 * Sync state to backend (PostgreSQL).
 * Used internally when state changes occur.
 */
const syncToBackend = async (state: PrerequisiteState): Promise<void> => {
  try {
    const backendState = toBackendFormat(state);
    await savePrerequisiteStateApi(backendState, DEFAULT_MERCHANT_ID);
  } catch (error) {
    console.warn("Failed to sync prerequisite state to backend:", error);
    // Continue using localStorage as fallback
  }
};

/**
 * Sync onboarding mode to backend via merchant mode endpoint.
 * Includes CSRF protection for the PATCH request.
 */
const syncModeToBackend = async (mode: OnboardingMode): Promise<void> => {
  try {
    const csrfToken = await csrfManager.getToken();
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
    const response = await fetch(`${API_BASE_URL}/api/merchant/mode`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      credentials: "include",
      body: JSON.stringify({ mode }),
    });

    if (!response.ok) {
      throw new Error(`Failed to sync mode: ${response.status}`);
    }
  } catch (error) {
    console.warn("Failed to sync onboarding mode to backend:", error);
    // Re-throw so caller can handle UI feedback
    throw error;
  }
};

export const onboardingStore = create<OnboardingStore>((set, get) => ({
  ...initialState,

  togglePrerequisite: (key: PrerequisiteKey) => {
    const currentState = get();
    const newState = {
      ...currentState,
      [key]: !currentState[key],
    };
    set(newState);
    saveToStorage(newState);
    // Sync to backend asynchronously (don't await)
    syncToBackend(newState);
  },

  setOnboardingMode: async (mode: OnboardingMode) => {
    // Sync mode to backend FIRST - throw error on failure so UI can handle it
    // Only update store after successful API call
    await syncModeToBackend(mode);
    
    // API call succeeded - now update store and localStorage
    const currentState = get();
    const newState = {
      ...currentState,
      onboardingMode: mode,
    };
    set(newState);
    saveToStorage(newState);
  },

  reset: () => {
    set(initialState);
    try {
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (error) {
      console.warn("Failed to clear onboarding state from localStorage:", error);
    }
    // Backend state is not deleted - keeps server record as fallback
  },

  loadFromStorage: () => {
    const stored = loadFromStorage();
    set(stored);
  },

  /**
   * Manually sync current state to backend (Story 1.2 migration).
   * Call this after making changes to ensure backend is updated.
   */
  syncToBackend: async () => {
    const state = get();
    await syncToBackend(state);
  },

  /**
   * Load state from backend (Story 1.2 migration, Story 8.6 mode loading).
   * Fetches both prerequisites and onboarding mode from backend.
   * If backend has data, use it; otherwise keep localStorage data.
   */
  loadFromBackend: async () => {
    try {
      // Fetch both prerequisites and mode in parallel
      const [backendData, mode] = await Promise.all([
        getPrerequisiteState(DEFAULT_MERCHANT_ID),
        getOnboardingMode(),
      ]);

      if (backendData) {
        // Backend has data - use it with the fetched mode
        const frontendState = fromBackendFormat(backendData, mode ?? undefined);
        set(frontendState);
        saveToStorage(frontendState);
      } else {
        // Backend has no data - try to migrate from localStorage
        const localStorageState = loadFromStorage();
        const hasLocalData =
          localStorageState.cloudAccount ||
          localStorageState.facebookAccount ||
          localStorageState.shopifyAccess ||
          localStorageState.llmProviderChoice;

        if (hasLocalData) {
          // Migrate localStorage data to backend
          console.info("Migrating localStorage state to backend...");
          const syncData: PrerequisiteSyncRequest = {
            cloudAccount: localStorageState.cloudAccount,
            facebookAccount: localStorageState.facebookAccount,
            shopifyAccess: localStorageState.shopifyAccess,
            llmProviderChoice: localStorageState.llmProviderChoice,
            updatedAt: localStorageState.updatedAt ?? undefined,
          };
          const syncedState = await syncPrerequisiteStateApi(syncData, DEFAULT_MERCHANT_ID);
          if (syncedState) {
            const migratedState = fromBackendFormat(syncedState, mode ?? undefined);
            set(migratedState);
            saveToStorage(migratedState);
          }
      } else if (mode) {
        // No prerequisites but mode exists - just set the mode
        set({ ...get(), onboardingMode: mode });
        saveToStorage(get());
      }
      }
    } catch (error) {
      console.warn("Failed to load onboarding state from backend:", error);
      // Keep localStorage data as fallback
    }
  },

  /**
   * Check if prerequisites are complete (Story 8.6: mode-aware).
   * - General mode: only cloud + LLM required
   * - E-commerce mode: all 4 prerequisites required
   * - No mode selected: e-commerce requirements (default)
   */
  isComplete: () => {
    const state = get();
    const baseComplete = state.cloudAccount && state.llmProviderChoice;

    // General mode: only cloud + LLM required
    if (state.onboardingMode === "general") {
      return baseComplete;
    }

    // E-commerce mode (default): all prerequisites required
    return baseComplete && state.facebookAccount && state.shopifyAccess;
  },

  /**
   * Count completed prerequisites (Story 8.6: mode-aware).
   */
  completedCount: () => {
    const state = get();
    const baseCount = [state.cloudAccount, state.llmProviderChoice].filter(Boolean).length;

    if (state.onboardingMode === "general") {
      return baseCount;
    }

    return (
      baseCount +
      [state.facebookAccount, state.shopifyAccess].filter(Boolean).length
    );
  },

  /**
   * Total prerequisites count (Story 8.6: mode-aware).
   * - General mode: 2 prerequisites (cloud + LLM)
   * - E-commerce mode (or no mode selected): 4 prerequisites
   */
  totalCount: () => {
    const state = get();
    return state.onboardingMode === "general" ? 2 : 4;
  },
}));

// Initialize from localStorage on import (only in browser, not during tests)
if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
  onboardingStore.getState().loadFromStorage();

  // Story 1.2: Auto-migrate localStorage to backend on app load
  // Don't await - let it happen in background
  onboardingStore.getState().loadFromBackend();
}
