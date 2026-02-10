/**
 * Business Info & FAQ Service
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Provides client-side API for business information and FAQ management:
 * - Get and update business information (name, description, hours)
 * - CRUD operations for FAQ items
 * - FAQ reordering
 *
 * API Endpoints:
 * - GET /api/v1/merchant/business-info - Get current business information
 * - PUT /api/v1/merchant/business-info - Update business information
 * - GET /api/v1/merchant/faqs - Get all FAQ items
 * - POST /api/v1/merchant/faqs - Create new FAQ item
 * - PUT /api/v1/merchant/faqs/{faq_id} - Update FAQ item
 * - DELETE /api/v1/merchant/faqs/{faq_id} - Delete FAQ item
 * - PUT /api/v1/merchant/faqs/reorder - Reorder FAQ items
 */

import { apiClient } from './api';

/**
 * Response from business info endpoints
 */
export interface BusinessInfoResponse {
  business_name: string | null;
  business_description: string | null;
  business_hours: string | null;
}

/**
 * Request body for updating business information
 */
export interface BusinessInfoUpdateRequest {
  business_name?: string | null;
  business_description?: string | null;
  business_hours?: string | null;
}

/**
 * Response from FAQ endpoints
 */
export interface FaqResponse {
  id: number;
  question: string;
  answer: string;
  keywords: string | null;
  orderIndex: number;
  createdAt: string;
  updatedAt: string;
}

/**
 * Request body for creating a FAQ item
 */
export interface FaqCreateRequest {
  question: string;
  answer: string;
  keywords?: string | null;
  order_index?: number;
}

/**
 * Request body for updating a FAQ item
 */
export interface FaqUpdateRequest {
  question?: string;
  answer?: string;
  keywords?: string | null;
  order_index?: number;
}

/**
 * Request body for reordering FAQ items
 */
export interface FaqReorderRequest {
  faq_ids: number[];
}

/**
 * Error response from business info & FAQ endpoints
 */
export interface BusinessInfoErrorResponse {
  detail?: {
    error_code: number;
    message: string;
  };
  message?: string;
}

/**
 * Business Info & FAQ error codes from backend
 */
export enum BusinessInfoErrorCode {
  // Business Info errors (4100-4199)
  INVALID_BUSINESS_NAME = 4100,
  BUSINESS_DESCRIPTION_TOO_LONG = 4101,
  SAVE_FAILED = 4102,

  // FAQ errors (4150-4199)
  QUESTION_REQUIRED = 4150,
  ANSWER_REQUIRED = 4151,
  QUESTION_TOO_LONG = 4152,
  ANSWER_TOO_LONG = 4153,
  FAQ_NOT_FOUND = 4154,
  SAVE_FAILED_FAQ = 4155,
  FAQ_ACCESS_DENIED = 4156,
}

/**
 * Business Info & FAQ Service Error
 */
export class BusinessInfoError extends Error {
  constructor(
    message: string,
    public code?: BusinessInfoErrorCode,
    public status?: number
  ) {
    super(message);
    this.name = 'BusinessInfoError';
  }
}

/**
 * Business Info & FAQ API Client
 *
 * Handles all business info and FAQ operations with automatic error handling
 * and response parsing.
 */
