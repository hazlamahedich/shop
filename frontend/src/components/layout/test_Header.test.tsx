/**
 * Header Component Tests
 *
 * Story 1.8: Tests for header with merchant info and logout functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Header from './Header';

// Mock the auth store
const mockLogout = vi.fn();
const mockNavigate = vi.fn();

vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    merchant: null,
    logout: mockLogout,
    isAuthenticated: false,
  })),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Merchant Info Display', () => {
    it('should not show merchant info when not authenticated', () => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        merchant: null,
        logout: mockLogout,
        isAuthenticated: false,
      });

      render(<Header />);

      expect(screen.queryByLabelText(/logged in as/i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/logout options/i)).not.toBeInTheDocument();
    });

    it('should display merchant email when authenticated', () => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        merchant: { id: 1, email: 'merchant@example.com', merchant_key: 'abc123' },
        logout: mockLogout,
        isAuthenticated: true,
      });

      render(<Header />);

      const merchantInfo = screen.getByLabelText(/logged in as/i);
      expect(merchantInfo).toBeInTheDocument();
      expect(merchantInfo).toHaveTextContent('merchant@example.com');
    });

    it('should show logout button when authenticated', () => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        merchant: { id: 1, email: 'merchant@example.com', merchant_key: 'abc123' },
        logout: mockLogout,
        isAuthenticated: true,
      });

      render(<Header />);

      expect(screen.getByLabelText(/logout options/i)).toBeInTheDocument();
    });
  });

  describe('Logout Flow', () => {
    beforeEach(() => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        merchant: { id: 1, email: 'merchant@example.com', merchant_key: 'abc123' },
        logout: mockLogout,
        isAuthenticated: true,
      });
    });

    it('should show confirmation dialog when logout button is clicked', async () => {
      render(<Header />);

      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/are you sure you want to logout/i)).toBeInTheDocument();
    });

    it('should call logout and navigate when confirmed', async () => {
      mockLogout.mockResolvedValue(undefined);

      render(<Header />);

      // Click logout button
      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      // Click confirm in dialog
      const confirmButton = screen.getByRole('button', { name: /^logout$/i });
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalledTimes(1);
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });

    it('should close dialog when cancelled', async () => {
      render(<Header />);

      // Click logout button
      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      await userEvent.click(cancelButton);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      expect(mockLogout).not.toHaveBeenCalled();
    });

    it('should show loading state while logging out', async () => {
      let logoutResolver: (value: void) => void;
      mockLogout.mockImplementation(
        () => new Promise((resolve) => (logoutResolver = resolve))
      );

      render(<Header />);

      // Click logout button
      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      // Click confirm
      const confirmButton = screen.getByRole('button', { name: /^logout$/i });
      await userEvent.click(confirmButton);

      // Check for loading state
      expect(await screen.findByText(/logging out/i)).toBeInTheDocument();

      // Resolve logout
      logoutResolver!();

      await waitFor(() => {
        expect(screen.queryByText(/logging out/i)).not.toBeInTheDocument();
      });
    });

    it('should navigate to login even if logout API fails', async () => {
      mockLogout.mockRejectedValue(new Error('Logout failed'));

      render(<Header />);

      // Click logout button
      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      // Click confirm
      const confirmButton = screen.getByRole('button', { name: /^logout$/i });
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalledTimes(1);
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      vi.mocked(
        require('../../stores/authStore').useAuthStore
      ).mockReturnValue({
        merchant: { id: 1, email: 'merchant@example.com', merchant_key: 'abc123' },
        logout: mockLogout,
        isAuthenticated: true,
      });
    });

    it('should have proper ARIA labels', () => {
      render(<Header />);

      expect(screen.getByLabelText(/logged in as/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/logout options/i)).toBeInTheDocument();
      expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
    });

    it('should set aria-expanded on logout button when dialog is open', async () => {
      render(<Header />);

      const logoutButton = screen.getByLabelText(/logout options/i);
      expect(logoutButton).toHaveAttribute('aria-expanded', 'false');

      await userEvent.click(logoutButton);

      expect(logoutButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('should have proper dialog ARIA attributes', async () => {
      render(<Header />);

      const logoutButton = screen.getByLabelText(/logout options/i);
      await userEvent.click(logoutButton);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'logout-dialog-title');
      expect(dialog).toHaveAttribute('aria-describedby', 'logout-dialog-description');
    });
  });

  describe('Navigation Elements', () => {
    it('should render search input', () => {
      render(<Header />);

      expect(screen.getByLabelText('Search')).toBeInTheDocument();
    });

    it('should render notification bell', () => {
      render(<Header />);

      expect(screen.getByLabelText('Notifications')).toBeInTheDocument();
    });

    it('should show notification indicator', () => {
      render(<Header />);

      const bell = screen.getByLabelText('Notifications');
      const indicator = within(bell).querySelector('.bg-red-500');
      expect(indicator).toBeInTheDocument();
    });
  });
});
