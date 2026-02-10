/**
 * CSRF Store - Zustand state management for CSRF tokens
 *
 * Story 1.9: CSRF Token Generation
 *
 * Manages CSRF token lifecycle including:
 * - Token fetching and caching
 * - Automatic refresh before expiry
 * - Token validation
 * - Error handling and recovery
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  csrfApi,
  CsrfManager,
  CsrfError,
  CsrfErrorCode,
  type CsrfTokenResponse,
  type CsrfValidationResponse,
} from '../services/csrf';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * CSRF Store State
 */
export interface CsrfState {
  // Token data
  token: string | null;
  sessionId: string | null;
  expiryTime: number | null;

  // UI state
  loadingState: LoadingState;
  error: string | null;
  lastFetchTime: number | null;

  // Rate limit state
  rateLimitRemaining: number | null;
  rateLimitResetAt: number | null;

  // Actions - Token management
  fetchToken: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearToken: () => Promise<void>;
  validateToken: () => Promise<boolean>;

  // Actions - State checks
  getToken: () => Promise<string>;
  isTokenValid: () => boolean;
  getRemainingTime: () => number;
  isRateLimited: () => boolean;

  // Actions - Utility
  clearError: () => void;
  reset: () => void;
}

// Helper to calculate expiry time with buffer
const calculateExpiryTime = (maxAge: number): number => {
  // Refresh 5 minutes before expiry (or halfway if less than 10 min)
  const buffer = Math.min(300, maxAge / 2);
  return Date.now() + (maxAge - buffer) * 1000;
};

/**
 * CSRF store using Zustand
 *
 * Manages CSRF token state with automatic refresh and error recovery.
 */
export const useCsrfStore = create<CsrfState>()(
  persist(
    (set, get) => ({
      // Initial state
      token: null,
      sessionId: null,
      expiryTime: null,
      loadingState: 'idle',
      error: null,
      lastFetchTime: null,
      rateLimitRemaining: null,
      rateLimitResetAt: null,

      /**
       * Fetch a new CSRF token
       *
       * Always fetches a fresh token from the server.
       */
      fetchToken: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const response: CsrfTokenResponse = await csrfApi.getCsrfToken();

          set({
            token: response.csrf_token,
            sessionId: response.session_id,
            expiryTime: calculateExpiryTime(response.max_age),
            loadingState: 'success',
            lastFetchTime: Date.now(),
            rateLimitRemaining: null, // Reset on successful fetch
            rateLimitResetAt: null,
          });

          // Schedule auto-refresh if token will expire
          const remainingTime = calculateExpiryTime(response.max_age) - Date.now();
          if (remainingTime > 0) {
            setTimeout(() => {
              const store = get();
              // Only auto-refresh if we still have this token
              if (store.token === response.csrf_token && store.loadingState !== 'loading') {
                store.refreshToken().catch((error) => {
                  console.error('Failed to auto-refresh CSRF token:', error);
                });
              }
            }, Math.max(0, remainingTime - 60000)); // Refresh 1 minute before expiry
          }
        } catch (error) {
          const errorMessage =
            error instanceof CsrfError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to fetch CSRF token';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          // Check if rate limited
          if (error instanceof CsrfError && error.code === CsrfErrorCode.RATE_LIMIT_EXCEEDED) {
            set({
              rateLimitRemaining: 0,
              rateLimitResetAt: Date.now() + 60000, // 1 minute from now
            });
          }

          throw error;
        }
      },

      /**
       * Refresh the current CSRF token
       *
       * Maintains the existing session but generates a new token.
       */
      refreshToken: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          const response: CsrfTokenResponse = await csrfApi.refreshCsrfToken();

          set({
            token: response.csrf_token,
            sessionId: response.session_id,
            expiryTime: calculateExpiryTime(response.max_age),
            loadingState: 'success',
            lastFetchTime: Date.now(),
          });
        } catch (error) {
          const errorMessage =
            error instanceof CsrfError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to refresh CSRF token';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          throw error;
        }
      },

      /**
       * Clear the current CSRF token
       *
       * Removes the token from memory and from the server.
       */
      clearToken: async () => {
        set({ loadingState: 'loading', error: null });

        try {
          await csrfApi.clearCsrfToken();

          set({
            token: null,
            sessionId: null,
            expiryTime: null,
            loadingState: 'idle',
            lastFetchTime: null,
          });
        } catch (error) {
          const errorMessage =
            error instanceof CsrfError
              ? error.message
              : error instanceof Error
                ? error.message
                : 'Failed to clear CSRF token';

          set({
            loadingState: 'error',
            error: errorMessage,
          });

          // Clear local state even on error
          set({
            token: null,
            sessionId: null,
            expiryTime: null,
          });

          throw error;
        }
      },

      /**
       * Validate the current token
       *
       * @returns true if token is valid, false otherwise
       */
      validateToken: async (): Promise<boolean> => {
        const { token } = get();

        if (!token) {
          return false;
        }

        try {
          const result: CsrfValidationResponse = await csrfApi.validateCsrfToken(token);
          return result.valid;
        } catch {
          return false;
        }
      },

      /**
       * Get the current valid CSRF token
       *
       * Returns the cached token if still valid, otherwise fetches a new one.
       *
       * @returns The current valid CSRF token
       */
      getToken: async (): Promise<string> => {
        const state = get();

        // Check if token exists and is not expired
        if (state.token && state.expiryTime && Date.now() < state.expiryTime) {
          return state.token;
        }

        // Need to fetch a new token
        await state.fetchToken();

        const newState = get();
        if (!newState.token) {
          throw new Error('Failed to obtain CSRF token');
        }

        return newState.token;
      },

      /**
       * Check if the current token is valid
       *
       * @returns true if token exists and is not expired
       */
      isTokenValid: (): boolean => {
        const { token, expiryTime } = get();
        return token !== null && expiryTime !== null && Date.now() < expiryTime;
      },

      /**
       * Get remaining time until token expires
       *
       * @returns Remaining seconds until expiry, or 0 if expired/unknown
       */
      getRemainingTime: (): number => {
        const { expiryTime } = get();
        if (!expiryTime) {
          return 0;
        }
        return Math.max(0, Math.floor((expiryTime - Date.now()) / 1000));
      },

      /**
       * Check if currently rate limited
       *
       * @returns true if rate limited, false otherwise
       */
      isRateLimited: (): boolean => {
        const { rateLimitResetAt } = get();
        if (!rateLimitResetAt) {
          return false;
        }
        return Date.now() < rateLimitResetAt;
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },

      /**
       * Reset store to initial state
       */
      reset: () => {
        set({
          token: null,
          sessionId: null,
          expiryTime: null,
          loadingState: 'idle',
          error: null,
          lastFetchTime: null,
          rateLimitRemaining: null,
          rateLimitResetAt: null,
        });
      },
    }),
    {
      name: 'csrf-store',
      // Only persist non-sensitive data (token itself is in httpOnly cookie)
      partialize: (state) => ({
        sessionId: state.sessionId,
        lastFetchTime: state.lastFetchTime,
        rateLimitResetAt: state.rateLimitResetAt,
      }),
    }
  )
);

