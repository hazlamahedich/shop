/**
 * BusinessHoursConfig Component Tests
 *
 * Story 3.10: Business Hours Configuration
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BusinessHoursConfig } from './BusinessHoursConfig';
import { useBusinessHoursStore } from '@/stores/businessHoursStore';

vi.mock('@/stores/businessHoursStore', () => ({
  useBusinessHoursStore: vi.fn(),
}));

const mockUseBusinessHoursStore = vi.mocked(useBusinessHoursStore);

const mockStore = {
  config: {
    timezone: 'America/Los_Angeles',
    hours: [
      { day: 'mon', isOpen: true, openTime: '09:00', closeTime: '17:00' },
      { day: 'tue', isOpen: true, openTime: '09:00', closeTime: '17:00' },
      { day: 'wed', isOpen: true, openTime: '09:00', closeTime: '17:00' },
      { day: 'thu', isOpen: true, openTime: '09:00', closeTime: '17:00' },
      { day: 'fri', isOpen: true, openTime: '09:00', closeTime: '17:00' },
      { day: 'sat', isOpen: false },
      { day: 'sun', isOpen: false },
    ],
    outOfOfficeMessage: 'Our team is offline.',
    formattedHours: '9:00 AM - 5:00 PM, Mon-Fri',
  },
  loading: false,
  saving: false,
  error: null,
  lastSaved: null,
  loadConfig: vi.fn().mockResolvedValue(undefined),
  updateConfig: vi.fn(),
  updateDayHours: vi.fn(),
};

const emptyStore = {
  config: null,
  loading: false,
  saving: false,
  error: null,
  lastSaved: null,
  loadConfig: vi.fn().mockResolvedValue(undefined),
  updateConfig: vi.fn(),
  updateDayHours: vi.fn(),
};

describe('BusinessHoursConfig', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('when loading', () => {
    it('shows loading state', () => {
      mockUseBusinessHoursStore.mockImplementation((selector) => {
        if (typeof selector === 'function') {
          return selector({ ...emptyStore, loading: true });
        }
        return { ...emptyStore, loading: true };
      });

      render(<BusinessHoursConfig />);
      expect(screen.getByText('Loading business hours...')).toBeInTheDocument();
    });
  });

  describe('when no config', () => {
    it('shows initialization option', () => {
      mockUseBusinessHoursStore.mockImplementation((selector) => {
        if (typeof selector === 'function') {
          return selector(emptyStore);
        }
        return emptyStore;
      });

      render(<BusinessHoursConfig />);
      expect(screen.getByText('No business hours configured yet.')).toBeInTheDocument();
      expect(screen.getByText('Set Default Hours (Mon-Fri 9 AM - 5 PM)')).toBeInTheDocument();
    });
  });

  describe('with config', () => {
    beforeEach(() => {
      mockUseBusinessHoursStore.mockImplementation((selector) => {
        if (typeof selector === 'function') {
          return selector(mockStore);
        }
        return mockStore;
      });
    });

    it('renders the component with title', () => {
      render(<BusinessHoursConfig />);
      expect(screen.getByText('Business Hours')).toBeInTheDocument();
    });

    it('shows day rows', () => {
      render(<BusinessHoursConfig />);
      expect(screen.getByText('Monday')).toBeInTheDocument();
      expect(screen.getByText('Tuesday')).toBeInTheDocument();
      expect(screen.getByText('Friday')).toBeInTheDocument();
      expect(screen.getByText('Saturday')).toBeInTheDocument();
    });

    it('shows out of office message textarea with default value', () => {
      render(<BusinessHoursConfig />);
      const textarea = screen.getByDisplayValue('Our team is offline.');
      expect(textarea).toBeInTheDocument();
    });

    it('calls loadConfig on mount', () => {
      render(<BusinessHoursConfig />);
      expect(mockStore.loadConfig).toHaveBeenCalled();
    });
  });
});
