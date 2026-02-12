/**
 * Bot Configuration Service
 *
 * Story 1.12: Bot Naming
 * Story 1.14: Smart Greeting Templates
 * Story 1.15: Product Highlight Pins
 *
 * Provides client-side API for bot configuration management:
 * - Get bot configuration (bot_name, personality, custom_greeting)
 * - Update bot name
 * - Get/Update greeting configuration
 * - Product pin management (Story 1.15)
 *
 * API Endpoints:
 * - GET /api/v1/merchant/bot-config - Get current bot configuration
 * - PUT /api/v1/merchant/bot-config - Update bot configuration
 * - GET /api/v1/merchant/greeting-config - Get greeting configuration
 * - PUT /api/v1/merchant/greeting-config - Update greeting configuration
 * - GET /api/v1/merchant/product-pins - Get products with pin status
 * - POST /api/v1/merchant/product-pins - Pin a product
 * - DELETE /api/v1/merchant/product-pins/{product_id} - Unpin a product
 * - POST /api/v1/merchant/product-pins/reorder - Reorder pinned products
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
 * Story 1.14: Response from greeting config endpoints
 */
export interface GreetingConfigResponse {
  greetingTemplate: string | null;
  useCustomGreeting: boolean;
  personality: string | null;
  defaultTemplate: string | null;
  availableVariables: string[];
}

/**
 * Request body for updating bot name
 */
export interface BotNameUpdateRequest {
  bot_name?: string | null;
}

/**
 * Story 1.14: Request body for updating greeting config
 */
export interface GreetingConfigUpdateRequest {
  greeting_template?: string | null;
  use_custom_greeting?: boolean;
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
  // Product pin errors (4250-4299) - Story 1.15
  PRODUCT_PIN_LIMIT_REACHED = 4250,
  PRODUCT_PIN_ALREADY_PINNED = 4251,
  PRODUCT_PIN_NOT_FOUND = 4252,
}

/**
 * Bot Config Service Error
 */
export class BotConfigError extends Error {
  public code?: BotConfigErrorCode;
  public status?: number;