/**
 * CSRF Hook Helpers
 *
 * Convenience hooks for common CSRF operations.
 */

/**
 * Initialize CSRF token on mount
 *
 * Usage in components:
 * ```tsx
 * useEffect(() => {
 *   const init = async () => {
 *     try {
 *       await useCsrfStore.getState().fetchToken();
 *     } catch (error) {
 *       console.error('Failed to initialize CSRF:', error);
 *     }
 *   };
 *   init();
 * }, []);
 * ```
 */
export const initializeCsrf = async (): Promise<void> => {
  try {
    await useCsrfStore.getState().fetchToken();
  } catch (error) {
    console.error('Failed to initialize CSRF:', error);
    throw error;
  }
};

/**
 * Get CSRF token for API requests
 *
 * Usage:
 * ```tsx
 * const getToken = useCsrfStore(state => state.getToken);
 *
 * // In API call
 * const token = await getToken();
 * headers.set('X-CSRF-Token', token);
 * ```
 */
export const getCsrfToken = (): Promise<string> => {
  return useCsrfStore.getState().getToken();
};

/**
 * Check if CSRF is ready for use
 *
 * @returns true if token is valid and not rate limited
 */
export const isCsrfReady = (): boolean => {
  const state = useCsrfStore.getState();
  return state.isTokenValid() && !state.isRateLimited();
};

/**
 * Selectors for common state values
 */
export const selectCsrfToken = (state: CsrfState) => state.token;
export const selectCsrfLoading = (state: CsrfState) => state.loadingState === 'loading';
export const selectCsrfError = (state: CsrfState) => state.error;
export const selectCsrfIsValid = (state: CsrfState) => state.isTokenValid();
export const selectCsrfRemainingTime = (state: CsrfState) => state.getRemainingTime();
export const selectIsRateLimited = (state: CsrfState) => state.isRateLimited();
