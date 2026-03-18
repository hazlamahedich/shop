import type { WidgetError } from './errors';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export type ThemeMode = 'light' | 'dark' | 'auto';

export type ConsentStatus = 'pending' | 'opted_in' | 'opted_out';

export interface ConsentState {
  promptShown: boolean;
  canStoreConversation: boolean;
  status: ConsentStatus;
}

export interface ConsentPromptResponse {
  status: ConsentStatus;
  can_store_conversation: boolean;
  consent_message_shown: boolean;
}

export interface RecordConsentRequest {
  session_id: string;
  consented: boolean;
  source_channel: string;
}

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
  mode?: ThemeMode;
}

export type PersonalityType = 'friendly' | 'professional' | 'enthusiastic';

export interface WidgetConfig {
  enabled: boolean;
  botName: string;
  welcomeMessage: string;
  theme: WidgetTheme;
  allowedDomains: string[];
  shopDomain?: string;
  personality?: PersonalityType;
  proactiveEngagementConfig?: ProactiveEngagementConfig;
  faqQuickButtons?: FAQQuickButtonsConfig;
  onboardingMode?: 'general' | 'ecommerce';
}

export interface WidgetSession {
  sessionId: string;
  merchantId: string;
  expiresAt: string;
  createdAt: string;
  lastActivityAt: string;
}

export interface QuickReply {
  id: string;
  text: string;
  icon?: string;
  payload?: string;
}

export interface FAQQuickButton {
  id: number;
  question: string;
  icon?: string;
}

export interface FAQQuickButtonsConfig {
  enabled: boolean;
  buttonIds: number[];
}

export interface QuickReplyConfig {
  replies: QuickReply[];
  dismissOnSelect?: boolean;
}

export const DEFAULT_QUICK_REPLIES: QuickReply[] = [
  { id: '1', text: 'Yes', icon: '✓' },
  { id: '2', text: 'No', icon: '✗' },
  { id: '3', text: 'Tell me more' },
];

export type SourceDocumentType = 'pdf' | 'url' | 'text';

export interface SourceCitation {
  documentId: number;
  title: string;
  documentType: SourceDocumentType;
  relevanceScore: number;
  url?: string;
  chunkIndex?: number;
}

export interface WidgetMessage {
  messageId: string;
  content: string;
  sender: 'user' | 'bot' | 'merchant' | 'system';
  createdAt: string;
  products?: WidgetProduct[];
  cart?: WidgetCart;
  checkoutUrl?: string;
  intent?: string;
  confidence?: number;
  quick_replies?: QuickReply[];
  sources?: SourceCitation[];
}

export interface MessageGroup {
  id: string;
  sender: 'user' | 'bot' | 'merchant' | 'system';
  messages: WidgetMessage[];
}

export type WidgetEdge = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';

export interface WidgetPosition {
  x: number;
  y: number;
  edge?: WidgetEdge;
}

export interface PositioningConfig {
  avoidElements: string[];
  minClearance: number;
  edgeSnapThreshold: number;
  viewportPadding: number;
}

export const DEFAULT_POSITIONING_CONFIG: PositioningConfig = {
  avoidElements: ['[data-important="true"]'],
  minClearance: 20,
  edgeSnapThreshold: 30,
  viewportPadding: 10,
};

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
  consentState: ConsentState;
  position: WidgetPosition;
  isDragging: boolean;
  isMinimized: boolean;
  unreadCount: number;
  themeMode: ThemeMode;
  faqQuickButtons: FAQQuickButton[];
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
  | { type: 'SET_CONSENT_STATE'; payload: ConsentState }
  | { type: 'SET_CONSENT_PROMPT_SHOWN'; payload: boolean }
  | { type: 'SET_POSITION'; payload: WidgetPosition }
  | { type: 'SET_DRAGGING'; payload: boolean }
  | { type: 'TOGGLE_MINIMIZED' }
  | { type: 'SET_UNREAD_COUNT'; payload: number }
  | { type: 'SET_THEME_MODE'; payload: ThemeMode }
  | { type: 'SET_FAQ_QUICK_BUTTONS'; payload: FAQQuickButton[] }
  | { type: 'RESET' };

