/**
 * Zustand Store for Authentication
 *
 * Story 1.8: Manages authentication state, login/logout, and session refresh.
 *
 * Features:
 * - Login with email/password
 * - Logout with session invalidation
 * - Get current merchant info
 * - Token refresh at 50% of session lifetime
 * - Multi-tab sync via BroadcastChannel (single instance)
 * - Auto-refresh token before expiration
 *
 * Note: Uses httpOnly cookies for session storage (no sessionStorage tokens needed).
 * sessionStorage is only used for page refresh persistence within same tab.
 */

import { create } from 'zustand';
import {
  login as loginApi,
  logout as logoutApi,
  getMe as getMeApi,
  refreshToken as refreshTokenApi,
  broadcastLogout,
  isSessionExpiringSoon,
} from '../services/auth';
import type {
  Merchant,
  AuthState,
  LoginRequest,
} from '../types/auth';

// Session duration is 24 hours from backend
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000;
// Refresh token at 50% of session lifetime (12 hours)
const REFRESH_THRESHOLD_MS = SESSION_DURATION_MS * 0.5;
// Check interval for token refresh (every 5 minutes)
const REFRESH_CHECK_INTERVAL_MS = 5 * 60 * 1000;

// Global BroadcastChannel for multi-tab logout sync (MEDIUM-7: single instance)
let globalBroadcastChannel: BroadcastChannel | null = null;

export interface AuthStore extends AuthState {
  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  refreshSession: () => Promise<void>;
  clearError: () => void;
  reset: () => void;
  // Internal
  _startRefreshTimer: () => void;
  _stopRefreshTimer: () => void;
  _broadcastChannel: BroadcastChannel | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  merchant: null,
  sessionExpiresAt: null,
  isLoading: false,
  error: null,
};

/**
 * Create auth store with Zustand.
 * Uses in-memory state only (no persistence for security).
 */
export const useAuthStore = create<AuthStore>((set, get) => {
  let refreshTimerId: ReturnType<typeof setInterval> | null = null;

  // Initialize from sessionStorage if available (for session persistence within tab)
  // Using sessionStorage instead of localStorage to avoid cross-tab state conflicts
  const storedAuth = sessionStorage.getItem('auth_state');
  const initialStateWithStorage = storedAuth ? JSON.parse(storedAuth) : initialState;

  return {
    ...initialStateWithStorage,
    _broadcastChannel: null,

    /**
     * Login with email and password.
     *
     * Rate limited: 5 attempts per 15 minutes per IP/email.
     * Session rotation: Invalidates old sessions.
     */
    login: async (credentials: LoginRequest) => {
      set({ isLoading: true, error: null });

      try {
        const response = await loginApi(credentials);

        const authState = {
          isAuthenticated: true,
          merchant: response.data.merchant,
          sessionExpiresAt: response.data.session.expiresAt,
          isLoading: false,
          error: null,
        };

        set(authState);

        // Save to sessionStorage for session persistence (LOW-14: updated comment)
        sessionStorage.setItem('auth_state', JSON.stringify(authState));

        // Start auto-refresh timer
        get()._startRefreshTimer();
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Login failed';
        set({
          isAuthenticated: false,
          merchant: null,
          sessionExpiresAt: null,
          isLoading: false,
          error: errorMessage,
        });
        throw error;
      }
    },

    /**
     * Logout merchant and invalidate session.
     *
     * Clears session cookie, revokes session in database,
     * and notifies other tabs via BroadcastChannel.
     */
    logout: async () => {
      set({ isLoading: true, error: null });

      try {
        // Stop refresh timer
        get()._stopRefreshTimer();

        // Call logout API
        await logoutApi();

        // Clear auth state
        const authState = {
          isAuthenticated: false,
          merchant: null,
          sessionExpiresAt: null,
          isLoading: false,
          error: null,
        };
        set(authState);

        // Clear sessionStorage (LOW-14: updated comment)
        sessionStorage.removeItem('auth_state');

        // Notify other tabs via global BroadcastChannel
        broadcastLogout();
      } catch (error) {
        set({ isLoading: false, error: 'Logout failed' });
        // Continue with client-side logout even if API fails
        // Clear sessionStorage on error too (LOW-14: updated comment)
        sessionStorage.removeItem('auth_state');
      }
    },

    /**
     * Get current authenticated merchant info.
     *
     * Validates JWT token and checks session is not revoked.
     */
    fetchMe: async () => {
      set({ isLoading: true, error: null });

      try {
        console.log('fetchMe: Calling getMeApi...');
        const response = await getMeApi();
        console.log('fetchMe: Success', response);

        const authState = {
          isAuthenticated: true,
          merchant: response.merchant,
          sessionExpiresAt: null, // /me endpoint doesn't return session info
          isLoading: false,
          error: null,
        };

        set(authState);

        // Save to sessionStorage for session persistence (LOW-14: updated comment)
        sessionStorage.setItem('auth_state', JSON.stringify(authState));

        // Start refresh timer if not already running
        if (!refreshTimerId) {
          get()._startRefreshTimer();
        }
      } catch (error) {
        console.error('fetchMe: Error', error);
        // Don't set error state on fetchMe failure - it's expected during initial load
        set({
          isAuthenticated: false,
          merchant: null,
          sessionExpiresAt: null,
          isLoading: false,
          error: null, // Clear error instead of showing "Session invalid"
        });
        // Clear sessionStorage on fetchMe failure (LOW-14: updated comment)
        sessionStorage.removeItem('auth_state');
        get()._stopRefreshTimer();
      }
    },

    /**
     * Refresh JWT token (extends session).
     *
     * Should be called at 50% of session lifetime (12 hours).
     * This is called automatically by the refresh timer.
     */
    refreshSession: async () => {
      const state = get();
      if (!state.isAuthenticated) return;

      try {
        const response = await refreshTokenApi();

        set({
          sessionExpiresAt: response.data.session.expiresAt,
          error: null,
        });
      } catch (error) {
        // Token refresh failed - session is invalid
        set({
          isAuthenticated: false,
          merchant: null,
          sessionExpiresAt: null,
          error: 'Session expired',
        });
        get()._stopRefreshTimer();
      }
    },

    /**
     * Clear error state.
     */
    clearError: () => {
      set({ error: null });
    },

    /**
     * Reset store to initial state.
     */
    reset: () => {
      get()._stopRefreshTimer();
      set({
        ...initialState,
        _broadcastChannel: null,
      });
    },

    /**
     * Start automatic token refresh timer.
     *
     * Checks every 5 minutes if token needs refresh.
     * Refreshes at 50% of session lifetime (12 hours).
     * @internal
     */
    _startRefreshTimer: () => {
      // Clear existing timer if any
      get()._stopRefreshTimer();

      refreshTimerId = setInterval(async () => {
        const state = get();

        // Check if session is expiring soon
        if (
          state.isAuthenticated &&
          state.sessionExpiresAt &&
          isSessionExpiringSoon(state.sessionExpiresAt, REFRESH_THRESHOLD_MS)
        ) {
          console.info('Token expiring soon, refreshing...');
          await get().refreshSession();
        }
      }, REFRESH_CHECK_INTERVAL_MS);
    },

    /**
     * Stop automatic token refresh timer.
     * @internal
     */
    _stopRefreshTimer: () => {
      if (refreshTimerId) {
        clearInterval(refreshTimerId);
        refreshTimerId = null;
      }
    },
  };
});

