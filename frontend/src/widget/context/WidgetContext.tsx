import * as React from 'react';
import type { WidgetAction, WidgetState, WidgetProduct, ConnectionStatus, ConsentState, ThemeMode } from '../types/widget';
import { createWidgetError } from '../types/errors';
import { shopifyCartClient } from '../api/shopifyCartClient';
import { 
  safeStorage, 
  SESSION_KEY, 
  MERCHANT_KEY, 
  getOrCreateVisitorId, 
  getVisitorId, 
  clearVisitorId,
  cacheMessages,
  getCachedMessages,
  clearMessageCache,
  saveWidgetPosition,
  loadWidgetPosition,
  isValidSessionId,
  getStoredTheme,
  setStoredTheme,
  type CachedMessage,
  type WidgetPosition,
} from '../utils/storage';

const initialConsentState: ConsentState = {
  promptShown: false,
  canStoreConversation: false,
  status: 'pending',
};

const getInitialPosition = (): { x: number; y: number } => {
  const saved = loadWidgetPosition();
  if (saved) {
    return saved;
  }
  return { x: 0, y: 0 };
};

const initialState: WidgetState = {
  isOpen: false,
  isLoading: false,
  isTyping: false,
  session: null,
  messages: [],
  config: null,
  error: null,
  errors: [],
  connectionStatus: 'disconnected',
  consentState: initialConsentState,
  position: getInitialPosition(),
  isDragging: false,
  isMinimized: false,
  unreadCount: 0,
  themeMode: 'auto',
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
      const newUnreadCount = state.isMinimized && action.payload.sender !== 'user' 
        ? state.unreadCount + 1 
        : state.unreadCount;
      return { ...state, messages: [...state.messages, action.payload], unreadCount: newUnreadCount };
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
    case 'SET_CONNECTION_STATUS':
      return { ...state, connectionStatus: action.payload };
    case 'SET_CONSENT_STATE':
      return { ...state, consentState: action.payload };
    case 'SET_CONSENT_PROMPT_SHOWN':
      return { ...state, consentState: { ...state.consentState, promptShown: action.payload } };
    case 'SET_POSITION':
      return { ...state, position: action.payload };
    case 'SET_DRAGGING':
      return { ...state, isDragging: action.payload };
    case 'TOGGLE_MINIMIZED':
      return { ...state, isMinimized: !state.isMinimized, unreadCount: !state.isMinimized ? 0 : state.unreadCount };
    case 'SET_UNREAD_COUNT':
      return { ...state, unreadCount: action.payload };
    case 'SET_THEME_MODE':
      return { ...state, themeMode: action.payload };
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
  connectionStatus: ConnectionStatus;
  recordConsent: (consented: boolean) => Promise<void>;
  forgetPreferences: () => Promise<void>;
  clearHistory: () => Promise<void>;
  updatePosition: (position: WidgetPosition) => void;
  toggleMinimized: () => void;
  setThemeMode: (mode: ThemeMode) => void;
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
  const consentPromptShownRef = React.useRef(false);
  const lastCachedLengthRef = React.useRef<number>(0);

  // Load theme synchronously on mount (before async initWidget completes)
  React.useEffect(() => {
    const storedTheme = getStoredTheme(merchantId);
    if (storedTheme && storedTheme !== state.themeMode) {
      dispatch({ type: 'SET_THEME_MODE', payload: storedTheme });
    }
  }, [merchantId]);

  React.useEffect(() => {
    if (!state.session?.sessionId || state.messages.length === 0) {
      return;
    }

    if (state.messages.length !== lastCachedLengthRef.current) {
      lastCachedLengthRef.current = state.messages.length;
      cacheMessages(state.session.sessionId, state.messages as CachedMessage[]);
    }
  }, [state.messages, state.session?.sessionId]);

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
      createSession: async (visitorId?: string) => {
        const { widgetClient } = await import('../api/widgetClient');
        return widgetClient.createSession(merchantId, visitorId);
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

      // Register the shop domain so isOnShopify() correctly detects custom-domain stores
      shopifyCartClient.setShopDomain(config.shopDomain);

      // Load stored theme preference
      const storedTheme = getStoredTheme(merchantId);
      dispatch({ type: 'SET_THEME_MODE', payload: storedTheme || 'auto' });

      const visitorId = getOrCreateVisitorId();

      const sessionId = safeStorage.get(SESSION_KEY);
      
      // Validate session ID format before attempting to use it
      if (sessionId && isValidSessionId(sessionId)) {
        const session = await getSession(sessionId)
        if (session) {
          dispatch({ type: 'SET_SESSION', payload: session })
          
          // Try to load messages from localStorage cache first (instant display)
          const cachedMessages = getCachedMessages(sessionId);
          if (cachedMessages && cachedMessages.length > 0) {
            dispatch({ type: 'SET_MESSAGES', payload: cachedMessages });
          }
          
          // Load existing consent status if available
          try {
            const consentStatus = await widgetClient.getConsentStatus(sessionId, visitorId);
            if (consentStatus) {
              const newConsentState: ConsentState = {
                promptShown: consentStatus.consent_message_shown || false,
                canStoreConversation: consentStatus.can_store_conversation,
                status: consentStatus.status,
              };
              dispatch({ type: 'SET_CONSENT_STATE', payload: newConsentState });
              
              // Mark ref to prevent showing prompt again if already shown
              if (consentStatus.consent_message_shown) {
                consentPromptShownRef.current = true;
              }
            }
          } catch (error) {
            // Ignore consent status load errors - will prompt on first message
          }
          
          // Fetch message history from backend
          try {
            const history = await widgetClient.getMessageHistory(sessionId);
            if (history.expired) {
              // History expired - clear cache and show message
              clearMessageCache(sessionId);
              dispatch({ type: 'SET_MESSAGES', payload: [] });
              
              // Show expired notification
              if (cachedMessages && cachedMessages.length > 0) {
                const expiredMessage = {
                  messageId: 'session-expired',
                  content: 'Your previous conversation has expired. Starting fresh!',
                  sender: 'system' as const,
                  createdAt: new Date().toISOString(),
                };
                dispatch({ type: 'SET_MESSAGES', payload: [expiredMessage] });
              }
            } else if (history.messages.length > 0) {
              // Convert backend messages to widget format
              const messages: CachedMessage[] = history.messages.map((msg, index) => ({
                messageId: `history-${index}`,
                content: msg.content,
                sender: msg.role === 'user' ? 'user' : 'bot',
                createdAt: msg.timestamp,
              }));
              
              dispatch({ type: 'SET_MESSAGES', payload: messages });
              
              // Update cache
              cacheMessages(sessionId, messages);
              
              // Mark greeting as shown if we have history
              if (messages.length > 0) {
                greetingShownRef.current = true;
              }
            }
          } catch (error) {
            // Failed to load history - keep cached messages if available
          }
          
          dispatch({ type: 'SET_LOADING', payload: false })
          return
        }
      }

      const newSession = await createSession(visitorId)
      dispatch({ type: 'SET_SESSION', payload: newSession })
      safeStorage.set(SESSION_KEY, newSession.sessionId)
      safeStorage.set(MERCHANT_KEY, merchantId)
    } catch (error) {
      addError(error, { action: 'Retry' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [merchantId, createSession, getSession, addError])

  const toggleChat = React.useCallback(() => {
    dispatch({ type: 'SET_OPEN', payload: !state.isOpen });
  }, [state.isOpen]);

  const recordConsent = React.useCallback(
    async (consented: boolean) => {
      if (!state.session?.sessionId || !isValidSessionId(state.session.sessionId)) return;

      try {
        const { widgetClient } = await import('../api/widgetClient');
        const visitorId = getVisitorId() || undefined;
        await widgetClient.recordConsent(state.session.sessionId, consented, visitorId);

        const newConsentState: ConsentState = {
          promptShown: true,
          canStoreConversation: consented,
          status: consented ? 'opted_in' : 'opted_out',
        };
        dispatch({ type: 'SET_CONSENT_STATE', payload: newConsentState });
      } catch (error) {
        console.error('[WidgetContext] recordConsent error:', error);
        addError(error, { action: 'Try Again' });
      }
    },
    [state.session, addError]
  );

  const sendMessage = React.useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      // Validate session exists and has valid UUID format
      if (!state.session?.sessionId || !isValidSessionId(state.session.sessionId)) {
        // Clear invalid session from storage
        safeStorage.remove(SESSION_KEY);
        
        // Create new session
        const visitorId = getVisitorId() || undefined;
        const newSession = await createSession(visitorId);
        dispatch({ type: 'SET_SESSION', payload: newSession });
        safeStorage.set(SESSION_KEY, newSession.sessionId);
        
        // Use new session ID
        state.session = newSession;
      }

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
        const botMessage = await widgetClient.sendMessage(state.session!.sessionId, content);
        dispatch({ type: 'ADD_MESSAGE', payload: botMessage });

        if (botMessage.consent_prompt_required && !consentPromptShownRef.current) {
          consentPromptShownRef.current = true;
          dispatch({ type: 'SET_CONSENT_PROMPT_SHOWN', payload: true });
        }

        if (shopifyCartClient.isOnShopify() && botMessage.cart) {
          syncCartToShopify(botMessage.cart);
        }
      } catch (error) {
        addError(error, { action: 'Try Again' });
      } finally {
        dispatch({ type: 'SET_TYPING', payload: false });
      }
    },
    [state.session, addError]
  );

  const syncCartToShopify = React.useCallback(
    async (cart: { items: Array<{ variantId?: string; quantity: number }>; itemCount?: number }) => {
      if (!shopifyCartClient.isOnShopify()) return;

        try {
          if (!cart.items || cart.items.length === 0) {
            await shopifyCartClient.clearCart();
          } else {
            const shopifyCart = await shopifyCartClient.getCart();
            const shopifyVariantIds = new Set(
              shopifyCart.items.map((item) => String(item.variant_id))
            );

            for (const item of cart.items) {
              if (item.variantId && !shopifyVariantIds.has(String(item.variantId))) {
                await shopifyCartClient.addToCart(item.variantId, item.quantity);
              }
            }
          }
        } catch (shopifyError) {
          // Ignore Shopify sync errors
        }
    },
    []
  );

  const addToCart = React.useCallback(
    async (product: WidgetProduct) => {
      lastActionRef.current = { type: 'addToCart', payload: product };
      setAddingProductId(product.id);
      try {
        const { widgetClient } = await import('../api/widgetClient');
        
        let sessionId = state.session?.sessionId;
        
        // Validate session ID format
        if (!sessionId || !isValidSessionId(sessionId)) {
          safeStorage.remove(SESSION_KEY);
          const visitorId = getVisitorId() || undefined;
          const newSession = await createSession(visitorId);
          dispatch({ type: 'SET_SESSION', payload: newSession });
          safeStorage.set(SESSION_KEY, newSession.sessionId);
          sessionId = newSession.sessionId;
        }

        const updatedCart = await widgetClient.addToCart(sessionId, product, 1);

        if (shopifyCartClient.isOnShopify() && product.variantId) {
          try {
            await shopifyCartClient.addToCart(product.variantId, 1);
          } catch (shopifyError) {
            // Ignore Shopify sync errors
          }
        }

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
      if (!variantId) return;
      
      setRemovingItemId(variantId);
      try {
        const { widgetClient } = await import('../api/widgetClient');
        
        let sessionId = state.session?.sessionId;
        
        // Validate session ID format
        if (!sessionId || !isValidSessionId(sessionId)) {
          safeStorage.remove(SESSION_KEY);
          const visitorId = getVisitorId() || undefined;
          const newSession = await createSession(visitorId);
          dispatch({ type: 'SET_SESSION', payload: newSession });
          safeStorage.set(SESSION_KEY, newSession.sessionId);
          sessionId = newSession.sessionId;
        }

        const updatedCart = await widgetClient.removeFromCart(sessionId, variantId);

        const removedItem = state.messages
          .flatMap(m => m.cart?.items || [])
          .find(item => item.variantId === variantId);
        const itemTitle = removedItem?.title || 'Item';

        const itemWord = updatedCart.itemCount === 1 ? 'item' : 'items';
        const confirmationMessage = {
          messageId: crypto.randomUUID(),
          content: updatedCart.itemCount > 0
            ? `Removed "${itemTitle}" from your cart.\n\nYour cart now has ${updatedCart.itemCount} ${itemWord} totaling $${updatedCart.total.toFixed(2)}.`
            : `Removed "${itemTitle}" from your cart.\n\nYour cart is now empty.`,
          sender: 'bot' as const,
          createdAt: new Date().toISOString(),
          cart: updatedCart,
        };
        dispatch({ type: 'ADD_MESSAGE', payload: confirmationMessage });

        if (shopifyCartClient.isOnShopify()) {
          try {
            await shopifyCartClient.removeFromCart(variantId);
          } catch (shopifyError) {
            // Ignore Shopify sync errors
          }
        }
      } catch (error) {
        addError(error, { action: 'Try Again' });
      } finally {
        setRemovingItemId(null);
      }
    },
    [state.session, state.messages, addError, createSession]
  );

  const checkout = React.useCallback(async () => {
    lastActionRef.current = { type: 'checkout' };
    setIsCheckingOut(true);
    try {
      const shopDomain = state.config?.shopDomain;
      
      if (!shopDomain) {
        throw new Error('Shop domain not configured');
      }

      const messagesWithCart = state.messages.filter(m => m.cart && m.cart.items.length > 0);
      const latestCart = messagesWithCart.length > 0 
        ? messagesWithCart[messagesWithCart.length - 1].cart 
        : null;

      if (!latestCart || latestCart.items.length === 0) {
        throw new Error('Your cart is empty');
      }

      const validItems = latestCart.items.filter(item => item.variantId && item.quantity > 0);
      if (validItems.length === 0) {
        throw new Error('No valid items in cart');
      }

      const cartItems = validItems
        .map(item => `${item.variantId}:${item.quantity}`)
        .join(',');

      const checkoutUrl = `https://${shopDomain}/cart/${cartItems}`;

      window.open(checkoutUrl, '_blank');

      const confirmationMessage = {
        messageId: crypto.randomUUID(),
        content: 'Opening checkout in a new tab...',
        sender: 'bot' as const,
        createdAt: new Date().toISOString(),
        checkoutUrl: checkoutUrl,
      };
      dispatch({ type: 'ADD_MESSAGE', payload: confirmationMessage });
    } catch (error) {
      addError(error, {
        action: 'Try Again',
        fallbackUrl: state.config?.shopDomain ? `https://${state.config.shopDomain}/cart` : undefined,
      });
    } finally {
      setIsCheckingOut(false);
    }
  }, [state.config, state.messages, addError]);

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

  React.useEffect(() => {
    if (!state.session?.sessionId || !state.isOpen) return;

    let cleanup: (() => void) | null = null;

    const connectWebSocket = async () => {
      const { connectWidgetWebSocket, isWebSocketSupported } = await import('../api/widgetWsClient');
      
      if (!isWebSocketSupported()) {
        dispatch({ type: 'SET_CONNECTION_STATUS', payload: 'error' });
        return;
      }

      cleanup = connectWidgetWebSocket(state.session!.sessionId, {
        onMessage: (event) => {
          if (event.type === 'merchant_message') {
            const data = event.data as { id: number; content: string; createdAt: string };
            const merchantMessage = {
              messageId: `merchant-${data.id}`,
              content: data.content,
              sender: 'merchant' as const,
              createdAt: data.createdAt,
            };
            dispatch({ type: 'ADD_MESSAGE', payload: merchantMessage });
          } else if (event.type === 'handoff_resolved') {
            const data = event.data as { id: number; content: string; createdAt: string };
            const resolutionMessage = {
              messageId: `resolution-${data.id}`,
              content: data.content,
              sender: 'bot' as const,
              createdAt: data.createdAt,
            };
            dispatch({ type: 'ADD_MESSAGE', payload: resolutionMessage });
          }
        },
        onStatusChange: (status) => {
          dispatch({ type: 'SET_CONNECTION_STATUS', payload: status });
        },
        onError: () => {
          // WebSocket error - connection status already updated
        },
      });
    };

    connectWebSocket();

    return () => {
      if (cleanup) cleanup();
    };
  }, [state.session?.sessionId, state.isOpen]);

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
    if (state.session?.sessionId && isValidSessionId(state.session.sessionId)) {
      try {
        await endWidgetSession(state.session.sessionId);
      } catch {
        // Ignore errors on cleanup
      }
    }
    safeStorage.remove(SESSION_KEY);
    safeStorage.remove(MERCHANT_KEY);
    dispatch({ type: 'RESET' });
  }, [state.session, endWidgetSession]);

  const forgetPreferences = React.useCallback(async () => {
    if (!state.session?.sessionId || !isValidSessionId(state.session.sessionId)) return;

    try {
      const { widgetClient } = await import('../api/widgetClient');
      const visitorId = getVisitorId() || undefined;
      const result = await widgetClient.forgetPreferences(state.session.sessionId, visitorId);

      if (result.clearVisitorId) {
        clearVisitorId();
      }

      const newConsentState: ConsentState = {
        promptShown: false,
        canStoreConversation: false,
        status: 'pending',
      };
      dispatch({ type: 'SET_CONSENT_STATE', payload: newConsentState });
    } catch (error) {
      addError(error, { action: 'Try Again' });
    }
  }, [state.session, addError]);

  const clearHistory = React.useCallback(async () => {
    if (!state.session?.sessionId || !isValidSessionId(state.session.sessionId)) return;

    try {
      const { widgetClient } = await import('../api/widgetClient');
      await widgetClient.clearMessageHistory(state.session.sessionId);
      
      // Clear local cache
      clearMessageCache(state.session.sessionId);
      
      // Clear messages from state
      dispatch({ type: 'SET_MESSAGES', payload: [] });
      
      // Reset greeting flag so welcome message shows again
      greetingShownRef.current = false;
      
      console.info('[WidgetContext] History cleared', { sessionId: state.session.sessionId });
    } catch (error) {
      addError(error, { action: 'Try Again' });
    }
  }, [state.session, addError]);

  const updatePosition = React.useCallback((position: { x: number; y: number }) => {
    dispatch({ type: 'SET_POSITION', payload: position });
    saveWidgetPosition(position);
  }, []);

  const toggleMinimized = React.useCallback(() => {
    dispatch({ type: 'TOGGLE_MINIMIZED' });
  }, []);

  const setThemeMode = React.useCallback((mode: ThemeMode) => {
    dispatch({ type: 'SET_THEME_MODE', payload: mode });
    setStoredTheme(merchantId, mode);
  }, [merchantId]);

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
      connectionStatus: state.connectionStatus,
      recordConsent,
      forgetPreferences,
      clearHistory,
      updatePosition,
      toggleMinimized,
      setThemeMode,
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
      recordConsent,
      forgetPreferences,
      clearHistory,
      updatePosition,
      toggleMinimized,
      setThemeMode,
    ]
  );

  return <WidgetContext.Provider value={value}>{children}</WidgetContext.Provider>;
}

export { WidgetContext };
