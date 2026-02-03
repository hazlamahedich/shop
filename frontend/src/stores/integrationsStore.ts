/**
 * Integrations Store - Zustand state management for Facebook and Shopify integration
 * Handles OAuth flow, connection status, and webhook verification
 */

import { create } from 'zustand';

// Types
export type ConnectionStatus = 'idle' | 'connecting' | 'connected' | 'error';

export interface FacebookConnection {
  connected: boolean;
  pageId?: string;
  pageName?: string;
  pagePictureUrl?: string;
  connectedAt?: string;
  webhookVerified: boolean;
}

export interface ShopifyConnection {
  connected: boolean;
  shopDomain?: string;
  shopName?: string;
  connectedAt?: string;
  storefrontApiConnected: boolean;
  adminApiConnected: boolean;
  webhookSubscribed: boolean;
}

export interface IntegrationsState {
  // Facebook connection state
  facebookStatus: ConnectionStatus;
  facebookConnection: FacebookConnection;
  facebookError?: string;

  // Shopify connection state
  shopifyStatus: ConnectionStatus;
  shopifyConnection: ShopifyConnection;
  shopifyError?: string;

  // Merchant ID for API calls
  merchantId: number;

  // Actions
  initiateFacebookOAuth: () => Promise<void>;
  checkFacebookStatus: () => Promise<void>;
  disconnectFacebook: () => Promise<void>;

  initiateShopifyOAuth: (shopDomain: string) => Promise<void>;
  checkShopifyStatus: () => Promise<void>;
  disconnectShopify: () => Promise<void>;

  clearError: () => void;
  clearFacebookError: () => void;
  clearShopifyError: () => void;
  setMerchantId: (merchantId: number) => void;
  reset: () => void;
}

// Initial state
const initialState = {
  facebookStatus: 'idle' as ConnectionStatus,
  facebookConnection: {
    connected: false,
    webhookVerified: false,
  },
  facebookError: undefined as string | undefined,

  shopifyStatus: 'idle' as ConnectionStatus,
  shopifyConnection: {
    connected: false,
    storefrontApiConnected: false,
    adminApiConnected: false,
    webhookSubscribed: false,
  },
  shopifyError: undefined as string | undefined,

  merchantId: 1,
};

/**
 * Integrations store using Zustand
 */
