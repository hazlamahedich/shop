import { useCallback } from 'react';
import type { WidgetConfig, WidgetMessage } from '../types/widget';
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

  return {
    sendMessage,
    getConfig,
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
