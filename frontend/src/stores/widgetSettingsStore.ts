/**
 * Widget Settings Store - Zustand state management
 *
 * Story 5.6: Merchant Widget Settings UI
 */

import { create } from 'zustand';
import type { WidgetConfig } from '../widget/types/widget';
import { apiClient } from '../services/api';

interface PartialWidgetTheme {
  primaryColor?: string;
  position?: 'bottom-right' | 'bottom-left';
}

interface WidgetConfigUpdateRequest {
  enabled?: boolean;
  botName?: string;
  welcomeMessage?: string;
  theme?: PartialWidgetTheme;
}

interface WidgetSettingsState {
  config: WidgetConfig | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  hasUnsavedChanges: boolean;

  fetchConfig: () => Promise<void>;
  updateConfig: (updates: WidgetConfigUpdateRequest) => Promise<void>;
  setConfig: (config: Partial<WidgetConfig>) => void;
  markDirty: () => void;
  resetDirty: () => void;
  reset: () => void;
}

const API_ENDPOINT = '/api/v1/merchants/widget-config';

const DEFAULT_CONFIG: WidgetConfig = {
  enabled: true,
  botName: 'Shopping Assistant',
  welcomeMessage: 'Hi! How can I help you today?',
  theme: {
    primaryColor: '#6366f1',
    backgroundColor: '#ffffff',
    textColor: '#1f2937',
    botBubbleColor: '#f3f4f6',
    userBubbleColor: '#6366f1',
    position: 'bottom-right',
    borderRadius: 16,
    width: 380,
    height: 600,
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  allowedDomains: [],
};

export const useWidgetSettingsStore = create<WidgetSettingsState>((set, get) => ({
  config: null,
  loading: false,
  saving: false,
  error: null,
  hasUnsavedChanges: false,

  fetchConfig: async () => {
    set({ loading: true, error: null });

    try {
      const envelope = await apiClient.get<WidgetConfig>(API_ENDPOINT);
      const data = envelope.data;

      const config: WidgetConfig = {
        enabled: data.enabled ?? DEFAULT_CONFIG.enabled,
        botName: data.botName ?? DEFAULT_CONFIG.botName,
        welcomeMessage: data.welcomeMessage ?? DEFAULT_CONFIG.welcomeMessage,
        theme: {
          ...DEFAULT_CONFIG.theme,
          ...(data.theme || {}),
        },
        allowedDomains: data.allowedDomains ?? DEFAULT_CONFIG.allowedDomains,
      };

      set({ config, loading: false, hasUnsavedChanges: false });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load widget settings',
      });
    }
  },

  updateConfig: async (updates: WidgetConfigUpdateRequest) => {
    set({ saving: true, error: null });

    try {
      const envelope = await apiClient.patch<WidgetConfig>(API_ENDPOINT, updates);
      const data = envelope.data;

      const config: WidgetConfig = {
        enabled: data.enabled ?? DEFAULT_CONFIG.enabled,
        botName: data.botName ?? DEFAULT_CONFIG.botName,
        welcomeMessage: data.welcomeMessage ?? DEFAULT_CONFIG.welcomeMessage,
        theme: {
          ...DEFAULT_CONFIG.theme,
          ...(data.theme || {}),
        },
        allowedDomains: data.allowedDomains ?? DEFAULT_CONFIG.allowedDomains,
      };

      set({ config, saving: false, hasUnsavedChanges: false });
    } catch (error) {
      set({
        saving: false,
        error: error instanceof Error ? error.message : 'Failed to save widget settings',
      });
      throw error;
    }
  },

  setConfig: (updates: Partial<WidgetConfig>) => {
    const { config } = get();
    if (!config) return;

    set({
      config: { ...config, ...updates },
      hasUnsavedChanges: true,
    });
  },

  markDirty: () => {
    set({ hasUnsavedChanges: true });
  },

  resetDirty: () => {
    set({ hasUnsavedChanges: false });
  },

  reset: () => {
    set({
      config: null,
      loading: false,
      saving: false,
      error: null,
      hasUnsavedChanges: false,
    });
  },
}));
