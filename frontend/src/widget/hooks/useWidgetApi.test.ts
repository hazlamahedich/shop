import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWidgetApi } from './useWidgetApi';

vi.mock('../api/widgetClient', () => ({
  widgetClient: {
    sendMessage: vi.fn(),
    getConfig: vi.fn(),
  },
}));

describe('useWidgetApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should send a message', async () => {
    const mockMessage = {
      messageId: 'msg-1',
      content: 'Hello!',
      sender: 'user' as const,
      createdAt: '2024-01-01T00:00:00Z',
    };

    const { widgetClient } = await import('../api/widgetClient');
    vi.mocked(widgetClient.sendMessage).mockResolvedValue(mockMessage);

    const { result } = renderHook(() => useWidgetApi());

    await act(async () => {
      const message = await result.current.sendMessage('session-1', 'Hello!');
      expect(message).toEqual(mockMessage);
    });
  });

  it('should get config', async () => {
    const mockConfig = {
      enabled: true,
      botName: 'TestBot',
      welcomeMessage: 'Hello!',
      theme: {
        primaryColor: '#6366f1',
        backgroundColor: '#ffffff',
        textColor: '#1f2937',
        botBubbleColor: '#f3f4f6',
        userBubbleColor: '#6366f1',
        position: 'bottom-right' as const,
        borderRadius: 16,
        width: 380,
        height: 600,
        fontFamily: 'Inter, sans-serif',
        fontSize: 14,
      },
      allowedDomains: [],
    };

    const { widgetClient } = await import('../api/widgetClient');
    vi.mocked(widgetClient.getConfig).mockResolvedValue(mockConfig);

    const { result } = renderHook(() => useWidgetApi());

    await act(async () => {
      const config = await result.current.getConfig('merchant-1');
      expect(config).toEqual(mockConfig);
    });
  });
});
