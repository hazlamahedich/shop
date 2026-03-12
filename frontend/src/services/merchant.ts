/**
 * Merchant Mode Service
 *
 * Story 8.7: Settings Mode Toggle
 *
 * Provides client-side API for merchant mode operations:
 * - Get current onboarding mode
 * - Update onboarding mode
 *
 * API Endpoints:
 * - GET /api/merchant/mode - Get current mode
 * - PATCH /api/merchant/mode - Update mode
 *
 * Note: CSRF protection is already bypassed for these endpoints (Story 8.1)
 */

import { apiClient } from './api';
import type { OnboardingMode } from '../types/onboarding';

/**
 * Response from merchant mode endpoints (GET)
 */
export interface MerchantModeResponse {
  onboardingMode: OnboardingMode;
}

/**
 * Request body for updating merchant mode
 */
export interface MerchantModeUpdateRequest {
  mode: OnboardingMode;
}

/**
 * Response from mode update endpoint (PATCH)
 */
export interface MerchantModeUpdateResponse {
  onboardingMode: OnboardingMode;
  updatedAt: string;
}

/**
 * API response envelope wrapper
 */
interface ApiResponse<T> {
  data: T;
}

/**
 * Retry configuration
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
};

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate exponential backoff delay with jitter
 */
function calculateDelay(attempt: number): number {
  const exponentialDelay = RETRY_CONFIG.baseDelayMs * Math.pow(2, attempt);
  const jitter = Math.random() * 100;
  return Math.min(exponentialDelay + jitter, RETRY_CONFIG.maxDelayMs);
}

/**
 * Error response from merchant mode endpoints
 */
export interface MerchantModeErrorResponse {
  error_code?: number;
  message?: string;
  detail?: {
    error_code: number;
    message: string;
  };
}

/**
 * Merchant Mode error codes from backend (Story 8.1)
 */
export enum MerchantModeErrorCode {
  INVALID_MODE = 8001,
  UNAUTHORIZED = 8002,
  UPDATE_FAILED = 8003,
}

/**
 * Merchant Mode Service Error
 */
export class MerchantModeError extends Error {
  constructor(
    message: string,
    public code?: MerchantModeErrorCode,
    public status?: number
  ) {
    super(message);
    this.name = 'MerchantModeError';
  }
}

/**
 * Merchant Mode API Client
 *
 * Handles all merchant mode operations with automatic error handling,
 * retry logic (3 retries with exponential backoff), and response parsing.
 */
export const merchantApi = {
  /**
   * Get the current merchant's onboarding mode
   *
   * @returns Onboarding mode (general or ecommerce)
   * @throws MerchantModeError if request fails after all retries
   */
  async getMerchantMode(): Promise<MerchantModeResponse> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
      try {
        const response = await apiClient.get<ApiResponse<MerchantModeResponse>>(
          '/api/merchant/mode'
        );
        return response.data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt < RETRY_CONFIG.maxRetries) {
          const delay = calculateDelay(attempt);
          await sleep(delay);
        }
      }
    }

    const errorMessage = lastError?.message || 'Failed to fetch merchant mode';
    throw new MerchantModeError(
      errorMessage,
      undefined,
      (lastError as any)?.status
    );
  },

  /**
   * Update the merchant's onboarding mode
   *
   * @param mode - New onboarding mode (general or ecommerce)
   * @returns Updated mode with timestamp
   * @throws MerchantModeError if request fails after all retries
   */
  async updateMerchantMode(
    mode: OnboardingMode
  ): Promise<MerchantModeUpdateResponse> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
      try {
        const response = await apiClient.patch<ApiResponse<MerchantModeUpdateResponse>>(
          '/api/merchant/mode',
          { mode }
        );
        return response.data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt < RETRY_CONFIG.maxRetries) {
          const delay = calculateDelay(attempt);
          await sleep(delay);
          continue;
        }

        let errorMessage = 'Failed to update merchant mode';
        let errorCode: MerchantModeErrorCode | undefined;

        if (lastError instanceof Error) {
          errorMessage = lastError.message;
        }

        const errorData = (lastError as any)?.detail || (lastError as any)?.details || (lastError as any);
        if (errorData?.error_code) {
          errorCode = errorData.error_code;
        }

        throw new MerchantModeError(
          errorMessage,
          errorCode,
          (lastError as any)?.status
        );
      }
    }

    throw new MerchantModeError('Failed to update merchant mode');
  },
};
