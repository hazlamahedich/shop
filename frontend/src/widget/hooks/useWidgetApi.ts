import { useCallback } from 'react';
import type {
  WidgetCart,
  WidgetCheckoutResult,
  WidgetConfig,
  WidgetMessage,
  WidgetSearchResult,
} from '../types/widget';
import { widgetClient, WidgetApiException } from '../api/widgetClient';

export function useWidgetApi() {
  const sendMessage = useCallback(
    async (sessionId: string, content: string): Promise<WidgetMessage> => {
      return widgetClient.sendMessage(sessionId, content);
    },
    []
  );

  const getConfig = useCallback(async (merchantId: string): Promise<WidgetConfig | null> => {
    try {
      return await widgetClient.getConfig(merchantId);
    } catch (error) {
      if (error instanceof WidgetApiException && error.code === 12005) {
        return getDefaultConfig();
      }
      throw error;
    }
  }, []);

  const searchProducts = useCallback(
    async (sessionId: string, query: string): Promise<WidgetSearchResult> => {
      return widgetClient.searchProducts(sessionId, query);
    },
    []
  );

  const getCart = useCallback(async (sessionId: string): Promise<WidgetCart> => {
    return widgetClient.getCart(sessionId);
  }, []);

  const addToCart = useCallback(
    async (sessionId: string, variantId: string, quantity: number = 1): Promise<WidgetCart> => {
      return widgetClient.addToCart(sessionId, variantId, quantity);
    },
    []
  );

  const removeFromCart = useCallback(
    async (sessionId: string, variantId: string): Promise<WidgetCart> => {
      return widgetClient.removeFromCart(sessionId, variantId);
    },
    []
  );

  const checkout = useCallback(
    async (sessionId: string): Promise<WidgetCheckoutResult> => {
      return widgetClient.checkout(sessionId);
    },
    []
  );

  return {
    sendMessage,
    getConfig,
    searchProducts,
    getCart,
    addToCart,
    removeFromCart,
    checkout,
  };
}

function getDefaultConfig(): WidgetConfig {
  return {
    enabled: true,
    botName: 'Assistant',
    welcomeMessage: 'Hello! How can I help you today?',
    theme: {
      primaryColor: '#6366f1',
      backgroundColor: '#ffffff',
      textColor: '#1f2937',
      botBubbleColor: '#f3f4f6',
      userBubbleColor: '#6366f1',
      position: 'bottom-right',
      borderRadius: 16,
      width: 380,
      height: 600,
      fontFamily: 'Inter, sans-serif',
      fontSize: 14,
    },
    allowedDomains: [],
  };
}
