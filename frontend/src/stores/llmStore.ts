import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LLMProvider, LLMStatus } from '../types/enums';

export interface LLMConfiguration {
  provider: LLMProvider | null;
  ollamaUrl?: string;
  ollamaModel?: string;
  cloudModel?: string;
  status: LLMStatus;
  error?: string;
  configuredAt?: string;
  lastTestAt?: string;
  testResult?: {
    success: boolean;
    latency_ms?: number;
    tokens_used?: number;
    tested_at?: string;
  };
  backupProvider?: string;
  totalTokensUsed?: number;
  totalCostUsd?: number;
}

export interface LLMProviderInfo {
  id: string;
  name: string;
  description: string;
  pricing: {
    inputCost: number;
    outputCost: number;
    currency: string;
  };
  models: string[];
  features: string[];
}

interface LLMState {
  configuration: LLMConfiguration;
  providers: LLMProviderInfo[];
  isConfiguring: boolean;
  isTesting: boolean;

  // Actions
  setConfiguration: (config: Partial<LLMConfiguration>) => void;
  configureLLM: (provider: string, config: any) => Promise<void>;
  getLLMStatus: () => Promise<void>;
  testLLM: (testPrompt: string) => Promise<void>;
  updateLLM: (updates: any) => Promise<void>;
  clearLLM: () => Promise<void>;
  getProviders: () => Promise<void>;
  getHealth: () => Promise<void>;
}

const API_BASE = '/api/llm';

export const useLLMStore = create<LLMState>()(
  persist(
    (set, get) => ({
      configuration: {
        provider: null,
        status: 'pending',
      },
      providers: [],
      isConfiguring: false,
      isTesting: false,

      setConfiguration: (config) => set((state) => ({
        configuration: { ...state.configuration, ...config },
      })),

      configureLLM: async (provider, config) => {
        set({ isConfiguring: true, error: undefined });
        try {
          const response = await fetch(`${API_BASE}/configure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              provider,
              ...(provider === 'ollama'
                ? { ollama_config: config }
                : { cloud_config: { ...config, provider } }
              ),
              ...(config.backupProvider ? { backup_provider: config.backupProvider } : {}),
            }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Configuration failed');
          }

          await get().getLLMStatus();
        } catch (error) {
          set({ error: (error as Error).message, isConfiguring: false });
          throw error;
        } finally {
          set({ isConfiguring: false });
        }
      },

      getLLMStatus: async () => {
        try {
          const response = await fetch(`${API_BASE}/status`);

          if (!response.ok) {
            // Not configured is expected state
            if (response.status === 404) {
              set({ configuration: { provider: null, status: 'pending' } });
              return;
            }
            throw new Error('Failed to get LLM status');
          }

          const data = await response.json();
          set({ configuration: data.data });
        } catch (error) {
          console.error('Error getting LLM status:', error);
        }
      },

      testLLM: async (testPrompt) => {
        set({ isTesting: true, error: undefined });
        try {
          const response = await fetch(`${API_BASE}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test_prompt: testPrompt }),
          });

          const data = await response.json();
          set({ configuration: { ...get().configuration, testResult: data.data } });
        } catch (error) {
          set({ error: (error as Error).message, isTesting: false });
          throw error;
        } finally {
          set({ isTesting: false });
        }
      },

      updateLLM: async (updates) => {
        try {
          const response = await fetch(`${API_BASE}/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail || 'Update failed');
          }

          await get().getLLMStatus();
        } catch (error) {
          set({ error: (error as Error).message });
          throw error;
        }
      },

      clearLLM: async () => {
        try {
          const response = await fetch(`${API_BASE}/clear`, {
            method: 'DELETE',
          });

          if (!response.ok) {
            throw new Error('Clear failed');
          }

          set({ configuration: { provider: null, status: 'pending' } });
        } catch (error) {
          set({ error: (error as Error).message });
          throw error;
        }
      },

      getProviders: async () => {
        try {
          const response = await fetch(`${API_BASE}/providers`);
          const data = await response.json();
          set({ providers: data.data.providers });
        } catch (error) {
          console.error('Error getting providers:', error);
        }
      },

      getHealth: async () => {
        try {
          const response = await fetch(`${API_BASE}/health`);
          const data = await response.json();
          return data.data;
        } catch (error) {
          console.error('Error getting health:', error);
          return { router: 'error' };
        }
      },
    }),
    {
      name: 'llm-storage',
    }
  )
);
