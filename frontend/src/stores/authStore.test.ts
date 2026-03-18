/**
 * Tests for Authentication Store
 *
 * Story 1.8: Tests for auth state management, login, logout, and token refresh.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthStore, cleanupAuth } from './authStore';
import type { Merchant, LoginRequest } from '../types/auth';

// Mock auth service
vi.mock('../services/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
  refreshToken: vi.fn(),
  setupAuthBroadcast: vi.fn(() => ({
    close: vi.fn(),
    addEventListener: vi.fn(),
  })),
  broadcastLogout: vi.fn(),
  isSessionExpiringSoon: vi.fn(),
}));

import { login as loginApi, logout as logoutApi, getMe as getMeApi, refreshToken as refreshTokenApi } from '../services/auth';

describe('authStore', () => {
  // Sprint Change 2026-02-13: Include store_provider and has_store_connected
  const mockMerchant: Merchant = {
    id: 1,
    email: 'test@example.com',
    merchant_key: 'abc123',
    store_provider: 'none',
    has_store_connected: false,
  };

  const mockSessionExpiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    useAuthStore.getState().reset();
  });

  afterEach(() => {
    cleanupAuth();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useAuthStore.getState();

      expect(state.isAuthenticated).toBe(false);
      expect(state.merchant).toBeNull();
      expect(state.sessionExpiresAt).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('login', () => {
    it('should successfully login and set auth state', async () => {
      // Mock response wrapped in envelope structure (matches backend API)
      const mockLoginResponse = {
        data: {
          merchant: mockMerchant,
          session: { expiresAt: mockSessionExpiresAt },
        },
        meta: { request_id: 'test', timestamp: new Date().toISOString() },
      };

      vi.mocked(loginApi).mockResolvedValueOnce(mockLoginResponse as any);

      const credentials: LoginRequest = {
        email: 'test@example.com',
        password: 'password123',
      };

      await useAuthStore.getState().login(credentials);

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.merchant).toEqual(mockMerchant);
      expect(state.sessionExpiresAt).toBe(mockSessionExpiresAt);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should set error state on login failure', async () => {
      const mockError = new Error('Invalid email or password');
      vi.mocked(loginApi).mockRejectedValueOnce(mockError);

      const credentials: LoginRequest = {
        email: 'test@example.com',
        password: 'wrongpassword',
      };

      await expect(useAuthStore.getState().login(credentials)).rejects.toThrow();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.merchant).toBeNull();
      expect(state.sessionExpiresAt).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Invalid email or password');
    });

    it('should set loading state during login', async () => {
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });

      vi.mocked(loginApi).mockReturnValueOnce(loginPromise as any);

      const credentials: LoginRequest = {
        email: 'test@example.com',
        password: 'password123',
      };

      // Start login (will not resolve yet)
      useAuthStore.getState().login(credentials);

      // Check loading state
      expect(useAuthStore.getState().isLoading).toBe(true);

      // Resolve login with envelope-wrapped response
      resolveLogin!({
        data: {
          merchant: mockMerchant,
          session: { expiresAt: mockSessionExpiresAt },
        },
        meta: { request_id: 'test', timestamp: new Date().toISOString() },
      });

      // Wait for async to complete
      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('should successfully logout and clear auth state', async () => {
      // Set up authenticated state
      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
      });

      vi.mocked(logoutApi).mockResolvedValueOnce(undefined);

      await useAuthStore.getState().logout();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.merchant).toBeNull();
      expect(state.sessionExpiresAt).toBeNull();
      expect(state.isLoading).toBe(false);
    });

    it('should stop refresh timer on logout', async () => {
      // Set up authenticated state with timer
      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
      });

      vi.mocked(logoutApi).mockResolvedValueOnce(undefined);

      await useAuthStore.getState().logout();

      // Timer should be stopped (we can't directly test this,
      // but the state should be cleared)
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe('fetchMe', () => {
    it('should fetch and set merchant info', async () => {
      const mockMeResponse = {
        merchant: mockMerchant,
      };

      vi.mocked(getMeApi).mockResolvedValueOnce(mockMeResponse);

      await useAuthStore.getState().fetchMe();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.merchant).toEqual(mockMerchant);
      expect(state.isLoading).toBe(false);
    });

    it('should clear auth state on fetch failure', async () => {
      // Set up authenticated state
      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
      });

      vi.mocked(getMeApi).mockRejectedValueOnce(new Error('Session invalid'));

      await useAuthStore.getState().fetchMe();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.merchant).toBeNull();
      expect(state.sessionExpiresAt).toBeNull();
      // Note: fetchMe deliberately clears error instead of setting it
      // (it's expected to fail during initial load)
      expect(state.error).toBeNull();
    });
  });

  describe('refreshSession', () => {
    it('should refresh session and update expiration', async () => {
      // Set up authenticated state
      const newExpiresAt = new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString();

      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
      });

      // Mock response wrapped in envelope structure (matches backend API)
      vi.mocked(refreshTokenApi).mockResolvedValueOnce({
        data: {
          session: { expiresAt: newExpiresAt },
        },
        meta: { request_id: 'test', timestamp: new Date().toISOString() },
      } as any);

      await useAuthStore.getState().refreshSession();

      expect(useAuthStore.getState().sessionExpiresAt).toBe(newExpiresAt);
    });

    it('should clear auth state on refresh failure', async () => {
      // Set up authenticated state
      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
      });

      vi.mocked(refreshTokenApi).mockRejectedValueOnce(new Error('Session expired'));

      await useAuthStore.getState().refreshSession();

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().sessionExpiresAt).toBeNull();
    });

    it('should not refresh if not authenticated', async () => {
      // Mock response (shouldn't be called but needs to be set up)
      vi.mocked(refreshTokenApi).mockResolvedValueOnce({
        data: {
          session: { expiresAt: mockSessionExpiresAt },
        },
        meta: { request_id: 'test', timestamp: new Date().toISOString() },
      } as any);

      await useAuthStore.getState().refreshSession();

      // Should not call refresh API
      expect(refreshTokenApi).not.toHaveBeenCalled();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({ error: 'Some error' });

      useAuthStore.getState().clearError();

      expect(useAuthStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset store to initial state', () => {
      useAuthStore.setState({
        isAuthenticated: true,
        merchant: mockMerchant,
        sessionExpiresAt: mockSessionExpiresAt,
        error: 'Some error',
      });

      useAuthStore.getState().reset();

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.merchant).toBeNull();
      expect(state.sessionExpiresAt).toBeNull();
      expect(state.error).toBeNull();
    });
  });

  // Sprint Change 2026-02-13: Store Provider Tests
  describe('store connection helpers', () => {
    describe('hasStoreConnected', () => {
      it('should return false when merchant is null', () => {
        useAuthStore.setState({ merchant: null });

        expect(useAuthStore.getState().hasStoreConnected()).toBe(false);
      });

      it('should return false when store_provider is none', () => {
        const merchantNoStore: Merchant = {
          ...mockMerchant,
          store_provider: 'none',
          has_store_connected: false,
        };
        useAuthStore.setState({ merchant: merchantNoStore });

        expect(useAuthStore.getState().hasStoreConnected()).toBe(false);
      });

      it('should return true when store_provider is shopify', () => {
        const merchantWithStore: Merchant = {
          ...mockMerchant,
          store_provider: 'shopify',
          has_store_connected: true,
        };
        useAuthStore.setState({ merchant: merchantWithStore });

        expect(useAuthStore.getState().hasStoreConnected()).toBe(true);
      });

      it('should return true when store_provider is woocommerce', () => {
        const merchantWithStore: Merchant = {
          ...mockMerchant,
          store_provider: 'woocommerce',
          has_store_connected: true,
        };
        useAuthStore.setState({ merchant: merchantWithStore });

        expect(useAuthStore.getState().hasStoreConnected()).toBe(true);
      });
    });

    describe('storeProvider', () => {
      it('should return "none" when merchant is null', () => {
        useAuthStore.setState({ merchant: null });

        expect(useAuthStore.getState().storeProvider()).toBe('none');
      });

      it('should return "none" when store_provider is none', () => {
        const merchantNoStore: Merchant = {
          ...mockMerchant,
          store_provider: 'none',
          has_store_connected: false,
        };
        useAuthStore.setState({ merchant: merchantNoStore });

        expect(useAuthStore.getState().storeProvider()).toBe('none');
      });

      it('should return "shopify" when store_provider is shopify', () => {
        const merchantWithStore: Merchant = {
          ...mockMerchant,
          store_provider: 'shopify',
          has_store_connected: true,
        };
        useAuthStore.setState({ merchant: merchantWithStore });

        expect(useAuthStore.getState().storeProvider()).toBe('shopify');
      });
    });
  });
});
