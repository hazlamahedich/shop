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
  // Search and filter parameters
  search?: string;
  dateFrom?: string;  // ISO 8601 date string
  dateTo?: string;    // ISO 8601 date string
  status?: ConversationStatus[];
  sentiment?: Sentiment[];
  hasHandoff?: boolean;
}

// Filter state for the conversations list
export interface ConversationsFilterState {
  searchQuery: string;
  dateRange: {
    from: string | null;
    to: string | null;
  };
  statusFilters: ConversationStatus[];
  sentimentFilters: Sentiment[];
  hasHandoffFilter: boolean | null;  // true = has handoff, false = no handoff, null = any
}

// Saved filter for quick re-application
export interface SavedFilter {
  id: string;
  name: string;
  filters: ConversationsFilterState;
  createdAt: string;
}

// ============================================
// Story 4-8: Conversation History Types
// ============================================

export interface MessageHistoryItem {
  id: number;
  sender: 'customer' | 'bot';
  content: string;
  createdAt: string;
  confidenceScore?: number | null;
}

export interface CartStateItem {
  productId: string;
  name: string;
  quantity: number;
}

export interface CartState {
  items: CartStateItem[];
}

export interface ExtractedConstraints {
  budget?: string | null;
  size?: string | null;
  category?: string | null;
}

export interface ConversationContext {
  cartState: CartState | null;
  extractedConstraints: ExtractedConstraints | null;
}

export interface HandoffContext {
  triggerReason: string;
  triggeredAt: string;
  urgencyLevel: 'high' | 'medium' | 'low';
  waitTimeSeconds: number;
}

export interface CustomerInfo {
  maskedId: string;
  orderCount: number;
}

export interface ConversationHistoryData {
  conversationId: number;
  messages: MessageHistoryItem[];
  context: ConversationContext;
  handoff: HandoffContext;
  customer: CustomerInfo;
}

export interface ConversationHistoryMeta {
  requestId: string;
  timestamp: string;
}

export interface ConversationHistoryResponse {
  data: ConversationHistoryData;
  meta: ConversationHistoryMeta;
}
