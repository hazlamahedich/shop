/**
 * Tests for FaqForm Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests FAQ form modal functionality including:
 * - Form rendering in create and edit modes
 * - Input validation
 * - Character count display
 * - Save and cancel handlers
 * - Accessibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FaqForm } from './FaqForm';
import type { FaqItem } from '../../stores/businessInfoStore';

const mockFaq: FaqItem = {
  id: 1,
  question: 'What are your hours?',
  answer: 'We are open 9-5 Monday through Friday.',
  keywords: 'hours, time, open',
  orderIndex: 0,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

describe('FaqForm', () => {
  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Create Mode', () => {
    it('should not render when isOpen is false', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={false}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render dialog when isOpen is true', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Add FAQ Item')).toBeInTheDocument();
    });

    it('should render empty form fields in create mode', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByLabelText(/Question/i)).toHaveValue('');
      expect(screen.getByLabelText(/Answer/i)).toHaveValue('');
      expect(screen.getByLabelText(/Keywords/i)).toHaveValue('');
    });

    it('should call onSave with form data when submitted', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      await userEvent.type(screen.getByLabelText(/Question/i), 'Test question?');
      await userEvent.type(screen.getByLabelText(/Answer/i), 'Test answer.');
      await userEvent.type(screen.getByLabelText(/Keywords/i), 'test, keyword');

      const saveButton = screen.getByRole('button', { name: /Save FAQ/i });
      await userEvent.click(saveButton);

      expect(mockOnSave).toHaveBeenCalledWith({
        question: 'Test question?',
        answer: 'Test answer.',
        keywords: 'test, keyword',
      });
    });

    it('should call onCancel when Cancel button is clicked', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await userEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should call onCancel when backdrop is clicked', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const backdrop = screen.getByRole('dialog').firstElementChild;
      if (backdrop) {
        await userEvent.click(backdrop);
        expect(mockOnCancel).toHaveBeenCalled();
      }
    });
  });

  describe('Edit Mode', () => {
    it('should display "Edit FAQ Item" title in edit mode', () => {
      render(
        <FaqForm
          faq={mockFaq}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Edit FAQ Item')).toBeInTheDocument();
    });

    it('should pre-populate form with FAQ data', () => {
      render(
        <FaqForm
          faq={mockFaq}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByLabelText(/Question/i)).toHaveValue(mockFaq.question);
      expect(screen.getByLabelText(/Answer/i)).toHaveValue(mockFaq.answer);
      expect(screen.getByLabelText(/Keywords/i)).toHaveValue(mockFaq.keywords);
    });
  });

  describe('Validation', () => {
    it('should show error when question is empty on submit', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByRole('button', { name: /Save FAQ/i });
      await userEvent.click(saveButton);

      // Error should appear for missing question
      const questionError = screen.queryByText(/Question is required/i);
      expect(questionError).toBeInTheDocument();
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    it('should show error when answer is empty on submit', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      await userEvent.type(screen.getByLabelText(/Question/i), 'Test question?');

      const saveButton = screen.getByRole('button', { name: /Save FAQ/i });
      await userEvent.click(saveButton);

      const answerError = screen.queryByText(/Answer is required/i);
      expect(answerError).toBeInTheDocument();
      expect(mockOnSave).not.toHaveBeenCalled();
    });

    it('should enforce max length on question (200 chars)', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const questionInput = screen.getByLabelText(/Question/i) as HTMLInputElement;
      await userEvent.type(questionInput, 'a'.repeat(250));

      expect(questionInput.value.length).toBeLessThanOrEqual(200);
    });

    it('should enforce max length on answer (1000 chars)', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const answerInput = screen.getByLabelText(/Answer/i) as HTMLTextAreaElement;
      await userEvent.type(answerInput, 'a'.repeat(1500));

      expect(answerInput.value.length).toBeLessThanOrEqual(1000);
    });

    it('should clear error when user starts typing', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      // Submit empty form to trigger error
      const saveButton = screen.getByRole('button', { name: /Save FAQ/i });
      await userEvent.click(saveButton);

      const questionError = screen.queryByText(/Question is required/i);
      expect(questionError).toBeInTheDocument();

      // Start typing - error should clear
      await userEvent.type(screen.getByLabelText(/Question/i), 'Test');
      expect(screen.queryByText(/Question is required/i)).not.toBeInTheDocument();
    });
  });

  describe('Character Counts', () => {
    it('should display character count for question', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      // Character count is shown near the input
      const countText = screen.getAllByText(/0 \/ 200/i).length > 0;
      expect(countText).toBe(true);
    });

    it('should display character count for answer', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      // Character count is shown near the input
      const countText = screen.getAllByText(/0 \/ 1000/i).length > 0;
      expect(countText).toBe(true);
    });

    it('should update character count as user types', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const questionInput = screen.getByLabelText(/Question/i);
      await userEvent.type(questionInput, 'Test question?');

      // Count should update (14 chars for "Test question?")
      const countText = screen.getAllByText(/14 \/ 200/i).length > 0;
      expect(countText).toBe(true);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('should mark required fields with aria-required', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByLabelText(/Question/i)).toHaveAttribute('aria-required', 'true');
      expect(screen.getByLabelText(/Answer/i)).toHaveAttribute('aria-required', 'true');
    });

    it('should set aria-invalid on fields with errors', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      const saveButton = screen.getByRole('button', { name: /Save FAQ/i });
      await userEvent.click(saveButton);

      const questionInput = screen.getByLabelText(/Question/i);
      // aria-invalid is set when errors exist
      expect(questionInput).toHaveAttribute('aria-invalid');
    });

    it('should close on Escape key press', async () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      await userEvent.keyboard('{Escape}');

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('should disable all inputs and buttons when disabled', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
          disabled={true}
        />
      );

      expect(screen.getByLabelText(/Question/i)).toBeDisabled();
      expect(screen.getByLabelText(/Answer/i)).toBeDisabled();
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /Saving/i })).toBeDisabled();
    });
  });

  describe('Help Text', () => {
    it('should display help text for each field', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/The question customers might ask/i)).toBeInTheDocument();
      expect(screen.getByText(/The answer the bot will provide/i)).toBeInTheDocument();
      expect(screen.getByText(/Comma-separated keywords/i)).toBeInTheDocument();
    });

    it('should display tip about keywords', () => {
      render(
        <FaqForm
          faq={null}
          isOpen={true}
          onSave={mockOnSave}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/Keywords help the bot match/i)).toBeInTheDocument();
    });
  });
});