export const businessInfoApi = {
  /**
   * Get the current merchant's business information
   *
   * @returns Business information with name, description, and hours
   * @throws BusinessInfoError if request fails
   */
  async getBusinessInfo(): Promise<BusinessInfoResponse> {
    try {
      const response = await apiClient.get<BusinessInfoResponse>(
        '/api/v1/merchant/business-info'
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch business information';
      throw new BusinessInfoError(errorMessage, undefined, (error as any)?.status);
    }
  },

  /**
   * Update the merchant's business information
   *
   * Allows updating business name, description, and/or hours.
   * Each field can be updated independently. Empty strings clear the field.
   *
   * @param update - Business information update with optional fields
   * @returns Updated business information
   * @throws BusinessInfoError if request fails
   */
  async updateBusinessInfo(
    update: BusinessInfoUpdateRequest
  ): Promise<BusinessInfoResponse> {
    try {
      const response = await apiClient.put<BusinessInfoResponse>(
        '/api/v1/merchant/business-info',
        update
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to update business information';
      let errorCode: BusinessInfoErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      // Extract error code from response if available
      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BusinessInfoError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },

  /**
   * Get all FAQ items for the merchant
   *
   * Returns FAQs ordered by their order_index field.
   *
   * @returns Array of FAQ items
   * @throws BusinessInfoError if request fails
   */
  async getFaqs(): Promise<FaqResponse[]> {
    try {
      const response = await apiClient.get<FaqResponse[]>(
        '/api/v1/merchant/faqs'
      );
      return response.data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch FAQ items';
      throw new BusinessInfoError(errorMessage, undefined, (error as any)?.status);
    }
  },

  /**
   * Create a new FAQ item
   *
   * Creates a new FAQ for the authenticated merchant.
   * The FAQ will be added at the end of the list.
   *
   * @param faq - FAQ creation data
   * @returns Created FAQ item
   * @throws BusinessInfoError if request fails
   */
  async createFaq(faq: FaqCreateRequest): Promise<FaqResponse> {
    try {
      const response = await apiClient.post<FaqResponse>(
        '/api/v1/merchant/faqs',
        faq
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to create FAQ item';
      let errorCode: BusinessInfoErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BusinessInfoError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },

  /**
   * Update an existing FAQ item
   *
   * Allows updating question, answer, keywords, and order.
   * Only the fields that are provided (non-undefined) will be updated.
   *
   * @param faqId - ID of the FAQ to update
   * @param update - FAQ update data
   * @returns Updated FAQ item
   * @throws BusinessInfoError if request fails
   */
  async updateFaq(faqId: number, update: FaqUpdateRequest): Promise<FaqResponse> {
    try {
      const response = await apiClient.put<FaqResponse>(
        `/api/v1/merchant/faqs/${faqId}`,
        update
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to update FAQ item';
      let errorCode: BusinessInfoErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BusinessInfoError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },

  /**
   * Delete an FAQ item
   *
   * Permanently deletes the specified FAQ.
   * Remaining FAQs will have their order_index values adjusted.
   *
   * @param faqId - ID of the FAQ to delete
   * @throws BusinessInfoError if request fails
   */
  async deleteFaq(faqId: number): Promise<void> {
    try {
      await apiClient.delete<{ success: true }>(
        `/api/v1/merchant/faqs/${faqId}`
      );
    } catch (error) {
      let errorMessage = 'Failed to delete FAQ item';
      let errorCode: BusinessInfoErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BusinessInfoError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },

  /**
   * Reorder FAQ items
   *
   * Allows merchants to specify the exact order of their FAQs
   * by providing an ordered list of FAQ IDs.
   *
   * @param faqIds - Array of FAQ IDs in the desired display order
   * @returns Array of reordered FAQ items
   * @throws BusinessInfoError if request fails
   */
  async reorderFaqs(faqIds: number[]): Promise<FaqResponse[]> {
    try {
      const response = await apiClient.put<FaqResponse[]>(
        '/api/v1/merchant/faqs/reorder',
        { faq_ids: faqIds } as FaqReorderRequest
      );
      return response.data;
    } catch (error) {
      let errorMessage = 'Failed to reorder FAQ items';
      let errorCode: BusinessInfoErrorCode | undefined;

      if (error instanceof Error) {
        errorMessage = error.message;
      }

      const errorData = (error as any)?.details;
      if (errorData?.error_code) {
        errorCode = errorData.error_code;
      }

      throw new BusinessInfoError(
        errorMessage,
        errorCode,
        (error as any)?.status
      );
    }
  },
};
