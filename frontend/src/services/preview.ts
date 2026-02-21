/**
 * Preview Mode Service
 *
 * Story 1.13: Bot Preview Mode
 *
 * Provides client-side API for preview mode functionality:
 * - Start a preview session
 * - Send messages in preview mode
 * - Reset preview conversation
 *
 * API Endpoints:
 * - POST /api/v1/preview/conversation - Create a new preview session
 * - POST /api/v1/preview/message - Send a message and get bot response
 * - DELETE /api/v1/preview/conversation - Clear preview session
 */

import { apiClient } from './api';

/**
 * Starter prompts provided by the preview API
 */
export interface StarterPrompt {
  text: string;
}

/**
 * Response from POST /api/v1/preview/conversation
 */
export interface PreviewSessionResponse {
  previewSessionId: string;
  merchantId: number;
  createdAt: string;
  starterPrompts: string[];
}

/**
 * Metadata about the bot response
 */
export interface PreviewMessageMetadata {
  intent: string;
  faqMatched: boolean;
  productsFound: number;
  llmProvider: string;
}

/**
 * Product returned in bot response
 */
export interface PreviewProduct {
  product_id: string;
  title: string;
  price: number | null;
  currency: string;
  image_url: string | null;
  available: boolean;
}

/**
 * Response from POST /api/v1/preview/message
 */
export interface PreviewMessageResponse {
  response: string;
  confidence: number;
  confidenceLevel: 'high' | 'medium' | 'low';
  metadata: PreviewMessageMetadata;
  products?: PreviewProduct[];
}

/**
 * Request body for POST /api/v1/preview/message
 */
export interface PreviewMessageRequest {
  message: string;
  previewSessionId: string;
}

/**
 * Response from DELETE /api/v1/preview/conversation
 */
export interface PreviewResetResponse {
  cleared: boolean;
  message: string;
}

/**
 * MinimalEnvelope wrapper for all responses
 */
export interface PreviewEnvelope<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

/**
 * Error response from preview endpoints
 */
export interface PreviewErrorResponse {
  detail?: {
    error_code: number;
    message: string;
  };
  message?: string;
}

/**
 * Preview Mode error codes from backend
 */
export enum PreviewErrorCode {
  // Message validation errors (4300-4309)
  INVALID_MESSAGE_FORMAT = 4300,
  MESSAGE_TOO_LONG = 4301,

  // Session errors (4310-4319)
  SESSION_NOT_FOUND = 4310,
  SESSION_EXPIRED = 4350,

  // Bot response errors (4320-4329)
  FAILED_TO_GENERATE = 4303,
  BOT_CONFIG_INCOMPLETE = 4304,

  // Reset errors (4350-4359)
  FAILED_TO_RESET = 4351,
}

/**
 * Preview API Service
 */
export const previewService = {
  /**
   * Start a new preview conversation session
   *
   * POST /api/v1/preview/conversation
   *
   * @returns Promise with preview session info and starter prompts
   */
  async startPreviewSession(): Promise<PreviewSessionResponse> {
    const response = await apiClient.post<PreviewSessionResponse>(
      '/api/v1/preview/conversation'
    );
    return response.data;
  },

  /**
   * Send a message in preview mode
   *
   * POST /api/v1/preview/message
   *
   * @param message - The message text to send
   * @param previewSessionId - The preview session ID
   * @returns Promise with bot response and confidence metadata
   */
  async sendPreviewMessage(
    message: string,
    previewSessionId: string
  ): Promise<PreviewMessageResponse> {
    const request: PreviewMessageRequest = {
      message,
      previewSessionId,
    };

    const response = await apiClient.post<PreviewMessageResponse>(
      '/api/v1/preview/message',
      request
    );
    return response.data;
  },

  /**
   * Reset the current preview conversation
   *
   * DELETE /api/v1/preview/conversation/{preview_session_id}
   *
   * @param previewSessionId - The preview session ID to reset
   * @returns Promise with reset confirmation
   */
  async resetPreviewConversation(
    previewSessionId: string
  ): Promise<PreviewResetResponse> {
    const response = await apiClient.delete<PreviewResetResponse>(
      `/api/v1/preview/conversation/${previewSessionId}`
    );
    return response.data;
  },
};
