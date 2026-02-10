/**
 * CSRF Service Tests
 *
 * Unit tests for CSRF service API and manager
 * Story 1.9: CSRF Token Generation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  csrfApi,
  CsrfManager,
  csrfManager,
  CsrfError,
  CsrfErrorCode,
  type CsrfTokenResponse,
  type CsrfValidationResponse,
} from './csrf';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('csrfApi', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('getCsrfToken', () => {
    it('should fetch a new CSRF token', async () => {
      const mockToken: CsrfTokenResponse = {
        csrf_token: 'session123:abc456def',
        session_id: 'session123',
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      const result = await csrfApi.getCsrfToken();

      expect(result).toEqual(mockToken);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/csrf-token'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
    });

    it('should include credentials for httpOnly cookies', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'test:token',
          session_id: 'test',
          max_age: 3600,
        }),
      });

      await csrfApi.getCsrfToken();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('should throw CsrfError on 401 unauthorized', async () => {
      const mockError = {
        ok: false,
        status: 401,
        json: async () => ({
          detail: {
            error_code: 1001,
            message: 'Unauthorized',
          },
        }),
      };
      mockFetch.mockResolvedValueOnce(mockError).mockResolvedValueOnce(mockError);

      await expect(csrfApi.getCsrfToken()).rejects.toThrow(CsrfError);
      await expect(csrfApi.getCsrfToken()).rejects.toThrow('Unauthorized');
    });

    it('should throw CsrfError with error code 2002 on rate limit', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({
          detail: {
            error_code: CsrfErrorCode.RATE_LIMIT_EXCEEDED,
            message: 'Too many CSRF token requests',
          },
        }),
      });

      try {
        await csrfApi.getCsrfToken();
        expect.fail('Should have thrown CsrfError');
      } catch (error) {
        expect(error).toBeInstanceOf(CsrfError);
        expect((error as CsrfError).code).toBe(CsrfErrorCode.RATE_LIMIT_EXCEEDED);
        expect((error as CsrfError).status).toBe(429);
      }
    });
  });

  describe('refreshCsrfToken', () => {
    it('should refresh CSRF token with POST', async () => {
      const mockToken: CsrfTokenResponse = {
        csrf_token: 'session123:new789xyz',
        session_id: 'session123', // Same session_id
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      const result = await csrfApi.refreshCsrfToken();

      expect(result).toEqual(mockToken);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/csrf-token/refresh'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });

    it('should maintain session_id across refreshes', async () => {
      const sessionId = 'persistent-session';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: `${sessionId}:old`,
          session_id: sessionId,
          max_age: 3600,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: `${sessionId}:new`,
          session_id: sessionId, // Same session
          max_age: 3600,
        }),
      });

      const original = await csrfApi.getCsrfToken();
      const refreshed = await csrfApi.refreshCsrfToken();

      expect(refreshed.session_id).toBe(original.session_id);
      expect(refreshed.csrf_token).not.toBe(original.csrf_token);
    });
  });

  describe('clearCsrfToken', () => {
    it('should clear CSRF token with DELETE', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'CSRF token cleared' }),
      });

      await csrfApi.clearCsrfToken();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/csrf-token'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should handle clear token errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({
          detail: {
            error_code: 1002,
            message: 'Internal server error',
          },
        }),
      });

      await expect(csrfApi.clearCsrfToken()).rejects.toThrow(CsrfError);
    });
  });

  describe('validateCsrfToken', () => {
    it('should validate a valid token', async () => {
      const mockResponse: CsrfValidationResponse = {
        valid: true,
        message: 'CSRF token is valid',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await csrfApi.validateCsrfToken('session123:abc456');

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/csrf-token/validate'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-CSRF-Token': 'session123:abc456',
          }),
        })
      );
    });

    it('should return valid=false for invalid token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          message: 'CSRF token is invalid or missing',
        }),
      });

      const result = await csrfApi.validateCsrfToken('invalid-token');

      expect(result.valid).toBe(false);
      expect(result.message).toContain('invalid');
    });

    it('should handle missing token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          message: 'CSRF token is invalid or missing',
        }),
      });

      const result = await csrfApi.validateCsrfToken('');

      expect(result.valid).toBe(false);
    });
  });
});

describe('CsrfManager', () => {
  let manager: CsrfManager;

  beforeEach(() => {
    manager = new CsrfManager();
    mockFetch.mockClear();
    vi.clearAllTimers();
    vi.useFakeTimers();
  });

  afterEach(() => {
    manager.destroy();
    vi.useRealTimers();
  });

  describe('getToken', () => {
    it('should fetch token on first call', async () => {
      const mockToken: CsrfTokenResponse = {
        csrf_token: 'session123:abc456',
        session_id: 'session123',
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      const token = await manager.getToken();

      expect(token).toBe(mockToken.csrf_token);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should return cached token if still valid', async () => {
      const mockToken: CsrfTokenResponse = {
        csrf_token: 'session123:abc456',
        session_id: 'session123',
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      await manager.getToken();
      const token2 = await manager.getToken();

      expect(token2).toBe(mockToken.csrf_token);
      expect(mockFetch).toHaveBeenCalledTimes(1); // Only one fetch
    });

    it('should refresh token if expired', async () => {
      const mockToken1: CsrfTokenResponse = {
        csrf_token: 'session123:old',
        session_id: 'session123',
        max_age: 1, // 1 second
      };

      const mockToken2: CsrfTokenResponse = {
        csrf_token: 'session123:new',
        session_id: 'session123',
        max_age: 3600,
      };

      let callCount = 0;
      mockFetch.mockImplementation(async () => {
        callCount++;
        if (callCount === 1) {
          return {
            ok: true,
            json: async () => mockToken1,
          };
        } else {
          return {
            ok: true,
            json: async () => mockToken2,
          };
        }
      });

      await manager.getToken();

      // Advance time past expiry
      vi.setSystemTime(Date.now() + 2000);

      const token = await manager.getToken();

      expect(token).toBe(mockToken2.csrf_token);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('fetchToken', () => {
    it('should fetch and store token', async () => {
      const mockToken: CsrfTokenResponse = {
        csrf_token: 'session123:abc456',
        session_id: 'session123',
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      await manager.fetchToken();

      expect(manager.getSessionId()).toBe('session123');
      expect(manager.getExpiryTime()).toBeGreaterThan(Date.now());
    });

    it('should schedule auto-refresh', async () => {
      const refreshSpy = vi.spyOn(manager, 'refreshToken').mockResolvedValue();

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 301, // Should trigger refresh at 300 seconds (5 min buffer)
        }),
      });

      await manager.fetchToken();

      // Advance time to trigger auto-refresh
      vi.advanceTimersByTime(301000);

      expect(refreshSpy).toHaveBeenCalled();
    });
  });

  describe('refreshToken', () => {
    it('should refresh existing token', async () => {
      const mockToken1: CsrfTokenResponse = {
        csrf_token: 'session123:old',
        session_id: 'session123',
        max_age: 3600,
      };

      const mockToken2: CsrfTokenResponse = {
        csrf_token: 'session123:new',
        session_id: 'session123',
        max_age: 3600,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken1,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken2,
      });

      await manager.fetchToken();
      await manager.refreshToken();

      expect(manager.getSessionId()).toBe('session123'); // Same session
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('validateToken', () => {
    it('should return true for valid token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 3600,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: true,
          message: 'CSRF token is valid',
        }),
      });

      await manager.fetchToken();
      const isValid = await manager.validateToken();

      expect(isValid).toBe(true);
    });

    it('should return false for invalid token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 3600,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          valid: false,
          message: 'CSRF token is invalid',
        }),
      });

      await manager.fetchToken();
      const isValid = await manager.validateToken();

      expect(isValid).toBe(false);
    });

    it('should return false when no token', async () => {
      const isValid = await manager.validateToken();
      expect(isValid).toBe(false);
    });
  });

  describe('clearToken', () => {
    it('should clear token and call API', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 3600,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'CSRF token cleared' }),
      });

      await manager.fetchToken();
      await manager.clearToken();

      expect(manager.getSessionId()).toBe(null);
      expect(manager.getExpiryTime()).toBe(null);
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('should clear local state even if API fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 3600,
        }),
      });

      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await manager.fetchToken();

      try {
        await manager.clearToken();
      } catch {
        // Expected to throw
      }

      // Local state should still be cleared
      expect(manager.getSessionId()).toBe(null);
      expect(manager.getExpiryTime()).toBe(null);
    });
  });

  describe('getRemainingTime', () => {
    it('should return remaining seconds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 600, // 10 minutes
        }),
      });

      await manager.fetchToken();

      const remaining = manager.getRemainingTime();
      expect(remaining).toBeGreaterThan(0);
      expect(remaining).toBeLessThanOrEqual(600);
    });

    it('should return 0 when no token', () => {
      const remaining = manager.getRemainingTime();
      expect(remaining).toBe(0);
    });
  });

  describe('destroy', () => {
    it('should clear refresh timer', async () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          csrf_token: 'session123:abc456',
          session_id: 'session123',
          max_age: 600,
        }),
      });

      await manager.fetchToken();
      manager.destroy();

      expect(clearTimeoutSpy).toHaveBeenCalled();
    });
  });
});

describe('CsrfErrorCode', () => {
  it('should have correct error code values', () => {
    expect(CsrfErrorCode.INVALID_TOKEN).toBe(2000);
    expect(CsrfErrorCode.RATE_LIMIT_EXCEEDED).toBe(2002);
  });
});
