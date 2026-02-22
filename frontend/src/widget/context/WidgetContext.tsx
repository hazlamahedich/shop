import * as React from 'react';
import type { WidgetAction, WidgetState, WidgetProduct } from '../types/widget';
import { createWidgetError } from '../types/errors';

const initialState: WidgetState = {
  isOpen: false,
  isLoading: false,
  isTyping: false,
  session: null,
  messages: [],
  config: null,
  error: null,
  errors: [],
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
    case 'ADD_WIDGET_ERROR':
      return { ...state, errors: [...state.errors, action.payload] };
    case 'DISMISS_WIDGET_ERROR':
      return {
        ...state,
        errors: state.errors.map((e) => (e.id === action.payload ? { ...e, dismissed: true } : e)),
      };
    case 'CLEAR_WIDGET_ERRORS':
      return { ...state, errors: [] };
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
  addToCart: (product: WidgetProduct) => Promise<void>;
  removeFromCart: (variantId: string) => Promise<void>;
  checkout: () => Promise<void>;
  addingProductId: string | null;
  removingItemId: string | null;
  isCheckingOut: boolean;
  addError: (error: unknown, context?: { action?: string; fallbackUrl?: string }) => void;
  dismissError: (errorId: string) => void;
  clearErrors: () => void;
  retryLastAction: () => void;
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
  const [addingProductId, setAddingProductId] = React.useState<string | null>(null);
  const [removingItemId, setRemovingItemId] = React.useState<string | null>(null);
  const [isCheckingOut, setIsCheckingOut] = React.useState(false);
  const lastActionRef = React.useRef<{ type: string; payload?: unknown } | null>(null);
  const greetingShownRef = React.useRef(false);

  const addError = React.useCallback(
    (error: unknown, context?: { action?: string; fallbackUrl?: string }) => {
      const widgetError = createWidgetError(error, context);
      dispatch({ type: 'ADD_WIDGET_ERROR', payload: widgetError });
      dispatch({ type: 'SET_ERROR', payload: widgetError.message });
      console.error('[Widget Error]', widgetError);
    },
    []
  );

  const dismissError = React.useCallback((errorId: string) => {
    dispatch({ type: 'DISMISS_WIDGET_ERROR', payload: errorId });
  }, []);

  const clearErrors = React.useCallback(() => {
    dispatch({ type: 'CLEAR_WIDGET_ERRORS' });
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const {
    createSession,
    getSession,
    endSession: endWidgetSession,
  } = React.useMemo(
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
    lastActionRef.current = { type: 'initWidget' };
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
      addError(error, { action: 'Retry' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [merchantId, createSession, getSession, addError]);

  const toggleChat = React.useCallback(() => {
    dispatch({ type: 'SET_OPEN', payload: !state.isOpen });
  }, [state.isOpen]);

  const sendMessage = React.useCallback(
    async (content: string) => {
      if (!state.session || !content.trim()) return;

      lastActionRef.current = { type: 'sendMessage', payload: content };

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
        addError(error, { action: 'Try Again' });
      } finally {
        dispatch({ type: 'SET_TYPING', payload: false });
      }
    },
    [state.session, addError]
  );

  const addToCart = React.useCallback(
    async (product: WidgetProduct) => {
      lastActionRef.current = { type: 'addToCart', payload: product };
      setAddingProductId(product.id);
      try {
        const { widgetClient } = await import('../api/widgetClient');
        
        let sessionId = state.session?.sessionId;
        
        if (!sessionId) {
          const newSession = await createSession();
          dispatch({ type: 'SET_SESSION', payload: newSession });
          sessionStorage.setItem('widget_session_id', newSession.sessionId);
          sessionId = newSession.sessionId;
        }

        const updatedCart = await widgetClient.addToCart(sessionId, product, 1);

        const itemWord = updatedCart.itemCount === 1 ? 'item' : 'items';
        const confirmationMessage = {
          messageId: crypto.randomUUID(),
          content: `Added "${product.title}" to your cart!\n\nYour cart now has ${updatedCart.itemCount} ${itemWord} totaling $${updatedCart.total.toFixed(2)}.`,
          sender: 'bot' as const,
          createdAt: new Date().toISOString(),
          cart: updatedCart,
        };
        dispatch({ type: 'ADD_MESSAGE', payload: confirmationMessage });
      } catch (error) {
        addError(error, { action: 'Try Again' });
      } finally {
        setAddingProductId(null);
      }
    },
    [state.session, addError, createSession]
  );

  const removeFromCart = React.useCallback(
    async (variantId: string) => {
      setRemovingItemId(variantId);
      try {
        const { widgetClient } = await import('../api/widgetClient');
        
        let sessionId = state.session?.sessionId;
        
        if (!sessionId) {
          const newSession = await createSession();
          dispatch({ type: 'SET_SESSION', payload: newSession });
          sessionStorage.setItem('widget_session_id', newSession.sessionId);
          sessionId = newSession.sessionId;
        }

        await widgetClient.removeFromCart(sessionId, variantId);
      } catch (error) {
        addError(error, { action: 'Try Again' });
      } finally {
        setRemovingItemId(null);
      }
    },
    [state.session, addError, createSession]
  );

  const checkout = React.useCallback(async () => {
    lastActionRef.current = { type: 'checkout' };
    setIsCheckingOut(true);
    try {
      const { widgetClient } = await import('../api/widgetClient');
      
      let sessionId = state.session?.sessionId;
      
      if (!sessionId) {
        const newSession = await createSession();
        dispatch({ type: 'SET_SESSION', payload: newSession });
        sessionStorage.setItem('widget_session_id', newSession.sessionId);
        sessionId = newSession.sessionId;
      }

      const result = await widgetClient.checkout(sessionId);

      window.open(result.checkoutUrl, '_blank');

      const confirmationMessage = {
        messageId: crypto.randomUUID(),
        content: result.message || 'Opening checkout in a new tab...',
        sender: 'bot' as const,
        createdAt: new Date().toISOString(),
        checkoutUrl: result.checkoutUrl,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: confirmationMessage });
    } catch (error) {
      addError(error, {
        action: 'Try Again',
        fallbackUrl: 'https://volare-sun.myshopify.com/cart',
      });
    } finally {
      setIsCheckingOut(false);
    }
  }, [state.session, addError, createSession]);

  // Show greeting message when config is loaded and widget is open with no messages
  React.useEffect(() => {
    if (
      state.isOpen &&
      state.messages.length === 0 &&
      state.config?.welcomeMessage &&
      !greetingShownRef.current
    ) {
      greetingShownRef.current = true;
      const greetingMessage = {
        messageId: crypto.randomUUID(),
        content: state.config.welcomeMessage,
        sender: 'bot' as const,
        createdAt: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: greetingMessage });
    }
  }, [state.isOpen, state.messages.length, state.config?.welcomeMessage]);

  const retryLastAction = React.useCallback(() => {
    if (!lastActionRef.current) return;
    const { type, payload } = lastActionRef.current;
    switch (type) {
      case 'initWidget':
        initWidget();
        break;
      case 'sendMessage':
        if (typeof payload === 'string') sendMessage(payload);
        break;
      case 'addToCart':
        if (payload) addToCart(payload as WidgetProduct);
        break;
      case 'checkout':
        checkout();
        break;
    }
  }, [initWidget, sendMessage, addToCart, checkout]);

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
      addToCart,
      removeFromCart,
      checkout,
      addingProductId,
      removingItemId,
      isCheckingOut,
      addError,
      dismissError,
      clearErrors,
      retryLastAction,
    }),
    [
      state,
      toggleChat,
      sendMessage,
      endSession,
      initWidget,
      merchantId,
      addToCart,
      removeFromCart,
      checkout,
      addingProductId,
      removingItemId,
      isCheckingOut,
      addError,
      dismissError,
      clearErrors,
      retryLastAction,
    ]
  );

  return <WidgetContext.Provider value={value}>{children}</WidgetContext.Provider>;
}

export { WidgetContext };
