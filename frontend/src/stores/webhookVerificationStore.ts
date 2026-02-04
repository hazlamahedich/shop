import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface WebhookStatus {
  webhookUrl: string;
  connected: boolean;
  lastWebhookAt?: string;
  lastVerifiedAt?: string;
  subscriptionStatus: 'active' | 'inactive';
  topics: string[];
  error?: string;
}

export interface WebhookVerificationStatus {
  facebook: WebhookStatus;
  shopify: WebhookStatus;
  overallStatus: 'ready' | 'partial' | 'not_connected';
  canGoLive: boolean;
}

export interface WebhookTestResult {
  testId: string;
  status: 'success' | 'failed';
  message: string;
  testMessageId?: string;
  deliveredAt?: string;
  conversationCreated?: boolean;
  testOrderId?: string;
  webhookReceivedAt?: string;
  orderStored?: boolean;
  pageId?: string;
  shopDomain?: string;
  webhookActive?: boolean;
}

export interface WebhookResubscribeResult {
  platform: 'facebook' | 'shopify';
  status: 'success' | 'partial' | 'failed';
  message: string;
  topics: Array<{ topic: string; success?: boolean; error?: string }>;
  subscribedAt?: string;
}

interface WebhookVerificationState {
  status: WebhookVerificationStatus | null;
  isTestingFacebook: boolean;
  isTestingShopify: boolean;
  isResubscribingFacebook: boolean;
  isResubscribingShopify: boolean;
  error?: string;
  lastTestResult?: WebhookTestResult;
  lastResubscribeResult?: WebhookResubscribeResult;

  // Actions
  getStatus: (merchantId: number) => Promise<void>;
  testFacebookWebhook: (merchantId: number) => Promise<WebhookTestResult>;
  testShopifyWebhook: (merchantId: number) => Promise<WebhookTestResult>;
  resubscribeFacebookWebhook: (merchantId: number) => Promise<WebhookResubscribeResult>;
  resubscribeShopifyWebhook: (merchantId: number) => Promise<WebhookResubscribeResult>;
  clearError: () => void;
}

const API_BASE = '/api/webhooks/verification';

