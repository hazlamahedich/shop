/**
 * ConversationHistory Page Unit Tests - Story 4-8
 *
 * Tests for the ConversationHistory page component including:
 * - formatConfidence utility function edge cases
 * - Loading and error states
 * - Back navigation
 * - Message rendering
 *
 * Acceptance Criteria Coverage:
 * - AC2: Bot Confidence Scores (formatting)
 * - AC6: Visual Message Distinction
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ConversationHistory from './ConversationHistory';
import { conversationsService } from '../services/conversations';
import type { ConversationHistoryResponse } from '../types/conversation';

vi.mock('../services/conversations', () => ({
  conversationsService: {
    getConversationHistory: vi.fn(),
  },
}));

const mockGetConversationHistory = vi.mocked(conversationsService.getConversationHistory);

const createMockHistoryResponse = (overrides: {
  conversationId?: number;
  platformSenderId?: string;
  platform?: string;
  messages?: Array<{ id: number; sender: 'customer' | 'bot' | 'merchant'; content: string; createdAt: string; confidenceScore?: number | null }>;
  context?: { cartState: { items: Array<{ productId: string; name: string; quantity: number }> } | null; extractedConstraints: { budget?: string | null; size?: string | null; category?: string | null } | null };
  handoff?: { triggerReason: string; triggeredAt: string; urgencyLevel: 'high' | 'medium' | 'low'; waitTimeSeconds: number };
  customer?: { maskedId: string; orderCount: number };
} = {}): ConversationHistoryResponse => ({
  data: {
    conversationId: overrides.conversationId ?? 1,
    platformSenderId: overrides.platformSenderId ?? 'test-sender-id',
    platform: overrides.platform ?? 'messenger',
    messages: overrides.messages ?? [
      { id: 1, sender: 'customer' as const, content: 'Hello', createdAt: new Date().toISOString(), confidenceScore: null },
    ],
    context: overrides.context ?? { cartState: null, extractedConstraints: null },
    handoff: overrides.handoff ?? {
      triggerReason: 'keyword',
      triggeredAt: new Date().toISOString(),
      urgencyLevel: 'medium' as const,
      waitTimeSeconds: 300,
    },
    customer: overrides.customer ?? { maskedId: '1234****', orderCount: 0 },
  },
  meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
});

const renderWithRouter = (initialEntry = '/conversations/1/history') => {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/conversations/:conversationId/history" element={<ConversationHistory />} />
        <Route path="/handoff-queue" element={<div data-testid="handoff-queue-page">Handoff Queue</div>} />
      </Routes>
    </MemoryRouter>
  );
};

describe('ConversationHistory Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('formatConfidence Edge Cases', () => {
    it('displays 0% confidence for score of 0', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'Low confidence', createdAt: new Date().toISOString(), confidenceScore: 0 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('confidence-badge')).toBeInTheDocument();
      });

      expect(screen.getByText('Confidence: 0%')).toBeInTheDocument();
    });

    it('displays 100% confidence for score of 1', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'High confidence', createdAt: new Date().toISOString(), confidenceScore: 1 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('confidence-badge')).toBeInTheDocument();
      });

      expect(screen.getByText('Confidence: 100%')).toBeInTheDocument();
    });

    it('displays rounded percentage for decimal scores', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'Decimal', createdAt: new Date().toISOString(), confidenceScore: 0.856 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('confidence-badge')).toBeInTheDocument();
      });

      expect(screen.getByText('Confidence: 86%')).toBeInTheDocument();
    });

    it('does not display badge for null confidence', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'customer', content: 'Customer message', createdAt: new Date().toISOString(), confidenceScore: null },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('message-bubble')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('confidence-badge')).not.toBeInTheDocument();
    });

    it('does not display badge for undefined confidence', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'No score', createdAt: new Date().toISOString(), confidenceScore: undefined },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('message-bubble')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('confidence-badge')).not.toBeInTheDocument();
    });

    it('handles very small confidence scores', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'Tiny score', createdAt: new Date().toISOString(), confidenceScore: 0.001 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('confidence-badge')).toBeInTheDocument();
      });

      expect(screen.getByText('Confidence: 0%')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading message while fetching', () => {
      mockGetConversationHistory.mockImplementation(() => new Promise(() => {}));

      renderWithRouter();

      expect(screen.getByText('Loading conversation...')).toBeInTheDocument();
    });

    it('has page test id during loading', () => {
      mockGetConversationHistory.mockImplementation(() => new Promise(() => {}));

      renderWithRouter();

      expect(screen.getByTestId('conversation-history-page')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('displays error message when fetch fails', async () => {
      mockGetConversationHistory.mockRejectedValueOnce(new Error('Failed to load conversation history'));

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Failed to load conversation history')).toBeInTheDocument();
      });
    });

    it('displays error message for network errors', async () => {
      mockGetConversationHistory.mockRejectedValueOnce(new Error('Network error'));

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('displays fallback error message for unknown errors', async () => {
      mockGetConversationHistory.mockRejectedValueOnce(new Error());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText(/not found|Failed to load/i)).toBeInTheDocument();
      });
    });

    it('displays back button in error state', async () => {
      mockGetConversationHistory.mockRejectedValueOnce(new Error('Test error'));

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Back to Queue')).toBeInTheDocument();
      });
    });
  });

  describe('Not Found State', () => {
    it('displays not found message when history is null', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(null as any);

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Conversation not found')).toBeInTheDocument();
      });
    });

    it('displays back button in not found state', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(null as any);

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Back to Queue')).toBeInTheDocument();
      });
    });
  });

  describe('Message Rendering', () => {
    it('displays customer messages with correct sender attribute', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'customer', content: 'Customer message', createdAt: new Date().toISOString(), confidenceScore: null },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('message-bubble')).toBeInTheDocument();
      });

      expect(screen.getByTestId('message-bubble')).toHaveAttribute('data-sender', 'customer');
    });

    it('displays bot messages with correct sender attribute', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'Bot message', createdAt: new Date().toISOString(), confidenceScore: 0.9 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('message-bubble')).toBeInTheDocument();
      });

      expect(screen.getByTestId('message-bubble')).toHaveAttribute('data-sender', 'bot');
    });

    it('displays shopper label for customer messages', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'customer', content: 'Test', createdAt: new Date().toISOString(), confidenceScore: null },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Shopper')).toBeInTheDocument();
      });
    });

    it('displays bot label for bot messages', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          messages: [
            { id: 1, sender: 'bot', content: 'Test', createdAt: new Date().toISOString(), confidenceScore: 0.9 },
          ],
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Bot')).toBeInTheDocument();
      });
    });
  });

  describe('Back Navigation', () => {
    it('navigates to handoff queue when back button clicked', async () => {
      const user = userEvent.setup({ delay: null });
      mockGetConversationHistory.mockResolvedValueOnce(createMockHistoryResponse());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /back to queue/i })).toBeInTheDocument();
      });

      await act(async () => {
        await user.click(screen.getByRole('button', { name: /back to queue/i }));
      });

      await waitFor(() => {
        expect(screen.getByTestId('handoff-queue-page')).toBeInTheDocument();
      });
    });

    it('navigates to handoff queue from error state', async () => {
      const user = userEvent.setup({ delay: null });
      mockGetConversationHistory.mockRejectedValueOnce(new Error('Test error'));

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('Back to Queue')).toBeInTheDocument();
      });

      await act(async () => {
        await user.click(screen.getByText('Back to Queue'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('handoff-queue-page')).toBeInTheDocument();
      });
    });
  });

  describe('Header', () => {
    it('displays page title', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(createMockHistoryResponse());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Conversation History' })).toBeInTheDocument();
      });
    });

    it('displays customer masked ID', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(
        createMockHistoryResponse({
          customer: { maskedId: '9999****', orderCount: 0 },
        })
      );

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByText('9999****')).toBeInTheDocument();
      });
    });
  });

  describe('Component Structure', () => {
    it('has correct page test id', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(createMockHistoryResponse());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('conversation-history-page')).toBeInTheDocument();
      });
    });

    it('displays message list', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(createMockHistoryResponse());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('message-list')).toBeInTheDocument();
      });
    });

    it('displays context sidebar', async () => {
      mockGetConversationHistory.mockResolvedValueOnce(createMockHistoryResponse());

      renderWithRouter();

      await waitFor(() => {
        expect(screen.getByTestId('context-sidebar')).toBeInTheDocument();
      });
    });
  });
});
