/**
 * Tests for ProtectedRoute Component
 *
 * Story 1.8: Tests for route protection and auth redirects.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ProtectedRoute } from './ProtectedRoute';
import { useAuthStore, initializeAuth } from '../../stores/authStore';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}));

// Mock auth store
vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
  initializeAuth: vi.fn(),
}));

describe('ProtectedRoute Component', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);
  });

  describe('when authenticated', () => {
    it('should render children', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        merchant: { id: 1, email: 'test@example.com', merchant_key: 'abc123' },
        sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });

    it('should not redirect to login', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        merchant: { id: 1, email: 'test@example.com', merchant_key: 'abc123' },
        sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockNavigate).not.toHaveBeenCalledWith('/login', expect.anything());
      });
    });
  });

  describe('when not authenticated', () => {
    it('should redirect to login after initialization', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        merchant: null,
        sessionExpiresAt: null,
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
      });
    });

    it('should not render children', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        merchant: null,
        sessionExpiresAt: null,
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      const { container } = render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(container.querySelector('div')).toBeNull();
      });
    });
  });

  describe('loading state', () => {
    it('should show loading spinner during initialization', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        merchant: null,
        sessionExpiresAt: null,
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockReturnValue(
        new Promise(() => {}) // Never resolves
      );

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should show loading spinner while fetching auth', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        merchant: null,
        sessionExpiresAt: null,
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.getByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('initialization', () => {
    it('should call initializeAuth on mount', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        merchant: { id: 1, email: 'test@example.com', merchant_key: 'abc123' },
        sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(initializeAuth).toHaveBeenCalledOnce();
      });
    });

    it('should not call initializeAuth if already authenticated', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        merchant: { id: 1, email: 'test@example.com', merchant_key: 'abc123' },
        sessionExpiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        login: vi.fn(),
        logout: vi.fn(),
        fetchMe: vi.fn(),
        refreshSession: vi.fn(),
        clearError: vi.fn(),
        reset: vi.fn(),
        _startRefreshTimer: vi.fn(),
        _stopRefreshTimer: vi.fn(),
        _broadcastChannel: null,
      });

      vi.mocked(initializeAuth).mockResolvedValueOnce(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(initializeAuth).toHaveBeenCalledOnce();
      });
    });
  });
});