export const useWebhookVerificationStore = create<WebhookVerificationState>()(
  persist(
    (set, get) => ({
      status: null,
      isTestingFacebook: false,
      isTestingShopify: false,
      isResubscribingFacebook: false,
      isResubscribingShopify: false,

      clearError: () => set({ error: undefined }),

      getStatus: async (merchantId: number) => {
        set({ error: undefined });
        try {
          const response = await fetch(`${API_BASE}/status?merchant_id=${merchantId}`);

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.detail?.message || data.detail || 'Failed to get webhook status');
          }

          set({ status: data.data });
        } catch (error) {
          const errorMessage = (error as Error).message;
          set({ error: errorMessage });
          throw error;
        }
      },

      testFacebookWebhook: async (merchantId: number) => {
        set({ isTestingFacebook: true, error: undefined, lastTestResult: undefined });
        try {
          const response = await fetch(`${API_BASE}/test-facebook?merchant_id=${merchantId}`, {
            method: 'POST',
          });

          const data = await response.json();

          if (!response.ok) {
            const errorDetail = data.detail;
            const errorMessage = typeof errorDetail === 'string'
              ? errorDetail
              : errorDetail?.message || 'Facebook webhook test failed';

            const result: WebhookTestResult = {
              testId: crypto.randomUUID(),
              status: 'failed',
              message: errorMessage,
            };

            set({
              lastTestResult: result,
              error: errorMessage,
              isTestingFacebook: false,
            });
            throw new Error(errorMessage);
          }

          const result: WebhookTestResult = data.data;
          set({ lastTestResult: result, isTestingFacebook: false });
          return result;
        } catch (error) {
          if (!get().lastTestResult) {
            set({
              lastTestResult: {
                testId: crypto.randomUUID(),
                status: 'failed',
                message: (error as Error).message,
              },
            });
          }
          set({ error: (error as Error).message, isTestingFacebook: false });
          throw error;
        }
      },

      testShopifyWebhook: async (merchantId: number) => {
        set({ isTestingShopify: true, error: undefined, lastTestResult: undefined });
        try {
          const response = await fetch(`${API_BASE}/test-shopify?merchant_id=${merchantId}`, {
            method: 'POST',
          });

          const data = await response.json();

          if (!response.ok) {
            const errorDetail = data.detail;
            const errorMessage = typeof errorDetail === 'string'
              ? errorDetail
              : errorDetail?.message || 'Shopify webhook test failed';

            const result: WebhookTestResult = {
              testId: crypto.randomUUID(),
              status: 'failed',
              message: errorMessage,
            };

            set({
              lastTestResult: result,
              error: errorMessage,
              isTestingShopify: false,
            });
            throw new Error(errorMessage);
          }

          const result: WebhookTestResult = data.data;
          set({ lastTestResult: result, isTestingShopify: false });
          return result;
        } catch (error) {
          if (!get().lastTestResult) {
            set({
              lastTestResult: {
                testId: crypto.randomUUID(),
                status: 'failed',
                message: (error as Error).message,
              },
            });
          }
          set({ error: (error as Error).message, isTestingShopify: false });
          throw error;
        }
      },

      resubscribeFacebookWebhook: async (merchantId: number) => {
        set({ isResubscribingFacebook: true, error: undefined, lastResubscribeResult: undefined });
        try {
          const response = await fetch(`${API_BASE}/resubscribe-facebook?merchant_id=${merchantId}`, {
            method: 'POST',
          });

          const data = await response.json();

          if (!response.ok) {
            const errorDetail = data.detail;
            const errorMessage = typeof errorDetail === 'string'
              ? errorDetail
              : errorDetail?.message || 'Facebook webhook re-subscription failed';

            const result: WebhookResubscribeResult = {
              platform: 'facebook',
              status: 'failed',
              message: errorMessage,
              topics: [],
            };

            set({
              lastResubscribeResult: result,
              error: errorMessage,
              isResubscribingFacebook: false,
            });
            throw new Error(errorMessage);
          }

          const result: WebhookResubscribeResult = data.data;
          set({ lastResubscribeResult: result, isResubscribingFacebook: false });

          // Refresh status after successful re-subscription
          await get().getStatus(merchantId);

          return result;
        } catch (error) {
          if (!get().lastResubscribeResult) {
            set({
              lastResubscribeResult: {
                platform: 'facebook',
                status: 'failed',
                message: (error as Error).message,
                topics: [],
              },
            });
          }
          set({ error: (error as Error).message, isResubscribingFacebook: false });
          throw error;
        }
      },

      resubscribeShopifyWebhook: async (merchantId: number) => {
        set({ isResubscribingShopify: true, error: undefined, lastResubscribeResult: undefined });
        try {
          const response = await fetch(`${API_BASE}/resubscribe-shopify?merchant_id=${merchantId}`, {
            method: 'POST',
          });

          const data = await response.json();

          if (!response.ok) {
            const errorDetail = data.detail;
            const errorMessage = typeof errorDetail === 'string'
              ? errorDetail
              : errorDetail?.message || 'Shopify webhook re-subscription failed';

            const result: WebhookResubscribeResult = {
              platform: 'shopify',
              status: 'failed',
              message: errorMessage,
              topics: [],
            };

            set({
              lastResubscribeResult: result,
              error: errorMessage,
              isResubscribingShopify: false,
            });
            throw new Error(errorMessage);
          }

          const result: WebhookResubscribeResult = data.data;
          set({ lastResubscribeResult: result, isResubscribingShopify: false });

          // Refresh status after successful re-subscription
          await get().getStatus(merchantId);

          return result;
        } catch (error) {
          if (!get().lastResubscribeResult) {
            set({
              lastResubscribeResult: {
                platform: 'shopify',
                status: 'failed',
                message: (error as Error).message,
                topics: [],
              },
            });
          }
          set({ error: (error as Error).message, isResubscribingShopify: false });
          throw error;
        }
      },
    }),
    {
      name: 'webhook-verification-storage',
      partialize: (state) => ({
        // Don't persist loading states or errors
        status: state.status,
      }),
    }
  )
);
