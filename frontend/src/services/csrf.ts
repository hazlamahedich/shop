/**
 * CSRF Service
 *
 * Provides client-side CSRF token management for state-changing operations.
 * Implements Story 1.9: CSRF Token Generation
 *
 * Features:
 * - Fetch new CSRF tokens
 * - Refresh existing tokens (maintains session)
 * - Clear CSRF tokens
 * - Validate tokens
 * - Auto-refresh before expiry
 *
 * API Endpoints:
 * - GET /api/v1/csrf-token - Get new token
 * - POST /api/v1/csrf-token/refresh - Refresh existing token
 * - DELETE /api/v1/csrf-token - Clear token
 * - GET /api/v1/csrf-token/validate - Validate current token
 */

const API_BASE_URL = ''; // Relative path for proxy

/**
 * Response from CSRF token endpoints
 */
export interface CsrfTokenResponse {
  csrf_token: string;
  session_id: string;
  max_age: number; // seconds until expiry (typically 3600 = 1 hour)
}

/**
 * Response from validate endpoint
 */
export interface CsrfValidationResponse {
  valid: boolean;
  message: string;
}

/**
 * Error response from CSRF endpoints
 */
export interface CsrfErrorResponse {
  detail: {
    error_code: number;
    message: string;
  };
}

/**
 * CSRF error codes from backend
 */
export enum CsrfErrorCode {
  INVALID_TOKEN = 2000,
  RATE_LIMIT_EXCEEDED = 2002,
}

/**
 * CSRF Service API
 *
 * Provides all CSRF token operations through a clean API.
 * All methods throw CsrfError on failure.
 */
export class CsrfError extends Error {
  constructor(
    message: string,
    public code?: CsrfErrorCode,
    public status?: number
  ) {
    super(message);
    this.name = 'CsrfError';
  }
}

/**
 * CSRF API client
 *
 * Handles all CSRF token operations with automatic error handling
 * and response parsing.
 */
export const csrfApi = {
  /**
   * Get a new CSRF token for the session
   *
   * @returns CSRF token response with token, session_id, and max_age
   * @throws CsrfError if request fails (401, 429, 500, etc.)
   */
  async getCsrfToken(): Promise<CsrfTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token`, {
      method: 'GET',
      credentials: 'include', // Required for httpOnly cookies
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      await this._handleError(response);
    }

    const data = await response.json();
    return {
      csrf_token: data.csrf_token,
      session_id: data.session_id,
      max_age: data.max_age,
    };
  },

  /**
   * Refresh the current CSRF token
   *
   * Maintains the existing session but generates a new token.
   * Useful for refreshing tokens before they expire.
   *
   * @returns New CSRF token response with same session_id
   * @throws CsrfError if request fails
   */
  async refreshCsrfToken(): Promise<CsrfTokenResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      await this._handleError(response);
    }

    const data = await response.json();
    return {
      csrf_token: data.csrf_token,
      session_id: data.session_id,
      max_age: data.max_age,
    };
  },

  /**
   * Clear the current CSRF token
   *
   * Invalidates the CSRF token by clearing it from the client's cookies.
   * Use this on logout or when clearing session data.
   *
   * @throws CsrfError if request fails
   */
  async clearCsrfToken(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      await this._handleError(response);
    }
  },

  /**
   * Validate the current CSRF token
   *
   * Checks if the current CSRF token is valid without consuming it.
   * The token must be provided via the X-CSRF-Token header.
   *
   * @param token - The CSRF token to validate
   * @returns Validation result with valid flag and message
   * @throws CsrfError if request fails (but not for invalid token)
   */
  async validateCsrfToken(token: string): Promise<CsrfValidationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/csrf-token/validate`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': token,
      },
    });

    // 200 is returned even for invalid tokens, so we expect OK
    if (!response.ok) {
      await this._handleError(response);
    }

    const data = await response.json();
    return {
      valid: data.valid,
      message: data.message,
    };
  },

  /**
   * Handle error responses from CSRF endpoints
   * @private
   */
  async _handleError(response: Response): Promise<never> {
    let errorMessage = `CSRF request failed: ${response.status}`;
    let errorCode: CsrfErrorCode | undefined;

    try {
      const data: CsrfErrorResponse = await response.json();
      if (data.detail?.message) {
        errorMessage = data.detail.message;
      }
      if (data.detail?.error_code) {
        errorCode = data.detail.error_code;
      }
    } catch {
      // Use default error message
    }

    throw new CsrfError(errorMessage, errorCode, response.status);
  },
};

