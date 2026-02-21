/**
 * Widget Settings Store - Zustand state management
 *
 * Story 5.6: Merchant Widget Settings UI
 *
 * Note: This store manages widget appearance settings only.
 * Bot name is configured via BotConfig page.
 * Welcome message is configured via PersonalityConfig page.
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

const DEFAULT_THEME = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right' as const,
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
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
        enabled: data.enabled ?? true,
        botName: data.botName ?? 'Shopping Assistant',
        welcomeMessage: data.welcomeMessage ?? 'Hi! How can I help you today?',
        theme: {
          ...DEFAULT_THEME,
          ...(data.theme || {}),
        },
        allowedDomains: data.allowedDomains ?? [],
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
        enabled: data.enabled ?? true,
        botName: data.botName ?? 'Shopping Assistant',
        welcomeMessage: data.welcomeMessage ?? 'Hi! How can I help you today?',
        theme: {
          ...DEFAULT_THEME,
          ...(data.theme || {}),
        },
        allowedDomains: data.allowedDomains ?? [],
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
