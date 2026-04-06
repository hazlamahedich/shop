import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { FeedbackRating } from './FeedbackRating';
import type { WidgetTheme, FeedbackRatingValue } from '../types/widget';

const mockTheme: WidgetTheme = {
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
};

const mockDarkTheme: WidgetTheme = {
  ...mockTheme,
  mode: 'dark',
};

describe('FeedbackRating', () => {
  const originalMatchMedia = window.matchMedia;
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
  });

  afterEach(() => {
    cleanup();
    window.matchMedia = originalMatchMedia;
  });

  describe('AC1, AC6: Rendering', () => {
    it('renders thumbs up/down buttons when feedbackEnabled is true', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          feedbackEnabled={true}
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByTestId('feedback-rating')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-up')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-down')).toBeInTheDocument();
    });

    it('renders "Was this helpful?" heading above buttons', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          feedbackEnabled={true}
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
    });

    it('renders "Yes" and "No" labels on buttons', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          feedbackEnabled={true}
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByText('Yes')).toBeInTheDocument();
      expect(screen.getByText('No')).toBeInTheDocument();
    });

    it('renders nothing when feedbackEnabled is false', () => {
      const { container } = render(
        <FeedbackRating
          messageId="msg-1"
          feedbackEnabled={false}
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders with default feedbackEnabled=true', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByTestId('feedback-rating')).toBeInTheDocument();
    });
  });

  describe('AC2: Clicking Sends Feedback', () => {
    it('shows comment form when thumbs down clicked', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));

      expect(screen.getByTestId('feedback-comment-form')).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('updates rating state (filled icon after selection)', async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      expect(thumbsUp).toHaveAttribute('aria-pressed', 'false');

      fireEvent.click(thumbsUp);

      await waitFor(() => {
        expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');
      });
    });
  });

  describe('AC3: Optional Text Feedback on Thumbs Down', () => {
    it('shows comment form when thumbs down is clicked', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));

      expect(screen.getByTestId('feedback-comment-form')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-comment')).toBeInTheDocument();
    });

    it('text input has max 500 characters', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));

      const textarea = screen.getByTestId('feedback-comment');
      expect(textarea).toHaveAttribute('maxLength', '500');
    });

    it('truncates input to 500 characters', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));

      const textarea = screen.getByTestId('feedback-comment');
      const longText = 'a'.repeat(600);
      fireEvent.change(textarea, { target: { value: longText } });

      expect(textarea).toHaveValue('a'.repeat(500));
    });

    it('submits rating with comment when submit button clicked', async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));

      const textarea = screen.getByTestId('feedback-comment');
      fireEvent.change(textarea, { target: { value: 'Not helpful enough' } });

      fireEvent.click(screen.getByText('Submit'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('msg-1', 'negative', 'Not helpful enough');
      });
    });

    it('dismisses form without submitting when Skip clicked', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-down'));
      expect(screen.getByTestId('feedback-comment-form')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Skip'));

      expect(screen.queryByTestId('feedback-comment-form')).not.toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('AC7: Accessibility', () => {
    it('has correct role and aria-label on container', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const container = screen.getByTestId('feedback-rating');
      expect(container).toHaveAttribute('role', 'group');
      expect(container).toHaveAttribute('aria-label', 'Rate this response');
    });

    it('has aria-label on thumbs up button', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      expect(thumbsUp).toHaveAttribute('aria-label', 'Rate as helpful');
      expect(thumbsUp).toHaveAttribute('role', 'button');
    });

    it('has aria-label on thumbs down button', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsDown = screen.getByTestId('feedback-down');
      expect(thumbsDown).toHaveAttribute('aria-label', 'Rate as not helpful');
      expect(thumbsDown).toHaveAttribute('role', 'button');
    });

    it('has aria-pressed state that changes on selection', async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      expect(thumbsUp).toHaveAttribute('aria-pressed', 'false');

      fireEvent.click(thumbsUp);

      await waitFor(() => {
        expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('has aria-live region for announcements', async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const container = screen.getByTestId('feedback-rating');
      const liveRegion = container.querySelector('[aria-live="polite"]');
      expect(liveRegion).toBeInTheDocument();
      expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
    });

    it('announces feedback submission', async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-up'));

      await waitFor(() => {
        const container = screen.getByTestId('feedback-rating');
        const liveRegion = container.querySelector('[aria-live="polite"]');
        expect(liveRegion).toHaveTextContent('Feedback submitted: Helpful');
      });
    });
  });

  describe('Touch Targets (WCAG 2.1 AA)', () => {
    it('has 44x44px minimum touch targets', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      const thumbsDown = screen.getByTestId('feedback-down');

      expect(thumbsUp).toHaveClass('feedback-button');
      expect(thumbsDown).toHaveClass('feedback-button');
      
      expect(thumbsUp.getAttribute('class')).toMatch(/feedback-button/);
      expect(thumbsDown.getAttribute('class')).toMatch(/feedback-button/);
    });
  });

  describe('Dark Mode', () => {
    it('applies dark mode class when theme mode is dark', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockDarkTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const container = screen.getByTestId('feedback-rating');
      expect(container).toHaveClass('feedback-rating--dark');
    });
  });

  describe('Reduced Motion', () => {
    it('respects prefers-reduced-motion', () => {
        window.matchMedia = vi.fn().mockImplementation((query: string) => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        }));

        render(
          <FeedbackRating
            messageId="msg-1"
            theme={mockTheme}
            onSubmit={mockOnSubmit}
          />
        );

        const thumbsUp = screen.getByTestId('feedback-up');
        expect(thumbsUp).toHaveClass('feedback-button');
    });
  });

  describe('User Rating State', () => {
    it('displays initial userRating if provided', () => {
      render(
        <FeedbackRating
          messageId="msg-1"
          userRating="positive"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');
    });

    it('updates when userRating prop changes', () => {
      const { rerender } = render(
        <FeedbackRating
          messageId="msg-1"
          userRating={undefined}
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      expect(thumbsUp).toHaveAttribute('aria-pressed', 'false');

      rerender(
        <FeedbackRating
          messageId="msg-1"
          userRating="positive"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Submitting State', () => {
    it('disables buttons while submitting', async () => {
      let resolveSubmit: () => void;
      mockOnSubmit.mockImplementation(() => new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      }));

      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      fireEvent.click(thumbsUp);

      expect(thumbsUp).toBeDisabled();

      resolveSubmit!();
      await waitFor(() => {
        expect(thumbsUp).not.toBeDisabled();
      });
    });

    it('shows cursor wait while submitting', async () => {
      let resolveSubmit: () => void;
      mockOnSubmit.mockImplementation(() => new Promise<void>((resolve) => {
        resolveSubmit = resolve;
      }));

      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      const thumbsUp = screen.getByTestId('feedback-up');
      fireEvent.click(thumbsUp);

      expect(thumbsUp).toBeDisabled();

      resolveSubmit!();
    });
  });

  describe('Error Handling', () => {
    it('announces error when submission fails', async () => {
      mockOnSubmit.mockRejectedValue(new Error('Network error'));
      
      vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <FeedbackRating
          messageId="msg-1"
          theme={mockTheme}
          onSubmit={mockOnSubmit}
        />
      );

      fireEvent.click(screen.getByTestId('feedback-up'));

      await waitFor(() => {
        const container = screen.getByTestId('feedback-rating');
        const liveRegion = container.querySelector('[aria-live="polite"]');
        expect(liveRegion).toHaveTextContent('Failed to submit feedback');
      });
    });
  });
});