export interface WidgetProduct {
  id: string;
  variantId: string;
  handle?: string;
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
  description?: string | null;
  imageUrl?: string | null;
  price: number;
  available: boolean;
  inventoryQuantity?: number | null;
  productType?: string | null;
  vendor?: string | null;
  variantId?: string | null;
}

export interface CarouselConfig {
  visibleCards: { mobile: number; desktop: number };
  cardWidth: number;
  cardGap: number;
  scrollDuration: number;
}

export const DEFAULT_CAROUSEL_CONFIG: CarouselConfig = {
  visibleCards: { mobile: 2, desktop: 3 },
  cardWidth: 140,
  cardGap: 12,
  scrollDuration: 300,
};

export interface VoiceInputConfig {
  enabled: boolean;
  language: string;
  continuous: boolean;
  interimResults: boolean;
}

export interface VoiceInputState {
  isListening: boolean;
  isProcessing: boolean;
  error: string | null;
  interimTranscript: string;
  finalTranscript: string;
}

export const DEFAULT_VOICE_CONFIG: VoiceInputConfig = {
  enabled: true,
  language: 'en-US',
  continuous: false,
  interimResults: true,
};

export const SUPPORTED_VOICE_LANGUAGES = [
  { code: 'en-US', name: 'English (US)' },
  { code: 'en-GB', name: 'English (UK)' },
  { code: 'es-ES', name: 'Spanish' },
  { code: 'fr-FR', name: 'French' },
  { code: 'de-DE', name: 'German' },
  { code: 'zh-CN', name: 'Chinese (Simplified)' },
  { code: 'ja-JP', name: 'Japanese' },
] as const;

export type TriggerType =
  | 'exit_intent'
  | 'time_on_page'
  | 'scroll_depth'
  | 'cart_abandonment'
  | 'product_view';

export interface ProactiveTriggerAction {
  text: string;
  prePopulatedMessage?: string;
}

export interface ProactiveTrigger {
  type: TriggerType;
  enabled: boolean;
  threshold?: number;
  message: string;
  actions: ProactiveTriggerAction[];
  cooldown: number;
}

export interface ProactiveEngagementConfig {
  enabled: boolean;
  triggers: ProactiveTrigger[];
}

export const DEFAULT_PROACTIVE_THRESHOLDS: Record<TriggerType, number | undefined> = {
  exit_intent: undefined,
  time_on_page: 30,
  scroll_depth: 50,
  cart_abandonment: undefined,
  product_view: 3,
};

export const DEFAULT_PROACTIVE_CONFIG: ProactiveEngagementConfig = {
  enabled: true,
  triggers: [
    {
      type: 'exit_intent',
      enabled: true,
      message: 'Wait! Before you go, can we help you find something?',
      actions: [
        { text: 'Get Help', prePopulatedMessage: 'I need help finding a product.' },
        { text: 'No thanks' },
      ],
      cooldown: 30,
    },
    {
      type: 'time_on_page',
      enabled: true,
      threshold: 30,
      message: 'Finding what you need? Our assistant can help!',
      actions: [
        { text: 'Chat Now', prePopulatedMessage: 'Hi! Can you help me?' },
        { text: 'Not now' },
      ],
      cooldown: 60,
    },
    {
      type: 'scroll_depth',
      enabled: true,
      threshold: 50,
      message: 'Looks like you\'re browsing! Need any recommendations?',
      actions: [
        { text: 'Yes, please!', prePopulatedMessage: 'Can you recommend some products?' },
        { text: 'No thanks' },
      ],
      cooldown: 30,
    },
    {
      type: 'product_view',
      enabled: true,
      threshold: 3,
      message: 'I noticed you\'ve viewed several products. Can I help you decide?',
      actions: [
        { text: 'Compare Products', prePopulatedMessage: 'Can you help me compare products?' },
        { text: 'Not now' },
      ],
      cooldown: 60,
    },
  ],
};
