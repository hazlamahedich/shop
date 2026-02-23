import type { WidgetError } from './errors';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WidgetTheme {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  botBubbleColor: string;
  userBubbleColor: string;
  position: 'bottom-right' | 'bottom-left';
  borderRadius: number;
  width: number;
  height: number;
  fontFamily: string;
  fontSize: number;
}

export interface WidgetConfig {
  enabled: boolean;
  botName: string;
  welcomeMessage: string;
  theme: WidgetTheme;
  allowedDomains: string[];
  shopDomain?: string;
}

export interface WidgetSession {
  sessionId: string;
  merchantId: string;
  expiresAt: string;
  createdAt: string;
  lastActivityAt: string;
}

export interface WidgetMessage {
  messageId: string;
  content: string;
  sender: 'user' | 'bot' | 'merchant';
  createdAt: string;
  products?: WidgetProduct[];
  cart?: WidgetCart;
  checkoutUrl?: string;
  intent?: string;
  confidence?: number;
}

export interface WidgetState {
  isOpen: boolean;
  isLoading: boolean;
  isTyping: boolean;
  session: WidgetSession | null;
  messages: WidgetMessage[];
  config: WidgetConfig | null;
  error: string | null;
  errors: WidgetError[];
  connectionStatus: ConnectionStatus;
}

export interface WidgetApiError {
  error_code: number;
  message: string;
}

export type WidgetAction =
  | { type: 'SET_OPEN'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_TYPING'; payload: boolean }
  | { type: 'SET_SESSION'; payload: WidgetSession | null }
  | { type: 'ADD_MESSAGE'; payload: WidgetMessage }
  | { type: 'SET_MESSAGES'; payload: WidgetMessage[] }
  | { type: 'SET_CONFIG'; payload: WidgetConfig | null }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'ADD_WIDGET_ERROR'; payload: WidgetError }
  | { type: 'DISMISS_WIDGET_ERROR'; payload: string }
  | { type: 'CLEAR_WIDGET_ERRORS' }
  | { type: 'SET_CONNECTION_STATUS'; payload: ConnectionStatus }
  | { type: 'RESET' };

export interface WidgetProduct {
  id: string;
  variantId: string;
  title: string;
  description?: string;
  price: number;
  imageUrl?: string;
  available: boolean;
  productType?: string;
  isPinned?: boolean;
}

export interface WidgetCartItem {
  variantId: string;
  title: string;
  price: number;
  quantity: number;
}

export interface WidgetCart {
  items: WidgetCartItem[];
  itemCount: number;
  total: number;
  shopifyCartUrl?: string;
}

export interface WidgetSearchResult {
  products: WidgetProduct[];
  total: number;
  query: string;
}

export interface WidgetCheckoutResult {
  checkoutUrl: string;
  message: string;
}

export interface WidgetProductDetail {
  id: string;
  title: string;
  description?: string;
  imageUrl?: string;
  price: number;
  available: boolean;
  inventoryQuantity?: number;
  productType?: string;
  vendor?: string;
  variantId?: string;
}
