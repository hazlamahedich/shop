/**
 * Bot Configuration Service
 *
 * Story 1.12: Bot Naming
 *
 * Provides client-side API for bot configuration management:
 * - Get bot configuration (bot_name, personality, custom_greeting)
 * - Update bot name
 *
 * API Endpoints:
 * - GET /api/v1/merchant/bot-config - Get current bot configuration
 * - PUT /api/v1/merchant/bot-config - Update bot configuration
 */

import { apiClient } from './api';

/**
 * Response from bot config endpoints
 */
export interface BotConfigResponse {
  botName: string | null;
  personality: string | null;
  customGreeting: string | null;
}

/**
 * Request body for updating bot name
 */
export interface BotNameUpdateRequest {
  bot_name?: string | null;
}

/**
 * Error response from bot config endpoints
 */
export interface BotConfigErrorResponse {
  detail?: {
    error_code: number;
    message: string;
  };
  message?: string;
}

/**
 * Bot Config error codes from backend
 */
export enum BotConfigErrorCode {
  // Bot name errors (4200-4249)
  BOT_NAME_TOO_LONG = 4200,
  SAVE_FAILED = 4201,
  BOT_CONFIG_ACCESS_DENIED = 4202,
}

/**
 * Bot Config Service Error
 */
export class BotConfigError extends Error {
  constructor(
    message: string,
    public code?: BotConfigErrorCode,
    public status?: number
  ) {
    super(message);
    this.name = 'BotConfigError';
  }
}

/**
 * Bot Config API Client
 *
 * Handles all bot configuration operations with automatic error handling
 * and response parsing.
 *
 * NOTE: apiClient.request<T>() returns ApiEnvelope<T> which contains:
 * - data: T (the actual response payload)
 * - meta: { requestId, timestamp, ... }
 *
 * The generic type parameter is the payload type, not the envelope.
 * The apiClient automatically unwraps the envelope and returns the data.
 */
export const botConfigApi = {
  /**
   * Get the current merchant's bot configuration
   *
   * @returns Bot configuration with bot_name, personality, and custom_greeting
   * @throws BotConfigError if request fails
   */
  async getBotConfig(): Promise<BotConfigResponse> {
    try {
      const response = await apiClient.get<BotConfigResponse>('/api/v1/merchant/bot-config');
      // apiClient.get<T> returns ApiEnvelope<T>, we access .data to get T
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch bot configuration';
      throw new BotConfigError(errorMessage, undefined, (error as any)?.status);
    }
  },

  /**
   * Update the merchant's bot name
   *
   * Allows updating the bot name. Empty strings or whitespace-only strings
   * will clear the bot name (set to null).
   *
   * @param update - Bot name update with optional bot_name field
   * @returns Updated bot configuration
   * @throws BotConfigError if request fails
   */
  async updateBotName(update: BotNameUpdateRequest): Promise<BotConfigResponse> {
    try {
      const response = await apiClient.put<BotConfigResponse>(
        '/api/v1/merchant/bot-config',
        update
      );
      // apiClient.put<T> returns ApiEnvelope<T>, we access .data to get T
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to update bot name';
      let errorCode: BotConfigErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Extract error code from response if available
      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BotConfigError(errorMessage, errorCode, (error as any)?.status);
    }
  },
};
