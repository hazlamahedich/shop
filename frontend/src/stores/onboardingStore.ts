/** Zustand store for onboarding prerequisite checklist.

Manages localStorage persistence for prerequisite checklist state.
Migrates to PostgreSQL after deployment (Story 1.2).

Key: shop_onboarding_prerequisites
Schema: { cloudAccount, facebookAccount, shopifyAccess, llmProviderChoice, updatedAt }
*/

import { create } from "zustand";

const STORAGE_KEY = "shop_onboarding_prerequisites";

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
  },

  loadFromStorage: () => {
    const stored = loadFromStorage();
    set(stored);
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
}
