/**
 * Merchant Configuration Service
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Provides client-side API for merchant personality configuration:
 * - Get current personality configuration
 * - Update personality and custom greeting
 *
 * API Endpoints:
 * - GET /api/merchant/personality - Get current configuration
 * - PATCH /api/merchant/personality - Update configuration
 */

import { apiClient } from './api';
import type { PersonalityType } from '../types/enums';

/**
 * Response from personality configuration endpoints
 */
export interface PersonalityConfigResponse {
  personality: PersonalityType;
  custom_greeting: string | null;
}

/**
 * Request body for updating personality configuration
 */
export interface PersonalityConfigUpdateRequest {
  personality?: PersonalityType;
  custom_greeting?: string | null;
}

/**
 * Error response from personality endpoints
 */
export interface PersonalityErrorResponse {
  detail?: {
    error_code: number;
    message: string;
  };
  message?: string;
}

/**
 * Personality Configuration error codes from backend
 */
export enum PersonalityErrorCode {
  INVALID_PERSONALITY = 4000,
  GREETING_TOO_LONG = 4001,
  SAVE_FAILED = 4002,
}

/**
 * Personality Configuration Service Error
 */
export class PersonalityConfigError extends Error {
  constructor(
    message: string,
    public code?: PersonalityErrorCode,
    public status?: number
  ) {
    super(message);
    this.name = 'PersonalityConfigError';
  }
}

/**
 * Request body for transforming greeting
 */
export interface GreetingTransformRequest {
  custom_greeting: string;
  target_personality: PersonalityType;
  bot_name?: string | null;
  business_name?: string | null;
}

/**
 * Response from greeting transform endpoint
 */
export interface GreetingTransformResponse {
  transformed_greeting: string;
  personality: PersonalityType;
  original_greeting: string;
}

/**
 * Personality Configuration API Client
 *
 * Handles all personality configuration operations with automatic error handling
 * and response parsing.
 */
export const merchantConfigApi = {
  /**
   * Get the current merchant's personality configuration
   *
   * @returns Personality configuration with personality type and custom greeting
   * @throws PersonalityConfigError if request fails
   */
  async getPersonalityConfig(): Promise<PersonalityConfigResponse> {
    try {
      const response = await apiClient.get<PersonalityConfigResponse>(
        '/api/merchant/personality'
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch personality configuration';
      throw new PersonalityConfigError(errorMessage, undefined, (error as any)?.status);
    }
  },

  /**
   * Update the merchant's personality configuration
   *
   * Allows updating personality type and/or custom greeting.
   * Either field can be updated independently.
   *
   * @param update - Configuration update with optional personality and custom_greeting
   * @returns Updated personality configuration
   * @throws PersonalityConfigError if request fails
   */
  async updatePersonalityConfig(
    update: PersonalityConfigUpdateRequest
  ): Promise<PersonalityConfigResponse> {
    try {
      const response = await apiClient.patch<PersonalityConfigResponse>(
        '/api/merchant/personality',
        update
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to update personality configuration';
      let errorCode: PersonalityErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Extract error code from response if available
      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new PersonalityConfigError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },

  /**
   * Transform a custom greeting to match a target personality tone
   *
   * Uses LLM to rewrite the greeting while preserving all business details
   * (business name, products, location, taglines, etc.) but changing the
   * tone to match the target personality.
   *
   * @param request - Transform request with greeting and target personality
   * @returns Transformed greeting with personality tone applied
   * @throws PersonalityConfigError if request fails
   */
  async transformGreeting(
    request: GreetingTransformRequest
  ): Promise<GreetingTransformResponse> {
    try {
      const response = await apiClient.post<GreetingTransformResponse>(
        '/api/merchant/greeting/transform',
        request
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to transform greeting';
      throw new PersonalityConfigError(errorMessage, undefined, (error as any)?.status);
    }
  },
};
