/**
 * Preview Mode Store
 *
 * Story 1.13: Bot Preview Mode
 *
 * Zustand store for managing preview mode state.
 * This store is NOT persisted (preview should reset on navigate away).
 *
 * State:
 * - messages: Array of chat messages in the preview conversation
 * - sessionId: Current preview session ID
 * - isLoading: Loading state for async operations
 * - error: Error message if something went wrong
 * - starterPrompts: Sample conversation starters
 * - botName: Bot name to display in responses
 */

import { create } from 'zustand';
import {
  previewService,
  PreviewMessageResponse,
  PreviewSessionResponse,
} from '../services/preview';

/**
 * Message in the preview conversation
 */
export interface PreviewMessage {
  id: string;
  role: 'user' | 'bot';
  content: string;
  timestamp: Date;
  confidence?: number;
  confidenceLevel?: 'high' | 'medium' | 'low';
  metadata?: {
    intent: string;
    faqMatched: boolean;
    productsFound: number;
    llmProvider: string;
  };
}

/**
 * Preview store state
 */
interface PreviewState {
  // State
  messages: PreviewMessage[];
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  starterPrompts: string[];
  botName: string;

  // Actions
  startSession: () => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  resetConversation: () => Promise<void>;
  clearMessages: () => void;
  setError: (error: string | null) => void;
  setBotName: (botName: string) => void;
}

/**
 * Generate unique message ID
 * Uses timestamp and random string for uniqueness
 */
function generateMessageId(): string {
  const randomStr = Math.random().toString(36).slice(2, 11);
  return `msg-${Date.now()}-${randomStr}`;
}

/**
 * Preview mode store
 *
 * Note: This store is NOT persisted to localStorage.
 * Preview conversations should reset when navigating away.
 */
export const usePreviewStore = create<PreviewState>((set, get) => ({
  // Initial state
  messages: [],
  sessionId: null,
  isLoading: false,
  error: null,
  starterPrompts: [],
  botName: 'Bot',

  /**
   * Start a new preview session
   */
  startSession: async () => {
    set({ isLoading: true, error: null });

    try {
      const sessionData: PreviewSessionResponse =
        await previewService.startPreviewSession();

      set({
        sessionId: sessionData.previewSessionId,
        starterPrompts: sessionData.starterPrompts,
        messages: [],
        isLoading: false,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to start preview session';
      set({
        error: errorMessage,
        isLoading: false,
      });
    }
  },

  /**
   * Send a message in preview mode
   */
  sendMessage: async (message: string) => {
    const { sessionId, messages } = get();

    if (!sessionId) {
      set({ error: 'No active preview session. Please start a new session.' });
      return;
    }

    if (!message.trim()) {
      return;
    }

    // Add user message immediately
    const userMessage: PreviewMessage = {
      id: generateMessageId(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    set({
      messages: [...messages, userMessage],
      isLoading: true,
      error: null,
    });

    try {
      const responseData: PreviewMessageResponse =
        await previewService.sendPreviewMessage(message, sessionId);

      // Add bot response with confidence metadata
      const botMessage: PreviewMessage = {
        id: generateMessageId(),
        role: 'bot',
        content: responseData.response,
        timestamp: new Date(),
        confidence: responseData.confidence,
        confidenceLevel: responseData.confidenceLevel,
        metadata: responseData.metadata,
      };

      set({
        messages: [...get().messages, botMessage],
        isLoading: false,
      });
    } catch (error) {
      const err = error as { status?: number; message?: string };

      // If session expired (404), clear state and show helpful message
      if (err.status === 404) {
        set({
          messages: [...messages], // Remove the user message we added
          sessionId: null,
          isLoading: false,
          error: 'Session expired. Please refresh the page to start a new session.',
        });
      } else {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to send message';

        // Add error message as bot response
        const errorMessageBot: PreviewMessage = {
          id: generateMessageId(),
          role: 'bot',
          content: `Sorry, I encountered an error: ${errorMessage}`,
          timestamp: new Date(),
        };

        set({
          messages: [...get().messages, errorMessageBot],
          error: errorMessage,
          isLoading: false,
        });
      }
    }
  },

  /**
   * Reset the current preview conversation
   *
   * If the backend session doesn't exist (e.g., server restart),
   * automatically start a new session so the user can continue.
   */
  resetConversation: async () => {
    const { sessionId } = get();

    if (!sessionId) {
      // No session exists, just clear messages
      set({ messages: [], error: null });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      await previewService.resetPreviewConversation(sessionId);
      set({
        messages: [],
        isLoading: false,
      });
    } catch (error) {
      // If session not found (404), it likely expired due to server restart
      // Start a new session automatically so user can continue
      const err = error as { status?: number; message?: string };
      if (err.status === 404) {
        // Clear expired session state and start fresh
        set({
          messages: [],
          sessionId: null,
        });
        // Automatically start a new session
        await get().startSession();
      } else {
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to reset conversation';
        set({
          error: errorMessage,
          isLoading: false,
        });
      }
    }
  },

  /**
   * Clear all messages (local only, no API call)
   */
  clearMessages: () => {
    set({ messages: [], error: null });
  },

  /**
   * Set error message
   */
  setError: (error: string | null) => {
    set({ error });
  },

  /**
   * Set bot name for display
   */
  setBotName: (botName: string) => {
    set({ botName });
  },
}));
