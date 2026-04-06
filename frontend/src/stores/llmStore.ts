import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { LLMProvider, LLMStatus } from '../types/enums';
import { csrfManager } from '../services/csrf';

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
  providers: Array<LLMProviderInfo>;
  isConfiguring: boolean;
  isTesting: boolean;
  error?: string;

  setConfiguration: (config: Partial<LLMConfiguration>) => void;
  configureLLM: (provider: string, config: any) => Promise<void>;
  getLLMStatus: () => Promise<void>;
  testLLM: (testPrompt: string) => Promise<void>;
  updateLLM: (updates: any) => Promise<void>;
  clearLLM: () => Promise<void>;
  getProviders: () => Promise<void>;
  getHealth: () => Promise<void>;
  switchProvider: (providerId: string, apiKey: string, model?: string) => Promise<void>;
}

const API_BASE = '/api/llm';

function getDevMerchantId(): string {
  try {
    const stored = localStorage.getItem('shop_auth_state');
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed?.merchant?.id) {
        return String(parsed.merchant.id);
      }
    }
  } catch {
    // Ignore parse errors
  }
  return import.meta.env?.VITE_MERCHANT_ID || '1';
}

function getHeaders(csrfToken?: string): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-Merchant-Id': getDevMerchantId(),
  };
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }
  return headers;
}

function parseError(data: any): string {
  if (typeof data.detail === 'string') {
    return data.detail;
  }
  if (data.detail?.error) {
    return data.detail.error;
  }
  if (data.message) {
    return data.message;
  }
  return 'An error occurred';
}

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
          const csrfToken = await csrfManager.getToken();
          const response = await fetch(`${API_BASE}/configure`, {
            method: 'POST',
            headers: getHeaders(csrfToken),
            credentials: 'include',
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
            throw new Error(parseError(data));
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
          const response = await fetch(`${API_BASE}/status`, {
            headers: getHeaders(),
            credentials: 'include',
          });

          if (!response.ok) {
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
          const csrfToken = await csrfManager.getToken();
          const response = await fetch(`${API_BASE}/test`, {
            method: 'POST',
            headers: getHeaders(csrfToken),
            credentials: 'include',
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
          const csrfToken = await csrfManager.getToken();
          const response = await fetch(`${API_BASE}/update`, {
            method: 'PUT',
            headers: getHeaders(csrfToken),
            credentials: 'include',
            body: JSON.stringify(updates),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(parseError(data));
          }

          await get().getLLMStatus();
        } catch (error) {
          set({ error: (error as Error).message });
          throw error;
        }
      },

      clearLLM: async () => {
        try {
          const csrfToken = await csrfManager.getToken();
          const response = await fetch(`${API_BASE}/clear`, {
            method: 'DELETE',
            headers: getHeaders(csrfToken),
            credentials: 'include',
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
          const response = await fetch(`${API_BASE}/providers`, {
            headers: getHeaders(),
            credentials: 'include',
          });
          const data = await response.json();
          set({ providers: data.data.providers });
        } catch (error) {
          console.error('Error getting providers:', error);
        }
      },

      getHealth: async () => {
        try {
          const response = await fetch(`${API_BASE}/health`, {
            headers: getHeaders(),
            credentials: 'include',
          });
          const data = await response.json();
          return data.data;
        } catch (error) {
          console.error('Error getting health:', error);
          return { router: 'error' };
        }
      },

      switchProvider: async (providerId: string, apiKey: string, model?: string) => {
        set({ isConfiguring: true });
        try {
          const csrfToken = await csrfManager.getToken();
          const response = await fetch(`${API_BASE}/switch-provider`, {
            method: 'POST',
            headers: getHeaders(csrfToken),
            credentials: 'include',
            body: JSON.stringify({
              provider_id: providerId,
              api_key: apiKey,
              model: model,
            }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(parseError(data));
          }

          await get().getLLMStatus();
        } catch (error) {
          set({ error: (error as Error).message });
          throw error;
        } finally {
          set({ isConfiguring: false });
        }
      },
    }),
    {
      name: 'llm-storage',
    }
  )
);