/**
 * CSRF Manager
 *
 * High-level CSRF token management with auto-refresh capabilities.
 * Handles token lifecycle including fetching, refreshing, and expiry.
 */
export class CsrfManager {
  private token: string | null = null;
  private sessionId: string | null = null;
  private expiryTime: number | null = null;
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Get the current CSRF token
   *
   * Returns the cached token if still valid, otherwise fetches a new one.
   *
   * @returns The current valid CSRF token
   */
  async getToken(): Promise<string> {
    // Check if we need to refresh the token
    if (this.expiryTime && Date.now() >= this.expiryTime) {
      await this.refreshToken();
    }

    // If no token, fetch one
    if (!this.token) {
      await this.fetchToken();
    }

    return this.token!;
  }

  /**
   * Fetch a new CSRF token
   *
   * Always fetches a fresh token from the server.
   */
  async fetchToken(): Promise<void> {
    const response = await csrfApi.getCsrfToken();
    this.token = response.csrf_token;
    this.sessionId = response.session_id;
    this._setExpiry(response.max_age);
    this._scheduleRefresh(response.max_age);
  }

  /**
   * Refresh the current CSRF token
   *
   * Refreshes the token while maintaining the session.
   */
  async refreshToken(): Promise<void> {
    const response = await csrfApi.refreshCsrfToken();
    this.token = response.csrf_token;
    this.sessionId = response.session_id;
    this._setExpiry(response.max_age);
    this._scheduleRefresh(response.max_age);
  }

  /**
   * Validate the current token
   *
   * @returns true if token is valid, false otherwise
   */
  async validateToken(): Promise<boolean> {
    if (!this.token) {
      return false;
    }

    try {
      const result = await csrfApi.validateCsrfToken(this.token);
      return result.valid;
    } catch {
      return false;
    }
  }

  /**
   * Clear the current token
   *
   * Removes the token from memory and from the server.
   */
  async clearToken(): Promise<void> {
    this._clearRefreshTimer();

    try {
      await csrfApi.clearCsrfToken();
    } finally {
      // Always clear local state
      this.token = null;
      this.sessionId = null;
      this.expiryTime = null;
    }
  }

  /**
   * Get the current session ID
   *
   * @returns The current session ID or null
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * Get token expiry timestamp
   *
   * @returns The expiry time as a timestamp or null
   */
  getExpiryTime(): number | null {
    return this.expiryTime;
  }

  /**
   * Get remaining time until token expires
   *
   * @returns Remaining seconds until expiry, or 0 if expired/unknown
   */
  getRemainingTime(): number {
    if (!this.expiryTime) {
      return 0;
    }
    return Math.max(0, Math.floor((this.expiryTime - Date.now()) / 1000));
  }

  /**
   * Set token expiry time
   * @private
   */
  private _setExpiry(maxAge: number): void {
    // Refresh 5 minutes before expiry (or halfway if less than 10 min)
    const refreshBuffer = Math.min(300, maxAge / 2);
    this.expiryTime = Date.now() + (maxAge - refreshBuffer) * 1000;
  }

  /**
   * Schedule automatic token refresh
   * @private
   */
  private _scheduleRefresh(maxAge: number): void {
    this._clearRefreshTimer();

    // Schedule refresh 5 minutes before expiry
    const refreshDelay = Math.max(0, (maxAge - 300) * 1000);

    this.refreshTimer = setTimeout(() => {
      this.refreshToken().catch((error) => {
        console.error('Failed to auto-refresh CSRF token:', error);
      });
    }, refreshDelay);
  }

  /**
   * Clear the refresh timer
   * @private
   */
  private _clearRefreshTimer(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Cleanup resources
   *
   * Call this when the manager is no longer needed.
   */
  destroy(): void {
    this._clearRefreshTimer();
  }
}

// Global CSRF manager instance
export const csrfManager = new CsrfManager();
