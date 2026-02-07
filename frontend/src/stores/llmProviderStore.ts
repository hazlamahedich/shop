/** Zustand store for LLM Provider switching state management.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Manages provider selection, switching, and validation state.
 * Follows Zustand patterns from previous stories (3-1, 3-2, 3-3).
 */

import { create } from 'zustand';
import {
  getProviders,
  switchProvider,
  validateProviderConfig,
} from '../services/llmProvider';

/** Provider pricing information */
export interface ProviderPricing {
  inputCost: number;
  outputCost: number;
  currency: string;
}

/** LLM Provider information */
export interface Provider {
  id: string;
  name: string;
  description: string;
  pricing: ProviderPricing;
  models: string[];
  features: string[];
  isActive?: boolean;
  estimatedMonthlyCost?: number;
}

/** Current provider information */
export interface CurrentProvider {
  id: string;
  name: string;
  description: string;
  model: string;
  status: string;
  configuredAt: string;
  totalTokensUsed: number;
  totalCostUsd: number;
}

/** Switch provider configuration */
export interface SwitchProviderConfig {
  providerId: string;
  apiKey?: string;
  serverUrl?: string;
  model?: string;
}

/** Validation result */
export interface ValidationResult {
  valid: boolean;
  provider: {
    id: string;
    name: string;
    testResponse: string;
    latencyMs?: number;
  };
  validatedAt: string;
}

/** Store state interface */
interface LLMProviderState {
  // State
  currentProvider: CurrentProvider | null;
  previousProviderId: string | null;
  availableProviders: Provider[];
  isLoading: boolean;
  isSwitching: boolean;
  switchError: string | null;
  selectedProvider: Provider | null;
  validationInProgress: boolean;

  // Actions
  loadProviders: () => Promise<void>;
  selectProvider: (providerId: string) => void;
  closeConfigModal: () => void;
  switchProvider: (config: SwitchProviderConfig) => Promise<void>;
  validateProvider: (config: SwitchProviderConfig) => Promise<ValidationResult>;
  clearError: () => void;
}

/** Create the LLM Provider store */
export const useLLMProviderStore = create<LLMProviderState>((set, get) => ({
  // Initial state
  currentProvider: null,
  previousProviderId: null,
  availableProviders: [],
  isLoading: false,
  isSwitching: false,
  switchError: null,
  selectedProvider: null,
  validationInProgress: false,

  /** Load all available providers with current provider indicator */
  loadProviders: async () => {
    set({ isLoading: true, switchError: null });

    try {
      const response = await getProviders();
      set({
        currentProvider: response.data.currentProvider,
        availableProviders: response.data.providers,
        isLoading: false,
      });
    } catch (error) {
      set({
        isLoading: false,
        switchError:
          error instanceof Error ? error.message : 'Failed to load providers',
      });
    }
  },

  /** Select a provider for configuration (opens modal) */
  selectProvider: (providerId: string) => {
    const { availableProviders, currentProvider } = get();
    const provider = availableProviders.find((p) => p.id === providerId);

    // Only allow selection if different from current
    if (provider && provider.id !== currentProvider?.id) {
      set({ selectedProvider: provider, switchError: null });
    }
  },

  /** Close configuration modal */
  closeConfigModal: () => {
    set({ selectedProvider: null, switchError: null, validationInProgress: false });
  },

  /** Switch to a new provider with validation */
  switchProvider: async (config: SwitchProviderConfig) => {
    const { currentProvider } = get();
    // Store previous provider ID for success notification
    set({ isSwitching: true, switchError: null, validationInProgress: true, previousProviderId: currentProvider?.id || null });

    try {
      await switchProvider(config);

      // Reload providers to update currentProvider and active indicators
      await get().loadProviders();

      set({
        isSwitching: false,
        selectedProvider: null,
        validationInProgress: false,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to switch provider';
      set({
        isSwitching: false,
        switchError: errorMessage,
        validationInProgress: false,
      });
      throw error; // Re-throw for caller to handle
    }
  },

  /** Validate provider configuration without switching */
  validateProvider: async (config: SwitchProviderConfig) => {
    set({ validationInProgress: true, switchError: null });

    try {
      const response = await validateProviderConfig(config);
      set({ validationInProgress: false });
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Validation failed';
      set({ validationInProgress: false, switchError: errorMessage });
      throw error;
    }
  },

  /** Clear error state */
  clearError: () => {
    set({ switchError: null });
  },
}));
