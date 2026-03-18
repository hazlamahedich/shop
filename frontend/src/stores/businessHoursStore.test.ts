/**
 * Business Hours Store Tests
 *
 * Story 3.10: Business Hours Configuration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useBusinessHoursStore, _clearDebouncedSave } from './businessHoursStore';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('businessHoursStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
    useBusinessHoursStore.getState().reset();
    _clearDebouncedSave();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('loadConfig', () => {
    it('loads config from API', async () => {
      const mockConfig = {
        timezone: 'America/New_York',
        hours: [{ day: 'mon', isOpen: true, openTime: '09:00', closeTime: '17:00' }],
        outOfOfficeMessage: 'Closed',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: mockConfig }),
      });

      await act(async () => {
        await useBusinessHoursStore.getState().loadConfig();
      });

      const state = useBusinessHoursStore.getState();
      expect(state.config?.timezone).toBe('America/New_York');
      expect(state.loading).toBe(false);
    });

    it('sets error on failed load', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await act(async () => {
        await useBusinessHoursStore.getState().loadConfig();
      });

      const state = useBusinessHoursStore.getState();
      expect(state.error).toBeTruthy();
      expect(state.loading).toBe(false);
    });
  });

  describe('updateConfig', () => {
    it('updates config and triggers save', async () => {
      vi.useFakeTimers();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: {} }),
      });

      useBusinessHoursStore.setState({
        config: {
          timezone: 'America/Los_Angeles',
          hours: [],
          outOfOfficeMessage: 'Test',
        },
      });

      act(() => {
        useBusinessHoursStore.getState().updateConfig({ timezone: 'Europe/London' });
      });

      const state = useBusinessHoursStore.getState();
      expect(state.config?.timezone).toBe('Europe/London');
      expect(state.saving).toBe(true);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/merchant/business-hours',
        expect.objectContaining({ method: 'PUT' })
      );

      vi.useRealTimers();
    });
  });

  describe('updateDayHours', () => {
    it('updates specific day hours', () => {
      useBusinessHoursStore.setState({
        config: {
          timezone: 'America/Los_Angeles',
          hours: [
            { day: 'mon', isOpen: true, openTime: '09:00', closeTime: '17:00' },
            { day: 'tue', isOpen: true, openTime: '09:00', closeTime: '17:00' },
          ],
          outOfOfficeMessage: 'Test',
        },
      });

      act(() => {
        useBusinessHoursStore.getState().updateDayHours(0, { isOpen: false });
      });

      const state = useBusinessHoursStore.getState();
      expect(state.config?.hours[0].isOpen).toBe(false);
      expect(state.config?.hours[1].isOpen).toBe(true);
    });
  });

  describe('reset', () => {
    it('clears all state', () => {
      useBusinessHoursStore.setState({
        config: { timezone: 'UTC', hours: [], outOfOfficeMessage: 'Test' },
        loading: true,
        saving: true,
        error: 'Error',
        lastSaved: new Date(),
      });

      act(() => {
        useBusinessHoursStore.getState().reset();
      });

      const state = useBusinessHoursStore.getState();
      expect(state.config).toBeNull();
      expect(state.loading).toBe(false);
      expect(state.saving).toBe(false);
      expect(state.error).toBeNull();
      expect(state.lastSaved).toBeNull();
    });
  });
});
