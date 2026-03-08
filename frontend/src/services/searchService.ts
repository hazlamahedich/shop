/**
 * Global Search API Service
 *
 * Handles API calls for global search across conversations, FAQs, etc.
 */

import { getCsrfToken } from '../stores/csrfStore';

const API_BASE = '/api/v1/search';

export interface ConversationSearchResult {
  id: number;
  platformSenderIdMasked: string;
  lastMessage: string | null;
  status: string;
  updatedAt: string;
}

export interface FaqSearchResult {
  id: number;
  question: string;
  answer: string;
}

export interface GlobalSearchResults {
  conversations: ConversationSearchResult[];
  faqs: FaqSearchResult[];
  total: number;
}

export interface GlobalSearchResponse {
  data: GlobalSearchResults;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

export const searchService = {
  async search(query: string): Promise<GlobalSearchResults> {
    if (!query || query.length < 2) {
      return { conversations: [], faqs: [], total: 0 };
    }

    const params = new URLSearchParams();
    params.append('q', query);

    const response = await fetch(`${API_BASE}?${params}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Search failed');
    }

    const data: GlobalSearchResponse = await response.json();
    return data.data;
  },
};
