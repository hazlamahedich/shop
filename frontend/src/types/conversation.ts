/**
 * Conversation Types
 *
 * Types for conversation list with pagination
 */

export type ConversationStatus = 'active' | 'handoff' | 'closed';
export type Sentiment = 'positive' | 'neutral' | 'negative';

export interface Conversation {
  id: number;
  platformSenderId: string;
  platformSenderIdMasked: string;
  lastMessage: string | null;
  status: ConversationStatus;
  sentiment: Sentiment;
  messageCount: number;
  updatedAt: string;
  createdAt: string;
}

export interface PaginationMeta {
  total: number;
  page: number;
  perPage: number;
  totalPages: number;
}

export interface ConversationsResponse {
  data: Conversation[];
  meta: {
    pagination: PaginationMeta;
  };
}

export interface ConversationsListParams {
  page?: number;
  perPage?: number;
  sortBy?: 'updated_at' | 'status' | 'created_at';
  sortOrder?: 'asc' | 'desc';
}
