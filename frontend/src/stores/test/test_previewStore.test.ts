/**
 * Tests for Preview Store
 *
 * Story 1.13: Bot Preview Mode
 *
 * Tests the Zustand store for managing preview mode state.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { usePreviewStore } from '../previewStore';
import * as previewService from '../../services/preview';

// Mock the preview service
vi.mock('../../services/preview', () => ({
  previewService: {
    startPreviewSession: vi.fn(),
    sendPreviewMessage: vi.fn(),
    resetPreviewConversation: vi.fn(),
  },
}));

describe('PreviewStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    usePreviewStore.setState({
      messages: [],
      sessionId: null,
      isLoading: false,
      error: null,
      starterPrompts: [],
      botName: 'Bot',
    });
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => usePreviewStore());

      expect(result.current.messages).toEqual([]);
      expect(result.current.sessionId).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.starterPrompts).toEqual([]);
      expect(result.current.botName).toBe('Bot');
    });
  });

  describe('startSession', () => {
    it('should start a preview session successfully', async () => {
      const mockSessionData = {
        previewSessionId: 'test-session-id',
        merchantId: 123,
        createdAt: '2026-02-11T12:00:00Z',
        starterPrompts: [
          'What products do you have under $50?',
          'What are your business hours?',
        ],
      };

      vi.mocked(previewService.previewService.startPreviewSession).mockResolvedValue(
        mockSessionData
      );

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.startSession();
      });

      expect(result.current.sessionId).toBe('test-session-id');
      expect(result.current.starterPrompts).toEqual(mockSessionData.starterPrompts);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle start session errors', async () => {
      vi.mocked(previewService.previewService.startPreviewSession).mockRejectedValue(
        new Error('Failed to start session')
      );

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.startSession();
      });

      expect(result.current.error).toBe('Failed to start session');
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('sendMessage', () => {
    beforeEach(() => {
      // Set up a session for message tests
      usePreviewStore.setState({ sessionId: 'test-session-id' });
    });

    it('should send a message and receive bot response', async () => {
      const mockResponse = {
        response: 'Here are some products for you!',
        confidence: 85,
        confidenceLevel: 'high' as const,
        metadata: {
          intent: 'product_search',
          faqMatched: false,
          productsFound: 3,
          llmProvider: 'ollama',
        },
      };

      vi.mocked(previewService.previewService.sendPreviewMessage).mockResolvedValue(
        mockResponse
      );

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.sendMessage('What shoes do you have?');
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('What shoes do you have?');
      expect(result.current.messages[1].role).toBe('bot');
      expect(result.current.messages[1].content).toBe(mockResponse.response);
      expect(result.current.messages[1].confidence).toBe(85);
      expect(result.current.messages[1].confidenceLevel).toBe('high');
    });

    it('should not send empty messages', async () => {
      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.sendMessage('   ');
      });

      expect(result.current.messages).toHaveLength(0);
      expect(
        previewService.previewService.sendPreviewMessage
      ).not.toHaveBeenCalled();
    });

    it('should handle send message errors gracefully', async () => {
      vi.mocked(previewService.previewService.sendPreviewMessage).mockRejectedValue(
        new Error('Network error')
      );

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[1].content).toContain('Network error');
      expect(result.current.error).toBe('Network error');
    });

    it('should require a session to send messages', async () => {
      usePreviewStore.setState({ sessionId: null });

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.sendMessage('Test message');
      });

      expect(result.current.error).toBe('No active preview session. Please start a new session.');
      expect(result.current.messages).toHaveLength(0);
    });
  });

  describe('resetConversation', () => {
    it('should reset conversation successfully', async () => {
      usePreviewStore.setState({
        sessionId: 'test-session-id',
        messages: [
          { id: '1', role: 'user', content: 'Test', timestamp: new Date() },
        ],
      });

      vi.mocked(
        previewService.previewService.resetPreviewConversation
      ).mockResolvedValue({ cleared: true, message: 'Conversation reset' });

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.resetConversation();
      });

      expect(result.current.messages).toEqual([]);
      expect(
        previewService.previewService.resetPreviewConversation
      ).toHaveBeenCalledWith('test-session-id');
    });

    it('should clear messages locally when no session exists', async () => {
      usePreviewStore.setState({
        sessionId: null,
        messages: [{ id: '1', role: 'user', content: 'Test', timestamp: new Date() }],
      });

      const { result } = renderHook(() => usePreviewStore());

      await act(async () => {
        await result.current.resetConversation();
      });

      expect(result.current.messages).toEqual([]);
      expect(
        previewService.previewService.resetPreviewConversation
      ).not.toHaveBeenCalled();
    });
  });

  describe('clearMessages', () => {
    it('should clear all messages locally', () => {
      usePreviewStore.setState({
        messages: [
          { id: '1', role: 'user', content: 'Test', timestamp: new Date() },
          { id: '2', role: 'bot', content: 'Response', timestamp: new Date() },
        ],
        error: 'Some error',
      });

      const { result } = renderHook(() => usePreviewStore());

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toEqual([]);
      expect(result.current.error).toBeNull();
    });
  });

  describe('setError', () => {
    it('should set error message', () => {
      const { result } = renderHook(() => usePreviewStore());

      act(() => {
        result.current.setError('Test error');
      });

      expect(result.current.error).toBe('Test error');
    });

    it('should clear error when set to null', () => {
      usePreviewStore.setState({ error: 'Existing error' });

      const { result } = renderHook(() => usePreviewStore());

      act(() => {
        result.current.setError(null);
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('setBotName', () => {
    it('should set bot name', () => {
      const { result } = renderHook(() => usePreviewStore());

      act(() => {
        result.current.setBotName('GearBot');
      });

      expect(result.current.botName).toBe('GearBot');
    });
  });
});
