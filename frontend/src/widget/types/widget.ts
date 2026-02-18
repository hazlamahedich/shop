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
  sender: 'user' | 'bot';
  createdAt: string;
}

export interface WidgetState {
  isOpen: boolean;
  isLoading: boolean;
  isTyping: boolean;
  session: WidgetSession | null;
  messages: WidgetMessage[];
  config: WidgetConfig | null;
  error: string | null;
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
  | { type: 'RESET' };