/**
 * Initialize auth store on app load.
 *
 * Checks if user is already authenticated via /auth/me.
 * This runs once on app initialization.
 * Also sets up global BroadcastChannel listener for multi-tab logout sync (MEDIUM-7).
 */
export const initializeAuth = async (): Promise<boolean> => {
  const store = useAuthStore.getState();

  // Setup global BroadcastChannel listener for multi-tab logout sync (MEDIUM-7: single instance)
  // This should be set up once when the app initializes, not per-component
  if (!globalBroadcastChannel) {
    globalBroadcastChannel = new BroadcastChannel('auth-channel');

    globalBroadcastChannel.addEventListener('message', (event) => {
      if (event.data.type === 'LOGOUT') {
        // Clear auth state when logout is broadcast from another tab
        store.reset();
        // Clear sessionStorage
        sessionStorage.removeItem('auth_state');
        // Use window.location for a full page reload to ensure clean state
        window.location.href = '/login';
      }
    });
  }

  // Always verify session with backend on page load
  // This ensures we catch expired/invalid sessions even if sessionStorage says we're logged in
  try {
    await store.fetchMe();
    return true; // Auth successful
  } catch (error) {
    // Not authenticated - that's okay, user will see login page
    // Clear the error and any stale auth state
    store.clearError();
    sessionStorage.removeItem('auth_state');
    console.info('No active session found');
    return false; // Not authenticated
  }
};

/**
 * Cleanup auth store on app unmount.
 *
 * Stops refresh timer and closes global broadcast channel (MEDIUM-7).
 */
export const cleanupAuth = (): void => {
  const store = useAuthStore.getState();
  store._stopRefreshTimer();
  // Close global broadcast channel (MEDIUM-7: single instance cleanup)
  if (globalBroadcastChannel) {
    globalBroadcastChannel.close();
    globalBroadcastChannel = null;
  }
};
