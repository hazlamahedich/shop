/**
 * Authentication API Service
 *
 * Story 1.8: Handles authentication, session management, and merchant info.
 *
 * Provides functions to:
 * - Login with email/password
 * - Logout and invalidate session
 * - Get current merchant info
 * - Refresh JWT token
 *
 * Note: Uses httpOnly cookies for session management (no localStorage tokens).
 */

import { apiClient } from './api';
import type {
  LoginRequest,
  RegisterRequest,
  LoginResponse,
  RefreshResponse,
  MeResponse,
  ApiError,
} from '../types/auth';

const API_BASE_URL = '';

/**
 * Login with email and password.
 *
 * Creates JWT token, stores session in database, and sets httpOnly cookie.
 * Implements session rotation (invalidates old sessions).
 * Rate limits login attempts (5 per 15 minutes per IP/email).
 *
 * @param credentials - Email and password
 * @returns Merchant info and session expiration
 * @throws ApiError with error_code on failure
 */
export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  // Direct fetch for login (no auth header needed, uses cookies)
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Important for httpOnly cookies
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    // Backend wraps errors in a 'detail' property
    const errorData = data?.detail || data || {
      error_code: 2000,
      message: 'Authentication failed',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    (error as any).details = errorData.details;
    throw error;
  }

  return response.json();
}

/**
 * Register a new merchant account.
 *
 * Creates merchant, session, and sets httpOnly cookie for auto-login.
 * Rate limits registration attempts (5 per 15 minutes per IP/email).
 *
 * @param credentials - Email and password
 * @returns Merchant info and session expiration
 * @throws ApiError with error_code on failure
 */
export async function register(credentials: RegisterRequest): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    const errorData = data?.detail || data || {
      error_code: 2000,
      message: 'Registration failed',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    (error as any).details = errorData.details;
    throw error;
  }

  return response.json();
}

/**
 * Logout merchant and invalidate session.
 *
 * Clears session cookie, revokes session in database, and
 * notifies other tabs via BroadcastChannel (handled by frontend).
 *
 * @throws Error if logout fails (non-blocking)
 */
export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
  } catch (error) {
    console.warn('Logout request failed:', error);
    // Continue with client-side logout even if API fails
  }
}

/**
 * Get current authenticated merchant info.
 *
 * @returns Current merchant information
 * @throws ApiError if not authenticated or session invalid
 */
export async function getMe(): Promise<MeResponse> {
  const envelope = await apiClient.get<MeResponse>('/api/v1/auth/me');
  return envelope.data;
}

/**
 * Refresh JWT token (extends session).
 *
 * Should be called at 50% of session lifetime (12 hours).
 *
 * @returns New session expiration time
 * @throws ApiError if not authenticated
 */
export async function refreshToken(): Promise<RefreshResponse> {
  // Direct fetch for refresh (uses httpOnly cookies)
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    // Backend wraps errors in a 'detail' property
    const errorData = data?.detail || data || {
      error_code: 2003,
      message: 'Token refresh failed',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    throw error;
  }

  return response.json();
}

/**
 * Setup BroadcastChannel for multi-tab logout sync.
 *
 * When one tab logs out, all other tabs are notified and redirect to login.
 *
 * @returns BroadcastChannel instance (call close() when done)
 */
export function setupAuthBroadcast(): BroadcastChannel {
  const channel = new BroadcastChannel('auth-channel');

  channel.addEventListener('message', (event) => {
    if (event.data.type === 'LOGOUT') {
      // Redirect to login page
      window.location.href = '/login';
    }
  });

  return channel;
}

/**
 * Notify other tabs of logout event.
 *
 * Call this after successful logout to sync state across all tabs.
 */
export function broadcastLogout(): void {
  const channel = new BroadcastChannel('auth-channel');
  channel.postMessage({ type: 'LOGOUT' });
  channel.close();
}

/**
 * Calculate time until session expiration.
 *
 * @param expiresAt - ISO-8601 datetime string
 * @returns Milliseconds until expiration, or 0 if already expired
 */
export function getTimeUntilExpiration(expiresAt: string): number {
  const expiration = new Date(expiresAt).getTime();
  const now = Date.now();
  return Math.max(0, expiration - now);
}

/**
 * Check if session is expired or will expire soon.
 *
 * @param expiresAt - ISO-8601 datetime string
 * @param thresholdMs - Threshold in milliseconds (default: 1 hour)
 * @returns True if session is expired or expiring soon
 */
export function isSessionExpiringSoon(
  expiresAt: string | null,
  thresholdMs: number = 60 * 60 * 1000 // 1 hour
): boolean {
  if (!expiresAt) return true;
  return getTimeUntilExpiration(expiresAt) < thresholdMs;
}


/**
 * Password Reset API Functions
 */

/**
 * Request password reset email.
 *
 * Generates a secure reset token and emails it to the merchant.
 * Token expires after 1 hour.
 * Rate limits requests (3 per hour per email/IP).
 *
 * @param email - Merchant email address
 * @returns Success message
 * @throws Error if request fails
 */
export async function forgotPassword(email: string): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    const errorData = data?.detail || data || {
      error_code: 2000,
      message: 'Failed to send reset email',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    throw error;
  }

  return response.json();
}

/**
 * Verify password reset token validity.
 *
 * Checks if token exists, is not expired, and has not been used.
 *
 * @param token - Password reset token
 * @returns Token validity and associated email (if valid)
 * @throws Error if verification fails
 */
export async function verifyResetToken(
  token: string
): Promise<{ valid: boolean; email: string | null }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/verify-reset-token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ token }),
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    const errorData = data?.detail || data || {
      error_code: 2000,
      message: 'Token verification failed',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    throw error;
  }

  return response.json();
}

/**
 * Reset password using valid token.
 *
 * Validates token, updates password, marks token as used,
 * invalidates all existing sessions, and sends confirmation email.
 *
 * @param token - Password reset token
 * @param newPassword - New password (min 8 characters)
 * @returns Success message
 * @throws Error if token is invalid, expired, or already used
 */
export async function resetPassword(
  token: string,
  newPassword: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      token,
      new_password: newPassword,
    }),
  });

  if (!response.ok) {
    const data: any = await response.json().catch(() => null);
    const errorData = data?.detail || data || {
      error_code: 2000,
      message: 'Password reset failed',
    };
    const error = new Error(errorData.message);
    (error as any).code = errorData.error_code;
    (error as any).details = errorData.details;
    throw error;
  }

  return response.json();
}

// Re-export as authApi for convenience
export const authApi = {
  login,
  register,
  logout,
  getMe,
  refreshToken,
  forgotPassword,
  verifyResetToken,
  resetPassword,
  setupAuthBroadcast,
  broadcastLogout,
  getTimeUntilExpiration,
  isSessionExpiringSoon,
};
