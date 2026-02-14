/**
 * Business Hours Store - Zustand state management for business hours configuration
 *
 * Story 3.10: Business Hours Configuration
 */

import { create } from 'zustand';
import { debounce } from 'lodash-es';
import type { BusinessHoursConfig, DayHours } from '../types/businessHours';
import { DEFAULT_CONFIG } from '../types/businessHours';
import { apiClient } from '../services/api';

interface BusinessHoursState {
  config: BusinessHoursConfig | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  lastSaved: Date | null;

  loadConfig: () => Promise<void>;
  updateConfig: (updates: Partial<BusinessHoursConfig>) => void;
  updateDayHours: (dayIndex: number, hours: Partial<DayHours>) => void;
  reset: () => void;
}

const API_ENDPOINT = '/api/v1/merchant/business-hours';

let debouncedSave: ReturnType<typeof debounce> | null = null;

const getDebouncedSave = () => {
  if (!debouncedSave) {
    debouncedSave = debounce(async (config: BusinessHoursConfig) => {
      try {
        await apiClient.put(API_ENDPOINT, config);

        useBusinessHoursStore.setState({
          saving: false,
          lastSaved: new Date(),
          error: null,
        });
      } catch (error) {
        useBusinessHoursStore.setState({
          saving: false,
          error: error instanceof Error ? error.message : 'Failed to save',
        });
      }
    }, 500);
  }
  return debouncedSave;
};

export const useBusinessHoursStore = create<BusinessHoursState>((set, get) => ({
  config: null,
  loading: false,
  saving: false,
  error: null,
  lastSaved: null,

  loadConfig: async () => {
    set({ loading: true, error: null });

    try {
      const envelope = await apiClient.get(API_ENDPOINT);
      const data = envelope.data || {};

      set({
        config: {
          timezone: data.timezone || DEFAULT_CONFIG.timezone,
          hours: data.hours || [],
          outOfOfficeMessage: data.outOfOfficeMessage || data.out_of_office_message || DEFAULT_CONFIG.outOfOfficeMessage,
          formattedHours: data.formattedHours || data.formatted_hours || '',
        },
        loading: false,
      });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load business hours',
      });
    }
  },

  updateConfig: (updates) => {
    const { config } = get();
    if (!config) return;

    const newConfig = { ...config, ...updates };
    set({ config: newConfig, saving: true });
    getDebouncedSave()(newConfig);
  },

  updateDayHours: (dayIndex, hours) => {
    const { config } = get();
    if (!config) return;

    const newHours = [...config.hours];
    newHours[dayIndex] = { ...newHours[dayIndex], ...hours };

    const newConfig = { ...config, hours: newHours };
    set({ config: newConfig, saving: true });
    getDebouncedSave()(newConfig);
  },

  reset: () => {
    if (debouncedSave) {
      debouncedSave.cancel();
    }
    set({
      config: null,
      loading: false,
      saving: false,
      error: null,
      lastSaved: null,
    });
  },
}));

export function _clearDebouncedSave() {
  if (debouncedSave) {
    debouncedSave.cancel();
    debouncedSave = null;
  }
}
