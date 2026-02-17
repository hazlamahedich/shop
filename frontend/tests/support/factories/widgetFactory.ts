/**
 * Widget Session Data Factories
 *
 * Factory functions for generating Widget test data.
 * Used by Story 5-1: Backend Widget API tests.
 *
 * @tags fixtures test-data factories widget story-5-1
 */

import { faker } from '@faker-js/faker';

export interface WidgetSession {
  sessionId: string;
  merchantId: number;
  createdAt: string;
  lastActivityAt: string;
  expiresAt: string;
}

export interface WidgetMessage {
  messageId: string;
  sessionId: string;
  content: string;
  sender: 'user' | 'bot';
  createdAt: string;
}

export interface WidgetConfig {
  enabled: boolean;
  botName: string;
  welcomeMessage: string;
  theme: WidgetTheme;
  allowedDomains: string[];
}

export interface WidgetTheme {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  position: string;
  borderRadius: number;
}

export const createWidgetSession = (overrides: Partial<WidgetSession> = {}): WidgetSession => {
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);

  const baseSession: WidgetSession = {
    sessionId: faker.string.uuid(),
    merchantId: 1,
    createdAt: now.toISOString(),
    lastActivityAt: now.toISOString(),
    expiresAt: expiresAt.toISOString(),
  };

  return { ...baseSession, ...overrides };
};

export const createWidgetMessage = (overrides: Partial<WidgetMessage> = {}): WidgetMessage => {
  const baseMessage: WidgetMessage = {
    messageId: faker.string.uuid(),
    sessionId: faker.string.uuid(),
    content: faker.lorem.sentence(),
    sender: 'bot',
    createdAt: new Date().toISOString(),
  };

  return { ...baseMessage, ...overrides };
};

export const createWidgetConfig = (overrides: Partial<WidgetConfig> = {}): WidgetConfig => {
  const baseConfig: WidgetConfig = {
    enabled: true,
    botName: 'Shopping Assistant',
    welcomeMessage: 'Hi! How can I help you today?',
    theme: createWidgetTheme(),
    allowedDomains: [],
  };

  return { ...baseConfig, ...overrides };
};

export const createWidgetTheme = (overrides: Partial<WidgetTheme> = {}): WidgetTheme => {
  const baseTheme: WidgetTheme = {
    primaryColor: '#6366f1',
    backgroundColor: '#ffffff',
    textColor: '#1f2937',
    position: 'bottom-right',
    borderRadius: 16,
  };

  return { ...baseTheme, ...overrides };
};

export const createConversationContext = (messageCount: number): string[] => {
  const contexts = [
    'Hi, I am looking for shoes',
    'What brands do you have?',
    'Do you have Nike in size 10?',
    'How much are they?',
    'Do you have any discounts?',
    'What colors are available?',
    'Can I return them if they dont fit?',
    'How long is shipping?',
    'Do you ship internationally?',
    'What payment methods do you accept?',
    'Can I track my order?',
    'Do you offer gift wrapping?',
    'Whats your return policy?',
    'Are there any sales coming up?',
    'Do you have a loyalty program?',
  ];

  return contexts.slice(0, Math.min(messageCount, contexts.length));
};

export const createRateLimitTestMessages = (count: number): string[] => {
  return Array.from({ length: count }, (_, i) => `Rate limit test message ${i}`);
};
