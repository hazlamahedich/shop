/**
 * SessionExpiryWarning Component Tests
 *
 * Story 1.8: Tests for session expiry warning component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SessionExpiryWarning from './SessionExpiryWarning';

// Mock the auth store
const mockRefreshSession = vi.fn();
const mockLogout = vi.fn();

vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    sessionExpiresAt: null,
    refreshSession: mockRefreshSession,
    logout: mockLogout,
    isAuthenticated: true,
  })),
}));

// Mock the auth service
const mockGetTimeUntilExpiration = vi.fn();
const mockIsSessionExpiringSoon = vi.fn();

vi.mock('../../services/auth', () => ({
  getTimeUntilExpiration: () => mockGetTimeUntilExpiration(),
  isSessionExpiringSoon: () => mockIsSessionExpiringSoon(),
}));

describe('SessionExpiryWarning', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Visibility', () => {
    it('should not show warning when user is not authenticated', () => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        isAuthenticated: false,
        sessionExpiresAt: null,
        refreshSession: mockRefreshSession,
        logout: mockLogout,
      });

      render(<SessionExpiryWarning />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should not show warning when session is not expiring soon', () => {
      mockIsSessionExpiringSoon.mockReturnValue(false);

      render(<SessionExpiryWarning />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should show warning when session is expiring soon', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000); // 4 minutes

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });
  });

  describe('Time Display', () => {
    it('should display remaining time correctly', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(2 * 60 * 1000 + 30 * 1000); // 2:30

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByText(/will expire in 2:30/i)).toBeInTheDocument();
      });
    });

    it('should format seconds with leading zero', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(1 * 60 * 1000 + 5 * 1000); // 1:05

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByText(/will expire in 1:05/i)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Action', () => {
    it('should call refreshSession when refresh button is clicked', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);
      mockRefreshSession.mockResolvedValue(undefined);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const refreshButton = screen.getByLabelText(/refresh session/i);
      await userEvent.click(refreshButton);

      expect(mockRefreshSession).toHaveBeenCalledTimes(1);
    });

    it('should show loading state while refreshing', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);
      let refreshResolver: (value: void) => void;
      mockRefreshSession.mockImplementation(
        () => new Promise((resolve) => (refreshResolver = resolve))
      );

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const refreshButton = screen.getByLabelText(/refresh session/i);
      await userEvent.click(refreshButton);

      expect(await screen.findByText(/refreshing/i)).toBeInTheDocument();

      refreshResolver!();
      await waitFor(() => {
        expect(screen.queryByText(/refreshing/i)).not.toBeInTheDocument();
      });
    });

    it('should hide warning after successful refresh', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);
      mockRefreshSession.mockResolvedValue(undefined);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const refreshButton = screen.getByLabelText(/refresh session/i);
      await userEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Logout Action', () => {
    it('should call logout when logout button is clicked', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);
      mockLogout.mockResolvedValue(undefined);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const logoutButton = screen.getByLabelText(/logout now/i);
      await userEvent.click(logoutButton);

      expect(mockLogout).toHaveBeenCalledTimes(1);
    });

    it('should hide warning after logout', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);
      mockLogout.mockResolvedValue(undefined);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const logoutButton = screen.getByLabelText(/logout now/i);
      await userEvent.click(logoutButton);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Close Action', () => {
    it('should hide warning when close button is clicked', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const closeButton = screen.getByLabelText(/close warning/i);
      await userEvent.click(closeButton);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Auto-logout', () => {
    it('should auto logout when session expires', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(false); // Not expiring soon
      mockGetTimeUntilExpiration.mockReturnValue(0); // Expired
      mockLogout.mockResolvedValue(undefined);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert).toHaveAttribute('aria-live', 'polite');
        expect(alert).toHaveAttribute('aria-atomic', 'true');
      });
    });

    it('should have accessible button labels', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(4 * 60 * 1000);

      render(<SessionExpiryWarning />);

      await waitFor(() => {
        expect(screen.getByLabelText(/refresh session/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/logout now/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/close warning/i)).toBeInTheDocument();
      });
    });
  });

  describe('Custom Thresholds', () => {
    it('should use custom warning threshold', async () => {
      mockIsSessionExpiringSoon.mockReturnValue(true);
      mockGetTimeUntilExpiration.mockReturnValue(9 * 60 * 1000); // 9 minutes

      render(<SessionExpiryWarning warningThreshold={10 * 60 * 1000} />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('should use custom check interval', () => {
      mockIsSessionExpiringSoon.mockReturnValue(false);
      mockGetTimeUntilExpiration.mockReturnValue(60 * 60 * 1000);

      const setIntervalSpy = vi.spyOn(global, 'setInterval');

      render(<SessionExpiryWarning checkInterval={60 * 1000} />);

      expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 60 * 1000);

      setIntervalSpy.mockRestore();
    });
  });
});
