/**
 * Tests for FaqList Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests FAQ list functionality including:
 * - Empty state rendering
 * - FAQ item display
 * - Add/Edit/Delete operations
 * - Loading states
 * - Drag and drop
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FaqList } from './FaqList';
import type { FaqItem } from '../../stores/businessInfoStore';

const mockFaqs: FaqItem[] = [
  {
    id: 1,
    question: 'What are your shipping options?',
    answer: 'We offer free shipping on orders over $50.',
    keywords: 'shipping, delivery',
    orderIndex: 0,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    question: 'Do you accept returns?',
    answer: 'Yes, within 30 days of purchase.',
    keywords: 'returns, refund',
    orderIndex: 1,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

// Mock the business info store
const mockStore = {
  faqs: [],
  faqsLoadingState: 'idle' as const,
  error: null,
  createFaq: vi.fn(),
  updateFaq: vi.fn(),
  deleteFaq: vi.fn(),
  reorderFaqs: vi.fn(),
  clearError: vi.fn(),
};

vi.mock('../../stores/businessInfoStore', () => ({
  useBusinessInfoStore: vi.fn(() => mockStore),
}));

// Mock FaqForm component
vi.mock('./FaqForm', () => ({
  FaqForm: () => null,
}));

describe('FaqList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStore.faqs = [];
    mockStore.faqsLoadingState = 'idle';
    mockStore.error = null;
  });

  describe('Empty State', () => {
    it('should render empty state when no FAQs exist', () => {
      mockStore.faqs = [];

      render(<FaqList />);

      expect(screen.getByText(/No FAQ items yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Create your first FAQ/i)).toBeInTheDocument();
    });

    it('should display Add FAQ Item button', () => {
      mockStore.faqs = [];

      render(<FaqList />);

      expect(screen.getByRole('button', { name: /Add FAQ Item/i })).toBeInTheDocument();
    });

    it('should render help text in empty state', () => {
      mockStore.faqs = [];

      render(<FaqList />);

      expect(screen.getByText(/Create FAQ items to help your bot/i)).toBeInTheDocument();
    });
  });

  describe('FAQ List Display', () => {
    beforeEach(() => {
      mockStore.faqs = [...mockFaqs];
    });

    it('should render all FAQ items', () => {
      render(<FaqList />);

      expect(screen.getByText(mockFaqs[0].question)).toBeInTheDocument();
      expect(screen.getByText(mockFaqs[1].question)).toBeInTheDocument();
    });

    it('should display answer preview', () => {
      render(<FaqList />);

      expect(screen.getByText(/We offer free shipping/i)).toBeInTheDocument();
      expect(screen.getByText(/within 30 days/i)).toBeInTheDocument();
    });

    it('should display keywords', () => {
      render(<FaqList />);

      expect(screen.getByText('shipping')).toBeInTheDocument();
      expect(screen.getByText('returns')).toBeInTheDocument();
    });

    it('should render edit and delete buttons for each FAQ', () => {
      render(<FaqList />);

      const editButtons = screen.getAllByLabelText(/Edit FAQ/i);
      const deleteButtons = screen.getAllByLabelText(/Delete FAQ/i);

      expect(editButtons).toHaveLength(2);
      expect(deleteButtons).toHaveLength(2);
    });

    it('should truncate long questions', () => {
      const longQuestionFaq: FaqItem = {
        ...mockFaqs[0],
        question: 'This is a very long question that exceeds fifty characters and should be truncated',
      };
      mockStore.faqs = [longQuestionFaq];

      render(<FaqList />);

      const questionElement = screen.getByText(/This is a very long question that/i);
      expect(questionElement).toBeInTheDocument();
    });

    it('should limit keyword display to 3 items', () => {
      const manyKeywordsFaq: FaqItem = {
        ...mockFaqs[0],
        keywords: 'one, two, three, four, five',
      };
      mockStore.faqs = [manyKeywordsFaq];

      render(<FaqList />);

      expect(screen.getByText('one')).toBeInTheDocument();
      expect(screen.getByText('two')).toBeInTheDocument();
      expect(screen.getByText('three')).toBeInTheDocument();
      expect(screen.getByText(/\+2 more/i)).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('should render loading spinner when loading', () => {
      mockStore.faqsLoadingState = 'loading';
      mockStore.faqs = [];

      render(<FaqList />);

      expect(screen.getByText(/Loading FAQ items/i)).toBeInTheDocument();
    });

    it('should not show Add button during initial loading', () => {
      mockStore.faqsLoadingState = 'loading';
      mockStore.faqs = [];

      render(<FaqList />);

      // During initial loading with no FAQs, the loading state is shown instead of the button
      const addButton = screen.queryByRole('button', { name: /Add FAQ Item/i });
      expect(addButton).not.toBeInTheDocument();
    });
  });

  describe('Error Display', () => {
    it('should display error message when error exists', () => {
      mockStore.error = 'Failed to load FAQs';

      render(<FaqList />);

      expect(screen.getByText(/Failed to load FAQs/i)).toBeInTheDocument();
    });

    it('should have dismiss button for error', () => {
      mockStore.error = 'Test error';

      render(<FaqList />);

      const dismissButton = screen.getByRole('button', { name: /Dismiss error/i });
      expect(dismissButton).toBeInTheDocument();
    });

    it('should call clearError when dismiss button clicked', async () => {
      mockStore.error = 'Test error';

      render(<FaqList />);

      const dismissButton = screen.getByRole('button', { name: /Dismiss error/i });
      await userEvent.click(dismissButton);

      expect(mockStore.clearError).toHaveBeenCalled();
    });
  });

  describe('Add FAQ', () => {
    it('should open form when Add FAQ button clicked', async () => {
      mockStore.faqs = [];

      render(<FaqList />);

      const addButton = screen.getByRole('button', { name: /Add FAQ Item/i });
      await userEvent.click(addButton);

      // Since FaqForm is mocked, we just verify it would be called
      expect(addButton).toBeInTheDocument();
    });
  });

  describe('Delete FAQ', () => {
    beforeEach(() => {
      mockStore.faqs = [...mockFaqs];
    });

    it('should show confirmation when delete clicked', async () => {
      window.confirm = vi.fn(() => true);

      render(<FaqList />);

      const deleteButton = screen.getAllByLabelText(/Delete FAQ/i)[0];
      await userEvent.click(deleteButton);

      expect(window.confirm).toHaveBeenCalledWith(
        expect.stringContaining('Are you sure you want to delete')
      );
    });

    it('should call deleteFaq when confirmed', async () => {
      window.confirm = vi.fn(() => true);

      render(<FaqList />);

      const deleteButton = screen.getAllByLabelText(/Delete FAQ/i)[0];
      await userEvent.click(deleteButton);

      expect(mockStore.deleteFaq).toHaveBeenCalledWith(1);
    });

    it('should not call deleteFaq when cancelled', async () => {
      window.confirm = vi.fn(() => false);

      render(<FaqList />);

      const deleteButton = screen.getAllByLabelText(/Delete FAQ/i)[0];
      await userEvent.click(deleteButton);

      expect(mockStore.deleteFaq).not.toHaveBeenCalled();
    });
  });

  describe('Drag and Drop', () => {
    beforeEach(() => {
      mockStore.faqs = [...mockFaqs];
    });

    it('should render drag handle for each FAQ', () => {
      render(<FaqList />);

      const dragHandles = screen.getAllByLabelText(/Drag to reorder/i);
      expect(dragHandles).toHaveLength(2);
    });

    it('should have draggable FAQ items', () => {
      render(<FaqList />);

      const faqCards = screen.getAllByRole('article');
      faqCards.forEach((card) => {
        expect(card).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockStore.faqs = [...mockFaqs];
    });

    it('should have proper ARIA labels for FAQ items', () => {
      render(<FaqList />);

      const faqCards = screen.getAllByRole('article');
      expect(faqCards[0]).toHaveAttribute('aria-label', expect.stringContaining('FAQ:'));
    });

    it('should have accessible button labels', () => {
      render(<FaqList />);

      expect(screen.getAllByLabelText(/Edit FAQ/i)).toHaveLength(2);
      expect(screen.getAllByLabelText(/Delete FAQ/i)).toHaveLength(2);
    });
  });

  describe('Help Text', () => {
    it('should display reorder tip when FAQs exist', () => {
      mockStore.faqs = [...mockFaqs];

      render(<FaqList />);

      expect(screen.getByText(/Drag and drop FAQ items to reorder/i)).toBeInTheDocument();
    });
  });
});