export const useIntegrationsStore = create<IntegrationsState>((set, get) => ({
  ...initialState,

  /**
   * Initiate Facebook OAuth flow
   * Opens popup window for Facebook authorization
   */
  initiateFacebookOAuth: async () => {
    const { merchantId } = get();
    set({ facebookStatus: 'connecting', facebookError: undefined });

    try {
      // Get OAuth URL from backend
      const response = await fetch(`/api/integrations/facebook/authorize?merchant_id=${merchantId}`);
      if (!response.ok) {
        throw new Error('Failed to initiate OAuth');
      }

      const { data } = await response.json();
      const { authUrl } = data;

      // Open popup window for OAuth
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      const popup = window.open(
        authUrl,
        'facebook-oauth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      if (!popup) {
        throw new Error('Popup blocked - please allow popups for this site');
      }

      // Listen for popup messages
      const messageHandler = (event: MessageEvent) => {
        // Verify origin (security)
        if (event.origin !== window.location.origin) return;

        if (event.data.type === 'facebook-oauth-success') {
          // Connection successful - refresh status
          get().checkFacebookStatus();
        } else if (event.data.type === 'facebook-oauth-error') {
          // Connection failed - show error
          set({
            facebookStatus: 'error',
            facebookError: event.data.error || 'Connection failed',
          });
        }

        // Clean up listener and close popup
        window.removeEventListener('message', messageHandler);
        popup?.close();
      };

      window.addEventListener('message', messageHandler);

    } catch (error) {
      set({
        facebookStatus: 'error',
        facebookError: error instanceof Error ? error.message : 'Failed to connect Facebook',
      });
    }
  },

  /**
   * Check current Facebook connection status
   */
  checkFacebookStatus: async () => {
    const { merchantId } = get();
    try {
      const response = await fetch(`/api/integrations/facebook/status?merchant_id=${merchantId}`);
      if (!response.ok) {
        throw new Error('Failed to check status');
      }

      const { data } = await response.json();

      set({
        facebookStatus: data.connected ? 'connected' : 'idle',
        facebookConnection: {
          connected: data.connected,
          pageId: data.pageId,
          pageName: data.pageName,
          pagePictureUrl: data.pagePictureUrl,
          connectedAt: data.connectedAt,
          webhookVerified: data.webhookVerified || false,
        },
        facebookError: undefined,
      });
    } catch (error) {
      console.error('Failed to check Facebook status:', error);
      set({
        facebookStatus: 'error',
        facebookError: 'Failed to check connection status',
      });
    }
  },

  /**
   * Disconnect Facebook integration
   */
  disconnectFacebook: async () => {
    const { merchantId } = get();
    set({ facebookStatus: 'connecting', facebookError: undefined });

    try {
      const response = await fetch(`/api/integrations/facebook/disconnect?merchant_id=${merchantId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to disconnect');
      }

      set({
        facebookStatus: 'idle',
        facebookConnection: {
          connected: false,
          webhookVerified: false,
        },
      });
    } catch (error) {
      set({
        facebookStatus: 'error',
        facebookError: error instanceof Error ? error.message : 'Failed to disconnect',
      });
    }
  },

  /**
   * Clear error state
   */
  clearError: () => {
    set({ facebookError: undefined, shopifyError: undefined });
  },

  /**
   * Clear Facebook error state only
   */
  clearFacebookError: () => {
    set({ facebookError: undefined });
  },

  /**
   * Clear Shopify error state only
   */
  clearShopifyError: () => {
    set({ shopifyError: undefined });
  },

  /**
   * Initiate Shopify OAuth flow
   * Opens popup window for Shopify authorization
   */
  initiateShopifyOAuth: async (shopDomain: string) => {
    const { merchantId } = get();
    set({ shopifyStatus: 'connecting', shopifyError: undefined });

    // Validate shop domain format
    const shopDomainPattern = /^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$/;
    if (!shopDomainPattern.test(shopDomain)) {
      set({
        shopifyStatus: 'error',
        shopifyError: 'Please enter a valid Shopify store domain (e.g., mystore.myshopify.com)',
      });
      return;
    }

    try {
      // Get OAuth URL from backend
      const response = await fetch(
        `/api/integrations/shopify/authorize?merchant_id=${merchantId}&shop_domain=${shopDomain}`
      );
      if (!response.ok) {
        throw new Error('Failed to initiate OAuth');
      }

      const { data } = await response.json();
      const { authUrl } = data;

      // Open popup window for OAuth
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      const popup = window.open(
        authUrl,
        'shopify-oauth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      if (!popup) {
        throw new Error('Popup blocked - please allow popups for this site');
      }

      // Listen for popup messages
      const messageHandler = (event: MessageEvent) => {
        // Verify origin (security)
        if (event.origin !== window.location.origin) return;

        if (event.data.type === 'shopify-oauth-success') {
          // Connection successful - refresh status
          get().checkShopifyStatus();
        } else if (event.data.type === 'shopify-oauth-error') {
          // Connection failed - show error
          set({
            shopifyStatus: 'error',
            shopifyError: event.data.error || 'Connection failed',
          });
        }

        // Clean up listener and close popup
        window.removeEventListener('message', messageHandler);
        popup?.close();
      };

      window.addEventListener('message', messageHandler);

    } catch (error) {
      set({
        shopifyStatus: 'error',
        shopifyError: error instanceof Error ? error.message : 'Failed to connect Shopify',
      });
    }
  },

  /**
   * Check current Shopify connection status
   */
  checkShopifyStatus: async () => {
    const { merchantId } = get();
    try {
      const response = await fetch(`/api/integrations/shopify/status?merchant_id=${merchantId}`);
      if (!response.ok) {
        throw new Error('Failed to check status');
      }

      const { data } = await response.json();

      set({
        shopifyStatus: data.connected ? 'connected' : 'idle',
        shopifyConnection: {
          connected: data.connected,
          shopDomain: data.shopDomain,
          shopName: data.shopName,
          connectedAt: data.connectedAt,
          storefrontApiConnected: data.storefrontApiConnected || false,
          adminApiConnected: data.adminApiConnected || false,
          webhookSubscribed: data.webhookSubscribed || false,
        },
        shopifyError: undefined,
      });
    } catch (error) {
      console.error('Failed to check Shopify status:', error);
      set({
        shopifyStatus: 'error',
        shopifyError: 'Failed to check connection status',
      });
    }
  },

  /**
   * Disconnect Shopify integration
   */
  disconnectShopify: async () => {
    const { merchantId } = get();
    set({ shopifyStatus: 'connecting', shopifyError: undefined });

    try {
      const response = await fetch(`/api/integrations/shopify/disconnect?merchant_id=${merchantId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to disconnect');
      }

      set({
        shopifyStatus: 'idle',
        shopifyConnection: {
          connected: false,
          storefrontApiConnected: false,
          adminApiConnected: false,
          webhookSubscribed: false,
        },
      });
    } catch (error) {
      set({
        shopifyStatus: 'error',
        shopifyError: error instanceof Error ? error.message : 'Failed to disconnect',
      });
    }
  },

  /**
   * Set merchant ID for API calls
   */
  setMerchantId: (merchantId: number) => {
    set({ merchantId });
  },

  /**
   * Reset store to initial state
   */
  reset: () => {
    set(initialState);
  },
}));
