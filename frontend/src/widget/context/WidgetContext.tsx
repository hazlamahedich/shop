import * as React from 'react';
import type { WidgetAction, WidgetState } from '../types/widget';

const initialState: WidgetState = {
  isOpen: false,
  isLoading: false,
  isTyping: false,
  session: null,
  messages: [],
  config: null,
  error: null,
};

function widgetReducer(state: WidgetState, action: WidgetAction): WidgetState {
  switch (action.type) {
    case 'SET_OPEN':
      return { ...state, isOpen: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_TYPING':
      return { ...state, isTyping: action.payload };
    case 'SET_SESSION':
      return { ...state, session: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'SET_CONFIG':
      return { ...state, config: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

interface WidgetContextValue {
  state: WidgetState;
  dispatch: React.Dispatch<WidgetAction>;
  toggleChat: () => void;
  sendMessage: (content: string) => Promise<void>;
  endSession: () => Promise<void>;
  initWidget: (merchantId: string) => Promise<void>;
  merchantId: string;
}

const WidgetContext = React.createContext<WidgetContextValue | null>(null);

export function useWidgetContext(): WidgetContextValue {
  const context = React.useContext(WidgetContext);
  if (!context) {
    throw new Error('useWidgetContext must be used within a WidgetProvider');
  }
  return context;
}

interface WidgetProviderProps {
  children: React.ReactNode;
  merchantId: string;
}

export function WidgetProvider({ children, merchantId }: WidgetProviderProps) {
  const [state, dispatch] = React.useReducer(widgetReducer, initialState);
  const { createSession, getSession, endSession: endWidgetSession } = React.useMemo(
    () => ({
      createSession: async () => {
        const { widgetClient } = await import('../api/widgetClient');
        return widgetClient.createSession(merchantId);
      },
      getSession: async (sessionId: string) => {
        const { widgetClient } = await import('../api/widgetClient');
        return widgetClient.getSession(sessionId);
      },
      endSession: async (sessionId: string) => {
        const { widgetClient } = await import('../api/widgetClient');
        return widgetClient.endSession(sessionId);
      },
    }),
    [merchantId]
  );

  const initWidget = React.useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });

    try {
      const { widgetClient } = await import('../api/widgetClient');
      const config = await widgetClient.getConfig(merchantId);
      dispatch({ type: 'SET_CONFIG', payload: config });

      const sessionId = sessionStorage.getItem('widget_session_id');
      if (sessionId) {
        const session = await getSession(sessionId);
        if (session) {
          dispatch({ type: 'SET_SESSION', payload: session });
          dispatch({ type: 'SET_LOADING', payload: false });
          return;
        }
      }

      const newSession = await createSession();
      dispatch({ type: 'SET_SESSION', payload: newSession });
      sessionStorage.setItem('widget_session_id', newSession.sessionId);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to initialize widget';
      dispatch({ type: 'SET_ERROR', payload: message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [merchantId, createSession, getSession]);

  const toggleChat = React.useCallback(() => {
    dispatch({ type: 'SET_OPEN', payload: !state.isOpen });
  }, [state.isOpen]);

  const sendMessage = React.useCallback(
    async (content: string) => {
      if (!state.session || !content.trim()) return;

      const userMessage = {
        messageId: crypto.randomUUID(),
        content,
        sender: 'user' as const,
        createdAt: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
      dispatch({ type: 'SET_TYPING', payload: true });

      try {
        const { widgetClient } = await import('../api/widgetClient');
        const botMessage = await widgetClient.sendMessage(state.session.sessionId, content);
        dispatch({ type: 'ADD_MESSAGE', payload: botMessage });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to send message';
        dispatch({ type: 'SET_ERROR', payload: message });
      } finally {
        dispatch({ type: 'SET_TYPING', payload: false });
      }
    },
    [state.session]
  );

  const endSession = React.useCallback(async () => {
    if (state.session) {
      try {
        await endWidgetSession(state.session.sessionId);
      } catch {
        // Ignore errors on cleanup
      }
    }
    sessionStorage.removeItem('widget_session_id');
    dispatch({ type: 'RESET' });
  }, [state.session, endWidgetSession]);

  const value = React.useMemo(
    () => ({
      state,
      dispatch,
      toggleChat,
      sendMessage,
      endSession,
      initWidget,
      merchantId,
    }),
    [state, toggleChat, sendMessage, endSession, initWidget, merchantId]
  );

  return <WidgetContext.Provider value={value}>{children}</WidgetContext.Provider>;
}

export { WidgetContext };
