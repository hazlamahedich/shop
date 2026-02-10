/**
 * CSRF Store Tests
 *
 * Unit tests for CSRF store (Zustand)
 * Story 1.9: CSRF Token Generation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useCsrfStore, initializeCsrf, getCsrfToken, isCsrfReady } from './csrfStore';
import { csrfApi, CsrfErrorCode } from '../services/csrf';

// Mock the CSRF API
vi.mock('../services/csrf', () => ({
  csrfApi: {
    getCsrfToken: vi.fn(),
    refreshCsrfToken: vi.fn(),
    clearCsrfToken: vi.fn(),
    validateCsrfToken: vi.fn(),
  },
  csrfManager: {},
  CsrfManager: class {},
  CsrfError: class extends Error {
    constructor(message: string, public code?: number, public status?: number) {
      super(message);
      this.name = 'CsrfError';
    }
  },
  CsrfErrorCode: {
    INVALID_TOKEN: 2000,
    RATE_LIMIT_EXCEEDED: 2002,
  },
}));

describe('useCsrfStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    // Reset store state
    useCsrfStore.getState().reset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = useCsrfStore.getState();

      expect(state.token).toBeNull();
      expect(state.sessionId).toBeNull();
      expect(state.expiryTime).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.lastFetchTime).toBeNull();
      expect(state.rateLimitRemaining).toBeNull();
      expect(state.rateLimitResetAt).toBeNull();
    });
  });

  describe('fetchToken', () => {
    it('should fetch and store token', async () => {
      const mockToken = {
        csrf_token: 'session123:abc456def',
        session_id: 'session123',
        max_age: 3600,
      };

      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce(mockToken);

      await useCsrfStore.getState().fetchToken();

      const state = useCsrfStore.getState();

      expect(state.token).toBe(mockToken.csrf_token);
      expect(state.sessionId).toBe(mockToken.session_id);
      expect(state.expiryTime).toBeGreaterThan(Date.now());
      expect(state.loadingState).toBe('success');
      expect(state.error).toBeNull();
      expect(state.lastFetchTime).toBeGreaterThan(0);
    });

    it('should set loading state during fetch', async () => {
      let resolveFetch: (value: any) => void;
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = resolve;
      });

      vi.mocked(csrfApi.getCsrfToken).mockReturnValueOnce(fetchPromise as any);

      // Start fetch (will hang)
      const fetchResult = useCsrfStore.getState().fetchToken();

      // Check loading state
      expect(useCsrfStore.getState().loadingState).toBe('loading');

      // Resolve fetch
      resolveFetch!({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await fetchResult;

      expect(useCsrfStore.getState().loadingState).toBe('success');
    });

    it('should handle fetch errors', async () => {
      const error = new Error('Network error');
      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(error);

      await expect(useCsrfStore.getState().fetchToken()).rejects.toThrow();

      const state = useCsrfStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Network error');
      expect(state.token).toBeNull();
    });

    it('should handle rate limit errors', async () => {
      const CsrfErrorMock = (await import('../services/csrf')).CsrfError;
      const error = new CsrfErrorMock(
        'Too many CSRF token requests',
        CsrfErrorCode.RATE_LIMIT_EXCEEDED,
        429
      );

      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(error);

      await expect(useCsrfStore.getState().fetchToken()).rejects.toThrow();

      const state = useCsrfStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Too many CSRF token requests');
      expect(state.rateLimitRemaining).toBe(0);
      expect(state.rateLimitResetAt).toBeGreaterThan(Date.now());
    });
  });

  describe('refreshToken', () => {
    it('should refresh and update token', async () => {
      const originalToken = {
        csrf_token: 'session123:old',
        session_id: 'session123',
        max_age: 3600,
      };

      const newToken = {
        csrf_token: 'session123:new',
        session_id: 'session123',
        max_age: 3600,
      };

      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce(originalToken);
      vi.mocked(csrfApi.refreshCsrfToken).mockResolvedValueOnce(newToken);

      // First fetch
      await useCsrfStore.getState().fetchToken();
      expect(useCsrfStore.getState().token).toBe(originalToken.csrf_token);

      // Refresh
      await useCsrfStore.getState().refreshToken();

      const state = useCsrfStore.getState();

      expect(state.token).toBe(newToken.csrf_token);
      expect(state.sessionId).toBe('session123'); // Same session
      expect(state.loadingState).toBe('success');
    });

    it('should handle refresh errors', async () => {
      const error = new Error('Refresh failed');
      vi.mocked(csrfApi.refreshCsrfToken).mockRejectedValueOnce(error);

      await expect(useCsrfStore.getState().refreshToken()).rejects.toThrow();

      const state = useCsrfStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Refresh failed');
    });
  });

  describe('clearToken', () => {
    it('should clear token and call API', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      vi.mocked(csrfApi.clearCsrfToken).mockResolvedValueOnce(undefined);

      // First fetch
      await useCsrfStore.getState().fetchToken();
      expect(useCsrfStore.getState().token).not.toBeNull();

      // Clear
      await useCsrfStore.getState().clearToken();

      const state = useCsrfStore.getState();

      expect(state.token).toBeNull();
      expect(state.sessionId).toBeNull();
      expect(state.expiryTime).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(csrfApi.clearCsrfToken).toHaveBeenCalled();
    });

    it('should clear local state even if API fails', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      vi.mocked(csrfApi.clearCsrfToken).mockRejectedValueOnce(
        new Error('API error')
      );

      // First fetch
      await useCsrfStore.getState().fetchToken();

      // Clear (will fail)
      await expect(useCsrfStore.getState().clearToken()).rejects.toThrow();

      // Local state should still be cleared
      const state = useCsrfStore.getState();

      expect(state.token).toBeNull();
      expect(state.sessionId).toBeNull();
      expect(state.expiryTime).toBeNull();
    });
  });

  describe('validateToken', () => {
    it('should return true for valid token', async () => {
      vi.mocked(csrfApi.validateCsrfToken).mockResolvedValueOnce({
        valid: true,
        message: 'CSRF token is valid',
      });

      const isValid = await useCsrfStore.getState().validateToken();

      expect(isValid).toBe(true);
    });

    it('should return false for invalid token', async () => {
      vi.mocked(csrfApi.validateCsrfToken).mockResolvedValueOnce({
        valid: false,
        message: 'CSRF token is invalid',
      });

      const isValid = await useCsrfStore.getState().validateToken();

      expect(isValid).toBe(false);
    });

    it('should return false when no token', async () => {
      const isValid = await useCsrfStore.getState().validateToken();

      expect(isValid).toBe(false);
      expect(csrfApi.validateCsrfToken).not.toHaveBeenCalled();
    });

    it('should handle validation errors', async () => {
      // First set a token
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await useCsrfStore.getState().fetchToken();

      // Validation throws error
      vi.mocked(csrfApi.validateCsrfToken).mockRejectedValueOnce(
        new Error('Validation failed')
      );

      const isValid = await useCsrfStore.getState().validateToken();

      expect(isValid).toBe(false);
    });
  });

  describe('getToken', () => {
    it('should return cached token if valid', async () => {
      const mockToken = {
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      };

      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce(mockToken);

      // First call should fetch
      const token1 = await useCsrfStore.getState().getToken();

      expect(token1).toBe(mockToken.csrf_token);
      expect(csrfApi.getCsrfToken).toHaveBeenCalledTimes(1);

      // Second call should use cache
      const token2 = await useCsrfStore.getState().getToken();

      expect(token2).toBe(mockToken.csrf_token);
      expect(csrfApi.getCsrfToken).toHaveBeenCalledTimes(1);
    });

    it('should fetch new token if expired', async () => {
      vi.useFakeTimers();

      const mockToken1 = {
        csrf_token: 'session123:old',
        session_id: 'session123',
        max_age: 1, // 1 second
      };

      const mockToken2 = {
        csrf_token: 'session123:new',
        session_id: 'session123',
        max_age: 3600,
      };

      vi.mocked(csrfApi.getCsrfToken)
        .mockResolvedValueOnce(mockToken1)
        .mockResolvedValueOnce(mockToken2);

      // First fetch
      const token1 = await useCsrfStore.getState().getToken();
      expect(token1).toBe(mockToken1.csrf_token);

      // Advance time past expiry
      vi.advanceTimersByTime(2000);

      // Should fetch new token
      const token2 = await useCsrfStore.getState().getToken();
      expect(token2).toBe(mockToken2.csrf_token);
      expect(csrfApi.getCsrfToken).toHaveBeenCalledTimes(2);
    });

    it('should fetch new token if none exists', async () => {
      const mockToken = {
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      };

      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce(mockToken);

      const token = await useCsrfStore.getState().getToken();

      expect(token).toBe(mockToken.csrf_token);
      expect(csrfApi.getCsrfToken).toHaveBeenCalled();
    });

    it('should throw if unable to obtain token', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(
        new Error('Fetch failed')
      );

      await expect(useCsrfStore.getState().getToken()).rejects.toThrow(
        'Failed to obtain CSRF token'
      );
    });
  });

  describe('isTokenValid', () => {
    it('should return true when token exists and not expired', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await useCsrfStore.getState().fetchToken();

      expect(useCsrfStore.getState().isTokenValid()).toBe(true);
    });

    it('should return false when no token', () => {
      expect(useCsrfStore.getState().isTokenValid()).toBe(false);
    });

    it('should return false when token expired', async () => {
      vi.useFakeTimers();

      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 1, // 1 second
      });

      await useCsrfStore.getState().fetchToken();
      expect(useCsrfStore.getState().isTokenValid()).toBe(true);

      // Advance past expiry
      vi.advanceTimersByTime(2000);

      expect(useCsrfStore.getState().isTokenValid()).toBe(false);
    });
  });

  describe('getRemainingTime', () => {
    it('should return remaining seconds', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 600, // 10 minutes
      });

      await useCsrfStore.getState().fetchToken();

      const remaining = useCsrfStore.getState().getRemainingTime();

      // Should be approximately 600 seconds (minus buffer)
      expect(remaining).toBeGreaterThan(0);
      expect(remaining).toBeLessThanOrEqual(600);
    });

    it('should return 0 when no token', () => {
      const remaining = useCsrfStore.getState().getRemainingTime();
      expect(remaining).toBe(0);
    });
  });

  describe('isRateLimited', () => {
    it('should return true when rate limited', async () => {
      const CsrfErrorMock = (await import('../services/csrf')).CsrfError;

      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(
        new CsrfErrorMock(
          'Rate limited',
          CsrfErrorCode.RATE_LIMIT_EXCEEDED,
          429
        )
      );

      await expect(useCsrfStore.getState().fetchToken()).rejects.toThrow();

      expect(useCsrfStore.getState().isRateLimited()).toBe(true);
    });

    it('should return false when not rate limited', () => {
      expect(useCsrfStore.getState().isRateLimited()).toBe(false);
    });
  });

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(
        new Error('Test error')
      );

      await expect(useCsrfStore.getState().fetchToken()).rejects.toThrow();

      expect(useCsrfStore.getState().error).toBe('Test error');

      useCsrfStore.getState().clearError();

      expect(useCsrfStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset to initial state', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await useCsrfStore.getState().fetchToken();

      expect(useCsrfStore.getState().token).not.toBeNull();

      useCsrfStore.getState().reset();

      const state = useCsrfStore.getState();

      expect(state.token).toBeNull();
      expect(state.sessionId).toBeNull();
      expect(state.expiryTime).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.lastFetchTime).toBeNull();
    });
  });
});

describe('CSRF Hook Helpers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCsrfStore.getState().reset();
  });

  describe('initializeCsrf', () => {
    it('should initialize CSRF token', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await initializeCsrf();

      expect(useCsrfStore.getState().token).toBe('session123:abc');
    });

    it('should propagate errors', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockRejectedValueOnce(
        new Error('Init failed')
      );

      await expect(initializeCsrf()).rejects.toThrow('Init failed');
    });
  });

  describe('getCsrfToken', () => {
    it('should get token from store', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      const token = await getCsrfToken();

      expect(token).toBe('session123:abc');
    });
  });

  describe('isCsrfReady', () => {
    it('should return true when token valid and not rate limited', async () => {
      vi.mocked(csrfApi.getCsrfToken).mockResolvedValueOnce({
        csrf_token: 'session123:abc',
        session_id: 'session123',
        max_age: 3600,
      });

      await useCsrfStore.getState().fetchToken();

      expect(isCsrfReady()).toBe(true);
    });

    it('should return false when no token', () => {
      expect(isCsrfReady()).toBe(false);
    });
  });
});
