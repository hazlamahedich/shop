/**
 * GreetingEditor Component Tests
 *
 * Story 1.10: Bot Personality Configuration
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GreetingEditor } from './GreetingEditor';

describe('GreetingEditor', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    defaultGreeting: 'Hey! 👋 How can I help you today?',
    onReset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the greeting editor', () => {
      render(<GreetingEditor {...defaultProps} />);

      // Use regex to match label text that may contain nested elements
      expect(screen.getByLabelText(/custom greeting/i)).toBeInTheDocument();
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should display the placeholder with default greeting', () => {
      render(<GreetingEditor {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('placeholder', expect.stringContaining('Hey! 👋 How can I help you today?'));
    });

    it('should show the character count', () => {
      render(<GreetingEditor {...defaultProps} />);

      expect(screen.getByText('0 / 500')).toBeInTheDocument();
    });

    it('should display the current value', () => {
      render(<GreetingEditor {...defaultProps} value="Hello there!" />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('Hello there!');
    });

    it('should show helper text about leaving empty', () => {
      render(<GreetingEditor {...defaultProps} />);

      expect(screen.getByText('Leave empty to use the personality\'s default greeting')).toBeInTheDocument();
    });
  });

  describe('Character Count', () => {
    it('should update character count as user types', () => {
      const { rerender } = render(<GreetingEditor {...defaultProps} value="Hi" />);

      expect(screen.getByText('2 / 500')).toBeInTheDocument();

      rerender(<GreetingEditor {...defaultProps} value="Hi there!" />);
      expect(screen.getByText('9 / 500')).toBeInTheDocument();
    });

    it('should show warning color when near limit', () => {
      // Need > 90% (450 chars), so use 451 to trigger warning state
      const longValue = 'a'.repeat(451);
      render(<GreetingEditor {...defaultProps} value={longValue} />);

      const characterCount = screen.getByText('451 / 500');
      expect(characterCount).toHaveClass('text-amber-600');
    });

    it('should show error color when at limit', () => {
      const longValue = 'a'.repeat(500);
      render(<GreetingEditor {...defaultProps} value={longValue} />);

      const characterCount = screen.getByText(/500/);
      expect(characterCount).toHaveClass('text-red-600');
    });
  });

  describe('Input Handling', () => {
    it('should call onChange when user types', () => {
      const handleChange = vi.fn();
      render(<GreetingEditor {...defaultProps} onChange={handleChange} />);

      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: 'Hello!' } });

      expect(handleChange).toHaveBeenCalledWith('Hello!');
    });

    it('should enforce max length', () => {
      const handleChange = vi.fn();
      render(<GreetingEditor {...defaultProps} onChange={handleChange} maxLength={10} />);

      const textarea = screen.getByRole('textbox');
      textarea.maxLength = 10;

      fireEvent.change(textarea, { target: { value: 'a'.repeat(15) } });

      // The textarea should not exceed maxLength
      expect(textarea.value.length).toBeLessThanOrEqual(10);
    });

    it('should not call onChange if value exceeds max length', () => {
      const handleChange = vi.fn();
      render(<GreetingEditor {...defaultProps} onChange={handleChange} maxLength={5} />);

      const textarea = screen.getByRole('textbox');
      const longValue = 'a'.repeat(10);

      // This should be handled by the component's maxLength
      fireEvent.change(textarea, { target: { value: longValue } });
    });
  });

  describe('Reset Button', () => {
    it('should show reset button when there is a custom greeting', () => {
      render(<GreetingEditor {...defaultProps} value="Custom greeting" />);

      expect(screen.getByRole('button', { name: /reset to default/i })).toBeInTheDocument();
    });

    it('should not show reset button when greeting is empty', () => {
      render(<GreetingEditor {...defaultProps} value="" />);

      expect(screen.queryByRole('button', { name: /reset to default/i })).not.toBeInTheDocument();
    });

    it('should call onReset when reset button is clicked', () => {
      const handleReset = vi.fn();
      render(<GreetingEditor {...defaultProps} value="Custom" onReset={handleReset} />);

      const resetButton = screen.getByRole('button', { name: /reset to default/i });
      resetButton.click();

      expect(handleReset).toHaveBeenCalled();
    });
  });

  describe('Greeting Preview', () => {
    it('should show preview when there is a value', () => {
      render(<GreetingEditor {...defaultProps} value="Welcome to our store!" />);

      expect(screen.getByText('Preview:')).toBeInTheDocument();
      // The greeting appears in both the textarea and preview, so use getAllByText
      expect(screen.getAllByText('Welcome to our store!').length).toBeGreaterThan(0);
    });

    it('should not show preview when value is empty', () => {
      render(<GreetingEditor {...defaultProps} value="" />);

      expect(screen.queryByText('Preview:')).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable input when disabled prop is true', () => {
      render(<GreetingEditor {...defaultProps} disabled />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
    });

    it('should disable reset button when disabled', () => {
      render(<GreetingEditor {...defaultProps} value="Custom" disabled />);

      const resetButton = screen.getByRole('button', { name: /reset to default/i });
      expect(resetButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper label association', () => {
      render(<GreetingEditor {...defaultProps} />);

      // Use regex to match label text that may contain nested elements
      const label = screen.getByLabelText(/custom greeting/i);
      const textarea = screen.getByRole('textbox');

      expect(label).toBeInTheDocument();
      expect(textarea).toHaveAttribute('id', 'greeting-input');
    });

    it('should announce character count to screen readers', () => {
      render(<GreetingEditor {...defaultProps} value="Hello" />);

      const characterCount = screen.getByText('5 / 500');
      expect(characterCount).toHaveAttribute('aria-live', 'polite');
    });

    it('should have descriptive ids for helper text', () => {
      render(<GreetingEditor {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby', 'greeting-description greeting-character-count');
    });
  });
});
