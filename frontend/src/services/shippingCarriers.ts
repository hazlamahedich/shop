/**
 * Shipping Carriers Service
 *
 * Story 6.3: Carrier Configuration API
 *
 * Provides client-side API for shipping carrier management:
 * - Get supported carriers (290+ international carriers)
 * - Get Shopify-supported carriers
 * - Detect carrier from tracking number
 * - CRUD operations for merchant's custom carriers
 *
 * API Endpoints:
 * - GET /api/carriers/supported - List all supported carriers
 * - GET /api/carriers/shopify - List Shopify-supported carriers
 * - POST /api/carriers/detect - Detect carrier from tracking number
 * - GET /api/merchants/{id}/carriers - List merchant's custom carriers
 * - POST /api/merchants/{id}/carriers - Create custom carrier
 * - GET /api/merchants/{id}/carriers/{cid} - Get single carrier
 * - PUT /api/merchants/{id}/carriers/{cid} - Update carrier
 * - DELETE /api/merchants/{id}/carriers/{cid} - Delete carrier
 */

import { apiClient } from './api';

/**
 * Supported carrier information
 */
export interface SupportedCarrier {
  name: string;
  region: string;
  pattern?: string;
  tracking_url_template: string;
}

/**
 * Shopify carrier information
 */
export interface ShopifyCarrier {
  name: string;
  url_template: string;
}

/**
 * Carrier detection request
 */
export interface CarrierDetectionRequest {
  tracking_number: string;
  merchant_id?: number;
  tracking_company?: string;
}

/**
 * Carrier detection result
 */
export interface CarrierDetectionResult {
  carrier_name: string | null;
  tracking_url: string | null;
  detection_method: 'custom' | 'shopify' | 'pattern' | 'none';
}

/**
 * Custom carrier configuration
 */
export interface CarrierConfig {
  id: number;
  merchant_id: number;
  carrier_name: string;
  tracking_url_template: string;
  tracking_number_pattern: string | null;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

/**
 * Create custom carrier request
 */
export interface CreateCarrierRequest {
  carrier_name: string;
  tracking_url_template: string;
  tracking_number_pattern?: string | null;
  is_active?: boolean;
  priority?: number;
}

/**
 * Update custom carrier request
 */
export interface UpdateCarrierRequest {
  carrier_name?: string;
  tracking_url_template?: string;
  tracking_number_pattern?: string | null;
  is_active?: boolean;
  priority?: number;
}

/**
 * Error response from carrier endpoints
 */
export interface CarrierErrorResponse {
  detail?: string;
  message?: string;
}

/**
 * Shipping Carriers Service
 */
class ShippingCarriersService {
  /**
   * Get all supported carriers (290+ international carriers)
   */
  async getSupportedCarriers(): Promise<SupportedCarrier[]> {
    const response = await apiClient.request<SupportedCarrier[]>(
      '/api/carriers/supported',
      { method: 'GET' }
    );
    return response.data;
  }

  /**
   * Get Shopify-supported carriers
   */
  async getShopifyCarriers(): Promise<ShopifyCarrier[]> {
    const response = await apiClient.request<ShopifyCarrier[]>(
      '/api/carriers/shopify',
      { method: 'GET' }
    );
    return response.data;
  }

  /**
   * Detect carrier from tracking number
   */
  async detectCarrier(
    request: CarrierDetectionRequest
  ): Promise<CarrierDetectionResult> {
    const response = await apiClient.request<CarrierDetectionResult>(
      '/api/carriers/detect',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    return response.data;
  }

  /**
   * Get merchant's custom carriers
   */
  async getMerchantCarriers(merchantId: number): Promise<CarrierConfig[]> {
    const response = await apiClient.request<CarrierConfig[]>(
      `/api/carriers/merchants/${merchantId}/carriers`,
      { method: 'GET' }
    );
    return response.data;
  }

  /**
   * Create custom carrier
   */
  async createCarrier(
    merchantId: number,
    request: CreateCarrierRequest
  ): Promise<CarrierConfig> {
    const response = await apiClient.request<CarrierConfig>(
      `/api/carriers/merchants/${merchantId}/carriers`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    return response.data;
  }

  /**
   * Get single carrier
   */
  async getCarrier(
    merchantId: number,
    carrierId: number
  ): Promise<CarrierConfig> {
    const response = await apiClient.request<CarrierConfig>(
      `/api/carriers/merchants/${merchantId}/carriers/${carrierId}`,
      { method: 'GET' }
    );
    return response.data;
  }

  /**
   * Update custom carrier
   */
  async updateCarrier(
    merchantId: number,
    carrierId: number,
    request: UpdateCarrierRequest
  ): Promise<CarrierConfig> {
    const response = await apiClient.request<CarrierConfig>(
      `/api/carriers/merchants/${merchantId}/carriers/${carrierId}`,
      {
        method: 'PUT',
        body: JSON.stringify(request),
      }
    );
    return response.data;
  }

  /**
   * Delete custom carrier
   */
  async deleteCarrier(
    merchantId: number,
    carrierId: number
  ): Promise<void> {
    await apiClient.request<void>(
      `/api/carriers/merchants/${merchantId}/carriers/${carrierId}`,
      { method: 'DELETE' }
    );
  }
}

export const shippingCarriersService = new ShippingCarriersService();
