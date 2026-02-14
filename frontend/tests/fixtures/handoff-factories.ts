/**
 * Handoff Detection Data Factories
 *
 * Provides factory functions for generating test data
 * for Story 4-5 Human Assistance Detection tests.
 *
 * Usage:
 *   import { createHandoffConversation, createHandoffMessage } from '../fixtures/handoff-factories';
 *   const conversation = createHandoffConversation({ handoffReason: 'keyword' });
 *
 * @package frontend/tests/fixtures/handoff-factories.ts
 */

import { faker } from '@faker-js/faker';

export type HandoffStatus = 'none' | 'pending' | 'active' | 'resolved';
export type HandoffReason = 'keyword' | 'low_confidence' | 'clarification_loop' | null;
export type ConversationStatus = 'active' | 'handoff' | 'closed';

export interface HandoffConversation {
  id: number;
  platformSenderId: string;
  status: ConversationStatus;
  handoffStatus: HandoffStatus;
  handoffReason: HandoffReason;
  handoffTriggeredAt: string | null;
  consecutiveLowConfidenceCount: number;
  lastMessage: string;
  createdAt: string;
  messages?: HandoffMessage[];
}

export interface HandoffMessage {
  id: number;
  role: 'customer' | 'bot';
  content: string;
  createdAt?: string;
}

export const HANDOFF_KEYWORDS = [
  'human',
  'person',
  'agent',
  'customer service',
  'real person',
  'talk to someone',
  'speak to someone',
  'representative',
  'manager',
  'support',
  'live chat',
  'operator',
  'help desk',
];

export const DEFAULT_HANDOFF_MESSAGE =
  "I'm having trouble understanding. Sorry! Let me get someone who can help. I've flagged this - our team will respond within 12 hours.";

export const createHandoffConversation = (
  overrides: Partial<HandoffConversation> = {}
): HandoffConversation => {
  const id = faker.number.int({ min: 1, max: 99999 });
  const now = new Date().toISOString();

  const base: HandoffConversation = {
    id,
    platformSenderId: `psid_${faker.string.alphanumeric(16)}`,
    status: 'active',
    handoffStatus: 'none',
    handoffReason: null,
    handoffTriggeredAt: null,
    consecutiveLowConfidenceCount: 0,
    lastMessage: faker.hacker.phrase(),
    createdAt: now,
  };

  return { ...base, ...overrides };
};

export const createKeywordTriggeredConversation = (
  keyword: string = 'human',
  overrides: Partial<HandoffConversation> = {}
): HandoffConversation => {
  return createHandoffConversation({
    status: 'handoff',
    handoffStatus: 'pending',
    handoffReason: 'keyword',
    handoffTriggeredAt: new Date().toISOString(),
    lastMessage: `I want to talk to a ${keyword}`,
    ...overrides,
  });
};

export const createLowConfidenceConversation = (
  confidenceCount: number = 3,
  overrides: Partial<HandoffConversation> = {}
): HandoffConversation => {
  return createHandoffConversation({
    status: 'handoff',
    handoffStatus: 'pending',
    handoffReason: 'low_confidence',
    handoffTriggeredAt: new Date().toISOString(),
    consecutiveLowConfidenceCount: confidenceCount,
    lastMessage: "I don't understand",
    ...overrides,
  });
};

export const createClarificationLoopConversation = (
  loopType: string = 'budget',
  overrides: Partial<HandoffConversation> = {}
): HandoffConversation => {
  return createHandoffConversation({
    status: 'handoff',
    handoffStatus: 'pending',
    handoffReason: 'clarification_loop',
    handoffTriggeredAt: new Date().toISOString(),
    lastMessage: `I don't know my ${loopType}`,
    ...overrides,
  });
};

export const createActiveConversation = (
  overrides: Partial<HandoffConversation> = {}
): HandoffConversation => {
  return createHandoffConversation({
    status: 'active',
    handoffStatus: 'none',
    consecutiveLowConfidenceCount: 0,
    ...overrides,
  });
};

export const createHandoffMessage = (
  overrides: Partial<HandoffMessage> = {}
): HandoffMessage => {
  const base: HandoffMessage = {
    id: faker.number.int({ min: 1, max: 99999 }),
    role: faker.helpers.arrayElement(['customer', 'bot']),
    content: faker.hacker.phrase(),
    createdAt: new Date().toISOString(),
  };

  return { ...base, ...overrides };
};

export const createConversationWithMessages = (
  conversationOverrides: Partial<HandoffConversation> = {},
  messageCount: number = 3
): HandoffConversation => {
  const messages: HandoffMessage[] = [];

  for (let i = 0; i < messageCount; i++) {
    messages.push(
      createHandoffMessage({
        id: i + 1,
        role: i % 2 === 0 ? 'customer' : 'bot',
      })
    );
  }

  return createHandoffConversation({
    messages,
    ...conversationOverrides,
  });
};

export const createHandoffConversationList = (
  count: number,
  options: {
    pendingCount?: number;
    activeCount?: number;
    resolvedCount?: number;
  } = {}
): HandoffConversation[] => {
  const { pendingCount = 0, activeCount = 0, resolvedCount = 0 } = options;
  const conversations: HandoffConversation[] = [];
  let idCounter = 1;

  for (let i = 0; i < pendingCount; i++) {
    conversations.push(
      createKeywordTriggeredConversation(undefined, { id: idCounter++ })
    );
  }

  for (let i = 0; i < activeCount; i++) {
    conversations.push(
      createHandoffConversation({
        id: idCounter++,
        status: 'handoff',
        handoffStatus: 'active',
        handoffReason: 'keyword',
      })
    );
  }

  for (let i = 0; i < resolvedCount; i++) {
    conversations.push(
      createHandoffConversation({
        id: idCounter++,
        status: 'handoff',
        handoffStatus: 'resolved',
        handoffReason: 'keyword',
      })
    );
  }

  while (conversations.length < count) {
    conversations.push(createActiveConversation({ id: idCounter++ }));
  }

  return conversations;
};

export const createHandoffApiSuccessResponse = (
  conversation: HandoffConversation
) => {
  return {
    data: conversation,
    meta: {
      requestId: faker.string.uuid(),
      timestamp: new Date().toISOString(),
    },
  };
};

export const createHandoffApiListResponse = (
  conversations: HandoffConversation[],
  total?: number
) => {
  return {
    data: {
      conversations,
      total: total ?? conversations.length,
    },
    meta: {
      requestId: faker.string.uuid(),
      timestamp: new Date().toISOString(),
    },
  };
};

export const createHandoffApiErrorResponse = (
  code: number,
  message: string
) => {
  return {
    error: message,
    code,
    message,
    meta: {
      requestId: faker.string.uuid(),
      timestamp: new Date().toISOString(),
    },
  };
};
