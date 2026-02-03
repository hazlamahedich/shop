/** Zustand store for onboarding prerequisite checklist.

Story 1.2 (implemented): Syncs prerequisite state with PostgreSQL backend
while keeping localStorage as fallback for offline scenarios.

Features:
- Primary storage: PostgreSQL (via API)
- Fallback storage: localStorage (for offline)
- Auto-sync: Changes saved to both backend and localStorage
- Migration: Loads from localStorage and syncs to backend on first load

Key: shop_onboarding_prerequisites
Schema: { cloudAccount, facebookAccount, shopifyAccess, llmProviderChoice, updatedAt }
*/

import { create } from "zustand";
import {
  getPrerequisiteState,
  savePrerequisiteState as savePrerequisiteStateApi,
  syncPrerequisiteState as syncPrerequisiteStateApi,
  toBackendFormat,
  fromBackendFormat,
  type PrerequisiteSyncRequest,
} from "../services/onboarding";

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
  updatedAt: string | null;
}

export interface OnboardingStore extends PrerequisiteState {
  // Actions
  togglePrerequisite: (key: PrerequisiteKey) => void;
  reset: () => void;
  loadFromStorage: () => void;
  syncToBackend: () => Promise<void>;
  loadFromBackend: () => Promise<void>;
  // Computed values
  isComplete: () => boolean;
  completedCount: () => number;
  totalCount: number;
}

const initialState: PrerequisiteState = {
  cloudAccount: false,
  facebookAccount: false,
  shopifyAccess: false,
  llmProviderChoice: false,
  updatedAt: null,
};

const loadFromStorage = (): PrerequisiteState => {
  try {
    if (typeof localStorage === "undefined") {
      return initialState;
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored) as PrerequisiteState;
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
   * Load state from backend (Story 1.2 migration).
   * If backend has data, use it; otherwise keep localStorage data.
   */
  loadFromBackend: async () => {
    try {
      const backendData = await getPrerequisiteState(DEFAULT_MERCHANT_ID);

      if (backendData) {
        // Backend has data - use it
        const frontendState = fromBackendFormat(backendData);
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
            const migratedState = fromBackendFormat(syncedState);
            set(migratedState);
            saveToStorage(migratedState);
          }
        }
      }
    } catch (error) {
      console.warn("Failed to load onboarding state from backend:", error);
      // Keep localStorage data as fallback
    }
  },

  isComplete: () => {
    const state = get();
    return (
      state.cloudAccount &&
      state.facebookAccount &&
      state.shopifyAccess &&
      state.llmProviderChoice
    );
  },

  completedCount: () => {
    const state = get();
    return [
      state.cloudAccount,
      state.facebookAccount,
      state.shopifyAccess,
      state.llmProviderChoice,
    ].filter(Boolean).length;
  },

  totalCount: 4,
}));

// Initialize from localStorage on import (only in browser, not during tests)
if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
  onboardingStore.getState().loadFromStorage();

  // Story 1.2: Auto-migrate localStorage to backend on app load
  // Don't await - let it happen in background
  onboardingStore.getState().loadFromBackend();
}
