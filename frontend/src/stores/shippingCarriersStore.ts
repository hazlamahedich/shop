/**
 * Shipping Carriers Store - Zustand state management for carrier configuration
 *
 * Story 6.4: Frontend Settings Page
 *
 * Manages custom carrier configuration state including:
 * - Custom carriers array with CRUD operations
 * - Loading and error states
 * - Carrier creation, updates, and deletion
 */

import { create } from 'zustand';
import {
  shippingCarriersService,
  type CarrierConfig,
  type CreateCarrierRequest,
  type UpdateCarrierRequest,
  type SupportedCarrier,
  type ShopifyCarrier,
} from '../services/shippingCarriers';

type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Shipping Carriers Store State
 */
export interface ShippingCarriersState {
  carriers: CarrierConfig[];
  supportedCarriers: SupportedCarrier[];
  shopifyCarriers: ShopifyCarrier[];
  loadingState: LoadingState;
  carriersLoadingState: LoadingState;
  error: string | null;

  fetchCarriers: (merchantId: number) => Promise<void>;
  fetchSupportedCarriers: () => Promise<void>;
  fetchShopifyCarriers: () => Promise<void>;
  createCarrier: (merchantId: number, request: CreateCarrierRequest) => Promise<CarrierConfig>;
  updateCarrier: (merchantId: number, carrierId: number, request: UpdateCarrierRequest) => Promise<void>;
  deleteCarrier: (merchantId: number, carrierId: number) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useShippingCarriersStore = create<ShippingCarriersState>()((set, get) => ({
  carriers: [],
  supportedCarriers: [],
  shopifyCarriers: [],
  loadingState: 'idle',
  carriersLoadingState: 'idle',
  error: null,

  fetchCarriers: async (merchantId: number) => {
    set({ carriersLoadingState: 'loading', error: null });

    try {
      const carriers = await shippingCarriersService.getMerchantCarriers(merchantId);
      set({
        carriers,
        carriersLoadingState: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch carriers';
      set({
        carriersLoadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchSupportedCarriers: async () => {
    set({ loadingState: 'loading', error: null });

    try {
      const supportedCarriers = await shippingCarriersService.getSupportedCarriers();
      set({
        supportedCarriers,
        loadingState: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch supported carriers';
      set({
        loadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  fetchShopifyCarriers: async () => {
    set({ loadingState: 'loading', error: null });

    try {
      const shopifyCarriers = await shippingCarriersService.getShopifyCarriers();
      set({
        shopifyCarriers,
        loadingState: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to fetch Shopify carriers';
      set({
        loadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  createCarrier: async (merchantId: number, request: CreateCarrierRequest) => {
    set({ carriersLoadingState: 'loading', error: null });

    try {
      const newCarrier = await shippingCarriersService.createCarrier(merchantId, request);
      set({
        carriers: [...get().carriers, newCarrier],
        carriersLoadingState: 'success',
      });
      return newCarrier;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to create carrier';
      set({
        carriersLoadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  updateCarrier: async (merchantId: number, carrierId: number, request: UpdateCarrierRequest) => {
    set({ carriersLoadingState: 'loading', error: null });

    try {
      const updatedCarrier = await shippingCarriersService.updateCarrier(
        merchantId,
        carrierId,
        request
      );
      set({
        carriers: get().carriers.map((c) => (c.id === carrierId ? updatedCarrier : c)),
        carriersLoadingState: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to update carrier';
      set({
        carriersLoadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  deleteCarrier: async (merchantId: number, carrierId: number) => {
    set({ carriersLoadingState: 'loading', error: null });

    try {
      await shippingCarriersService.deleteCarrier(merchantId, carrierId);
      set({
        carriers: get().carriers.filter((c) => c.id !== carrierId),
        carriersLoadingState: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to delete carrier';
      set({
        carriersLoadingState: 'error',
        error: errorMessage,
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      carriers: [],
      supportedCarriers: [],
      shopifyCarriers: [],
      loadingState: 'idle',
      carriersLoadingState: 'idle',
      error: null,
    });
  },
}));
