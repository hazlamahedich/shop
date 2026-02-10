/**
 * Authentication Types
 *
 * Types for authentication, session management, and merchant info.
 * Story 1.8: Merchant Dashboard Authentication
 */

/**
 * Merchant information from backend.
 */
export interface Merchant {
  id: number;
  email: string;
  merchant_key: string;
}

/**
 * Session information from backend.
 */
export interface Session {
  expiresAt: string; // ISO-8601 datetime
}

/**
 * Login request credentials.
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Successful login response.
 */
export interface LoginResponse {
  merchant: Merchant;
  session: Session;
}

/**
 * Token refresh response.
 */
export interface RefreshResponse {
  session: Session;
}

/**
 * Current merchant info response (/auth/me).
 */
export interface MeResponse {
  merchant: Merchant;
}

/**
 * API error response structure.
 */
export interface ApiError {
  error_code: number;
  message: string;
  details?: string;
}

/**
 * Auth state in the store.
 */
export interface AuthState {
  isAuthenticated: boolean;
  merchant: Merchant | null;
  sessionExpiresAt: string | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Auth error codes from backend.
 */
export enum AuthErrorCode {
  AUTH_FAILED = 2000,
  INVALID_CREDENTIALS = 2001,
  RATE_LIMITED = 2002,
  TOKEN_EXPIRED = 2003,
  INVALID_TOKEN = 2004,
  SESSION_REVOKED = 2005,
  MERCHANT_NOT_FOUND = 2006,
}