  constructor(
    message: string,
    code?: BotConfigErrorCode,
    status?: number
  ) {
    super(message);
    this.name = 'BotConfigError';
    this.code = code;
    this.status = status;
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
      const status = (error as any)?.status ?? 500;
      throw new BotConfigError(errorMessage, undefined, status);
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
      let status = 500;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Extract error code from error object
      const errorObj = error as any;
      if (errorObj && typeof errorObj.status === 'number') {
        status = errorObj.status;
      }
      if (errorObj && typeof errorObj.code === 'number') {
        errorCode = errorObj.code;
      }

      throw new BotConfigError(errorMessage, errorCode, status);
    }
  },

  /**
   * Get current merchant's greeting configuration (Story 1.14)
   *
   * @returns Greeting configuration with template, use_custom_greeting, etc.
   * @throws BotConfigError if request fails
   */
  async fetchGreetingConfig(): Promise<GreetingConfigResponse> {
    try {
      const response = await apiClient.get<GreetingConfigResponse>(
        '/api/v1/merchant/greeting-config'
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch greeting configuration';
      const status = (error as any)?.status ?? 500;
      throw new BotConfigError(errorMessage, undefined, status);
    }
  },

  /**
   * Update merchant's greeting configuration (Story 1.14)
   *
   * Allows updating greeting template and use_custom_greeting flag.
   * Empty strings or whitespace-only strings will clear the custom greeting.
   *
   * @param update - Greeting configuration update with optional fields
   * @returns Updated greeting configuration
   * @throws BotConfigError if request fails
   */
  async updateGreetingConfig(update: GreetingConfigUpdateRequest): Promise<GreetingConfigResponse> {
    try {
      const response = await apiClient.put<GreetingConfigResponse>(
        '/api/v1/merchant/greeting-config',
        update
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to update greeting configuration';
      let errorCode: BotConfigErrorCode | undefined;
      let status = 500;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Extract error code from error object
      const errorObj = error as any;
      if (errorObj && typeof errorObj.status === 'number') {
        status = errorObj.status;
      }
      if (errorObj && typeof errorObj.code === 'number') {
        errorCode = errorObj.code;
      }

      throw new BotConfigError(errorMessage, errorCode, status);
    }
  },
};

/**
 * Story 1.15: Product Highlight Pins
 *
 * Product pin related types and API functions
 */

/**
 * Single product item with pin status
 */
export interface ProductPinItem {
  productId: string;
  title: string;
  imageUrl?: string;
  isPinned: boolean;
  pinnedOrder?: number;
  pinnedAt?: string;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
}

/**
 * Response from product pins endpoints
 */
export interface ProductPinsResponse {
  products: ProductPinItem[];
  pagination?: PaginationMeta;
  pinLimit: number;
  pinnedCount: number;
}

/**
 * Request body for pinning a product
 */
export interface ProductPinRequest {
  productId: string;
}

/**
 * Response for single product pin operation
 */
export interface ProductPinResponse {
  productId: string;
  isPinned: boolean;
  pinnedOrder?: number;
  pinnedAt?: string;
}

/**
 * Request body for reordering pinned products
 */
export interface ReorderPinsRequest {
  productOrders: Array<{ productId: string; order: number }>;
}

/**
 * Product Pin API Client
 *
 * Story 1.15: Product Highlight Pins
 *
 * Handles all product pin operations with automatic error handling
 * and response parsing.
 */
export const productPinApi = {
  /**
   * Get products with pin status
   *
   * @param search - Optional search query for filtering products
   * @param pinnedOnly - If true, return only pinned products
   * @param page - Page number for pagination (default: 1)
   * @param limit - Items per page (default: 20)
   * @returns Product list with pin status and pagination info
   * @throws BotConfigError if request fails
   */
  async fetchProductsWithPinStatus(
    search?: string,
    pinnedOnly: boolean = false,
    page: number = 1,
    limit: number = 20,
  ): Promise<ProductPinsResponse> {
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (pinnedOnly) params.append('pinned_only', 'true');
      params.append('page', page.toString());
      params.append('limit', limit.toString());

      const response = await apiClient.get<ProductPinsResponse>(
        `/api/v1/merchant/product-pins?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch products';
      const status = (error as any)?.status ?? 500;
      throw new BotConfigError(errorMessage, undefined, status);
    }
  },

  /**
   * Pin a product
   *
   * @param productId - Shopify product ID to pin
   * @returns Updated pin status
   * @throws BotConfigError if request fails or limit reached
   */
  async pinProduct(productId: string): Promise<ProductPinResponse> {
    try {
      const response = await apiClient.post<ProductPinResponse>(
        '/api/v1/merchant/product-pins',
        { productId: productId }
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to pin product';
      let errorCode: BotConfigErrorCode | undefined;
      let status = 500;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorObj = error as any;
      if (errorObj && typeof errorObj.status === 'number') {
        status = errorObj.status;
      }
      if (errorObj && typeof errorObj.code === 'number') {
        errorCode = errorObj.code;
      }

      throw new BotConfigError(errorMessage, errorCode, status);
    }
  },

  /**
   * Unpin a product
   *
   * @param productId - Shopify product ID to unpin
   * @returns Updated pin status
   * @throws BotConfigError if request fails
   */
  async unpinProduct(productId: string): Promise<ProductPinResponse> {
    try {
      const response = await apiClient.delete<ProductPinResponse>(
        `/api/v1/merchant/product-pins/${encodeURIComponent(productId)}`
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to unpin product';
      let errorCode: BotConfigErrorCode | undefined;
      let status = 500;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorObj = error as any;
      if (errorObj && typeof errorObj.status === 'number') {
        status = errorObj.status;
      }
      if (errorObj && typeof errorObj.code === 'number') {
        errorCode = errorObj.code;
      }

      throw new BotConfigError(errorMessage, errorCode, status);
    }
  },

  /**
   * Reorder pinned products
   *
   * @param productOrders - Array of product IDs with their new order values
   * @returns Success confirmation
   * @throws BotConfigError if request fails
   */
  async reorderPinnedProducts(productOrders: ReorderPinsRequest['product_orders']): Promise<void> {
    try {
      await apiClient.post<void>(
        '/api/v1/merchant/product-pins/reorder',
        { productOrders: productOrders }
      );
    } catch (error) {
      let errorMessage = 'Failed to reorder products';
      let errorCode: BotConfigErrorCode | undefined;
      let status = 500;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorObj = error as any;
      if (errorObj && typeof errorObj.status === 'number') {
        status = errorObj.status;
      }
      if (errorObj && typeof errorObj.code === 'number') {
        errorCode = errorObj.code;
      }

      throw new BotConfigError(errorMessage, errorCode, status);
    }
  },
};
