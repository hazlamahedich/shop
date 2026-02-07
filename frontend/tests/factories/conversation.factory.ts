/**
 * Conversation Factory
 *
 * Factory functions for generating test conversation data
 * Follows data-factories.md patterns: dynamic, parallel-safe, explicit intent
 *
 * @tags factories conversation story-3-1
 */

import { faker } from '@faker-js/faker';

/**
 * Conversation status types
 */
export type ConversationStatus = 'active' | 'handoff' | 'closed';

/**
 * Conversation data structure matching API response
 */
export interface ConversationData {
  id?: number;
  platformSenderId?: string;
  platformSenderIdMasked?: string;
  lastMessage?: string | null;
  status?: ConversationStatus;
  sentiment?: 'positive' | 'neutral' | 'negative';
  messageCount?: number;
  updatedAt?: string;
  createdAt?: string;
}

/**
 * Create a test conversation with sensible defaults
 * Use overrides to specify what matters for each test
 *
 * @example
 * const activeConv = createConversation({ status: 'active', messageCount: 5 });
 * const oldConv = createConversation({ updatedAt: '2024-01-01T00:00:00Z' });
 */
export const createConversation = (overrides: Partial<ConversationData> = {}): ConversationData => {
  const platformSenderId = `customer_${faker.string.uuid()}`;
  const lastMessage = faker.lorem.sentence();

  const conversation: ConversationData = {
    id: faker.number.int({ min: 1, max: 999999 }),
    platformSenderId,
    platformSenderIdMasked: `${platformSenderId.substring(0, 4)}****`,
    lastMessage,
    status: faker.helpers.arrayElement(['active', 'handoff', 'closed']) as ConversationStatus,
    sentiment: faker.helpers.arrayElement(['positive', 'neutral', 'negative']) as any,
    messageCount: faker.number.int({ min: 0, max: 50 }),
    updatedAt: faker.date.recent({ days: 7 }).toISOString(),
    createdAt: faker.date.past({ years: 1 }).toISOString(),
    ...overrides,
  };

  return conversation;
};

/**
 * Create multiple conversations for pagination testing
 *
 * @param count - Number of conversations to create
 * @param overrides - Common overrides for all conversations
 * @returns Array of conversation data
 */
export const createConversations = (
  count: number,
  overrides: Partial<ConversationData> = {}
): ConversationData[] => {
  return Array.from({ length: count }, (_, i) =>
    createConversation({
      ...overrides,
      id: i + 1,
      updatedAt: faker.date.recent({ days: 7 - i * 0.1 }).toISOString(), // Stagger timestamps
    })
  );
};

/**
 * Create active conversation (helper)
 */
export const createActiveConversation = (overrides: Partial<ConversationData> = {}): ConversationData => {
  return createConversation({ ...overrides, status: 'active' });
};

/**
 * Create conversation needing handoff (helper)
 */
export const createHandoffConversation = (overrides: Partial<ConversationData> = {}): ConversationData => {
  return createConversation({ ...overrides, status: 'handoff' });
};

/**
 * Create closed conversation (helper)
 */
export const createClosedConversation = (overrides: Partial<ConversationData> = {}): ConversationData => {
  return createConversation({ ...overrides, status: 'closed' });
};

/**
 * Create conversation with specific message count
 */
export const createConversationWithMessages = (messageCount: number): ConversationData => {
  return createConversation({ messageCount });
};

/**
 * Create conversation from specific time ago
 * Useful for testing sort order and "time ago" display
 */
export const createConversationFromTimeAgo = (
  timeAgo: string,
  overrides: Partial<ConversationData> = {}
): ConversationData => {
  let updatedAt: string;

  const now = new Date();

  switch (timeAgo) {
    case 'just-now':
      updatedAt = new Date(now.getTime() - 10 * 1000).toISOString(); // 10 seconds ago
      break;
    case '1m':
      updatedAt = new Date(now.getTime() - 60 * 1000).toISOString(); // 1 minute ago
      break;
    case '5m':
      updatedAt = new Date(now.getTime() - 5 * 60 * 1000).toISOString(); // 5 minutes ago
      break;
    case '1h':
      updatedAt = new Date(now.getTime() - 60 * 60 * 1000).toISOString(); // 1 hour ago
      break;
    case '2h':
      updatedAt = new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(); // 2 hours ago
      break;
    case '1d':
      updatedAt = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString(); // 1 day ago
      break;
    case '1w':
      updatedAt = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString(); // 1 week ago
      break;
    default:
      updatedAt = now.toISOString();
  }

  return createConversation({ ...overrides, updatedAt });
};

/**
 * Pagination response factory
 * Creates complete API response with pagination metadata
 */
export interface PaginatedResponse {
  data: ConversationData[];
  meta: {
    pagination: {
      total: number;
      page: number;
      perPage: number;
      totalPages: number;
    };
  };
}

export const createPaginatedResponse = (
  conversations: ConversationData[],
  total: number,
  page: number = 1,
  perPage: number = 20
): PaginatedResponse => {
  return {
    data: conversations,
    meta: {
      pagination: {
        total,
        page,
        perPage,
        totalPages: Math.ceil(total / perPage),
      },
    },
  };
};

/**
 * Specialized factories for common test scenarios
 */

/**
 * Empty conversation list (empty state scenario)
 */
export const createEmptyConversationList = (): PaginatedResponse => {
  return createPaginatedResponse([], 0, 1, 20);
};

/**
 * Single page of conversations (no pagination needed)
 */
export const createSinglePageConversations = (count: number = 10): PaginatedResponse => {
  const conversations = createConversations(count);
  return createPaginatedResponse(conversations, count, 1, 20);
};

/**
 * Multi-page conversation list (for pagination testing)
 */
export const createMultiPageConversations = (
  totalPages: number = 3,
  perPage: number = 20
): PaginatedResponse => {
  const total = totalPages * perPage;
  const conversations = createConversations(perPage);
  return createPaginatedResponse(conversations, total, 1, perPage);
};
