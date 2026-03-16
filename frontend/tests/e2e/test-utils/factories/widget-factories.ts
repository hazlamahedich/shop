/**
 * @fileoverview Factory functions for widget test data
 * @description Reusable mock data generators with overrides for E2E tests
 */

import { faker } from '@faker-js/faker';

export type WidgetTheme = {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  botBubbleColor: string;
  userBubbleColor: string;
  position: string;
  borderRadius: number;
  width: number;
  height: number;
  fontFamily: string;
  fontSize: number;
};

export type QuickReply = {
  id: string;
  text: string;
  icon: string;
  payload: string;
};

export type WidgetConfig = {
  enabled: boolean;
  botName: string;
  bot_name: string;
  welcomeMessage: string;
  welcome_message: string;
  theme: WidgetTheme;
  allowedDomains: string[];
  shopDomain: string;
  shop_domain: string;
};

export type WidgetSession = {
  session_id: string;
  merchant_id: string;
  expires_at: string;
  created_at: string;
  last_activity_at: string;
};

export type WidgetMessageResponse = {
  message_id: string;
  content: string;
  sender: string;
  created_at: string;
  quick_replies: QuickReply[] | null;
};

/**
 * Create mock widget theme
 */
export const createWidgetTheme = (overrides: Partial<WidgetTheme> = {}): WidgetTheme => ({
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1e293b',
  botBubbleColor: '#f1f5f9',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 12,
  width: 400,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
  ...overrides,
});

/**
 * Create mock quick reply
 */
export const createQuickReply = (overrides: Partial<QuickReply> = {}): QuickReply => ({
  id: faker.string.alphanumeric(8),
  text: faker.word.sample(),
  icon: '✓',
  payload: faker.string.alphanumeric(16),
  ...overrides,
});

/**
 * Create standard Yes/No quick replies for testing
 */
export const createYesNoQuickReplies = (): QuickReply[] => [
  { id: 'yes', text: 'Yes', icon: '✓', payload: 'user_confirmed' },
  { id: 'no', text: 'No', icon: '✗', payload: 'user_declined' },
];

/**
 * Create mock widget config
 */
export const createWidgetConfig = (overrides: Partial<WidgetConfig> = {}): WidgetConfig => ({
  enabled: true,
  botName: 'Test Bot',
  bot_name: 'Test Bot',
  welcomeMessage: 'Hello! How can I help?',
  welcome_message: 'Hello! How can I help?',
  theme: createWidgetTheme(),
  allowedDomains: [],
  shopDomain: 'test.myshopify.com',
  shop_domain: 'test.myshopify.com',
  ...overrides,
});

/**
 * Create mock widget session
 */
export const createWidgetSession = (overrides: Partial<WidgetSession> = {}): WidgetSession => ({
  session_id: faker.string.uuid(),
  merchant_id: '4',
  expires_at: new Date(Date.now() + 3600000).toISOString(),
  created_at: new Date().toISOString(),
  last_activity_at: new Date().toISOString(),
  ...overrides,
});

/**
 * Create mock widget message response
 */
export const createWidgetMessageResponse = (
  userMessage: string,
  options: { withQuickReplies?: boolean } = {}
): WidgetMessageResponse => ({
  message_id: `msg-${Date.now()}`,
  content: `You said: "${userMessage}". How can I help further?`,
  sender: 'bot',
  created_at: new Date().toISOString(),
  quick_replies: options.withQuickReplies ? createYesNoQuickReplies() : null,
});
