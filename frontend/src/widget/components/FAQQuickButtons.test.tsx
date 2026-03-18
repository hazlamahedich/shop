import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { FAQQuickButtons } from './FAQQuickButtons';
import type { FAQQuickButton, WidgetTheme } from '../types/widget';

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

const createMockFaqButtons = (count: number): FAQQuickButton[] =>
  Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    question: `FAQ Question ${i + 1}?`,
    icon: i % 2 === 0 ? '❓' : undefined,
  }));

describe('FAQQuickButtons', () => {
  const originalMatchMedia = window.matchMedia;
  
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
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

  describe('AC1: FAQ Buttons Appear on Initial Load', () => {
    it('renders buttons when provided', () => {
      const buttons = createMockFaqButtons(3);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      expect(screen.getByText('FAQ Question 1?')).toBeInTheDocument();
      expect(screen.getByText('FAQ Question 2?')).toBeInTheDocument();
      expect(screen.getByText('FAQ Question 3?')).toBeInTheDocument();
    });

    it('returns null when buttons array is empty', () => {
      const { container } = render(
        <FAQQuickButtons
          buttons={[]}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('AC2: Top 5 FAQs by Configured Priority', () => {
    it('renders all buttons passed (truncation handled by API)', () => {
      const buttons = createMockFaqButtons(10);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      expect(screen.getAllByRole('button')).toHaveLength(10);
    });

    it('renders buttons in provided order (sorting handled by API)', () => {
      const buttons: FAQQuickButton[] = [
        { id: 3, question: 'Third Question?' },
        { id: 1, question: 'First Question?' },
        { id: 2, question: 'Second Question?' },
      ];
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const renderedButtons = screen.getAllByRole('button');
      expect(renderedButtons[0]).toHaveTextContent('Third Question?');
      expect(renderedButtons[1]).toHaveTextContent('First Question?');
      expect(renderedButtons[2]).toHaveTextContent('Second Question?');
    });

    it('renders chip-style buttons with correct classes', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btns = screen.getAllByRole('button');
      btns.forEach(button => {
        expect(button).toHaveClass('faq-quick-button');
      });
    });

    it('renders icons/emojis before text', () => {
      const buttons: FAQQuickButton[] = [
        { id: 1, question: 'What are your hours?', icon: '🕐' },
        { id: 2, question: 'How do I contact support?', icon: '📞' },
      ];
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn1 = screen.getByTestId('faq-quick-button-1');
      expect(btn1).toHaveTextContent('🕐');
      expect(btn1).toHaveTextContent('What are your hours?');

      const btn2 = screen.getByTestId('faq-quick-button-2');
      expect(btn2).toHaveTextContent('📞');
      expect(btn2).toHaveTextContent('How do I contact support?');
    });

    it('renders buttons without icons when icon is undefined', () => {
      const buttons: FAQQuickButton[] = [
        { id: 1, question: 'Question without icon' },
      ];
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      expect(btn).toHaveTextContent('Question without icon');
      expect(btn.querySelector('.faq-quick-button-icon')).toBeNull();
    });
  });

  describe('AC3: Clicking Button Sends FAQ Question', () => {
    it('calls onButtonClick with correct button on click', () => {
      const buttons = createMockFaqButtons(2);
      const onButtonClick = vi.fn();
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={onButtonClick}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      expect(onButtonClick).toHaveBeenCalledWith(buttons[0]);
      expect(onButtonClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('AC6: Responsive Layout', () => {
    it('has 44x44px minimum touch targets', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btns = screen.getAllByRole('button');
      btns.forEach(button => {
        expect(button.style.minHeight).toBe('44px');
        expect(button.style.minWidth).toBe('44px');
      });
    });

    it('renders flex wrap layout', () => {
      const buttons = createMockFaqButtons(5);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const container = screen.getByTestId('faq-quick-buttons');
      expect(container.style.display).toBe('flex');
      expect(container.style.flexWrap).toBe('wrap');
    });
  });

  describe('AC7: Keyboard Navigation', () => {
    it('supports keyboard navigation - Enter key', () => {
      const buttons = createMockFaqButtons(2);
      const onButtonClick = vi.fn();
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={onButtonClick}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.keyDown(btn, { key: 'Enter' });

      expect(onButtonClick).toHaveBeenCalledWith(buttons[0]);
    });

    it('supports keyboard navigation - Space key', () => {
      const buttons = createMockFaqButtons(2);
      const onButtonClick = vi.fn();
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={onButtonClick}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-2');
      fireEvent.keyDown(btn, { key: ' ' });

      expect(onButtonClick).toHaveBeenCalledWith(buttons[1]);
    });

    it('has visible focus indicator via role attribute', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      expect(btn).toHaveAttribute('role', 'button');
    });

    it('has tabIndex=0 for keyboard navigation', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btns = screen.getAllByRole('button');
      btns.forEach(button => {
        expect(button).toHaveAttribute('tabIndex', '0');
      });
    });
  });

  describe('Accessibility', () => {
    it('has accessibility attributes', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const container = screen.getByTestId('faq-quick-buttons');
      expect(container).toHaveAttribute('role', 'group');
      expect(container).toHaveAttribute('aria-label', 'FAQ quick buttons');

      const btns = screen.getAllByRole('button');
      btns.forEach((button, index) => {
        expect(button).toHaveAttribute('aria-label', buttons[index].question);
      });
    });

    it('has data-testid attributes', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      expect(screen.getByTestId('faq-quick-buttons')).toBeInTheDocument();
      expect(screen.getByTestId('faq-quick-button-1')).toBeInTheDocument();
      expect(screen.getByTestId('faq-quick-button-2')).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables buttons when disabled prop is true', () => {
      const buttons = createMockFaqButtons(2);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
          disabled={true}
        />
      );

      const btns = screen.getAllByRole('button');
      btns.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    it('does not call onButtonClick when disabled', () => {
      const buttons = createMockFaqButtons(2);
      const onButtonClick = vi.fn();
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={onButtonClick}
          theme={mockTheme}
          disabled={true}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      expect(onButtonClick).not.toHaveBeenCalled();
    });

    it('shows not-allowed cursor when disabled', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
          disabled={true}
        />
      );

      const btn = screen.getByRole('button');
      expect(btn.style.cursor).toBe('not-allowed');
    });
  });

  describe('Theme Integration', () => {
    it('uses theme primary color for border', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByRole('button');
      // Browser converts hex to rgb
      expect(btn.style.border).toContain('99, 102, 241');
    });

    it('uses theme text color', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByRole('button');
      // Browser converts hex to rgb
      expect(btn.style.color).toContain('30, 41, 59');
    });
  });

  describe('Ripple Effect', () => {
    it('should show ripple effect on button click', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple).toBeDefined();
    });

    it('should apply ripple animation with 600ms duration', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.animationDuration).toBe('600ms');
    });

    it('should use transform for ripple (GPU-accelerated)', () => {
      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.transform).toContain('translate');
    });
  });

  describe('Reduced Motion', () => {
    it('should disable animations with reduced motion preference', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));
      window.matchMedia = mockMatchMedia;

      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByRole('button');
      expect(btn.style.transition).toBe('none');
    });

    it('should disable ripple animation with reduced motion', () => {
      const mockMatchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));
      window.matchMedia = mockMatchMedia;

      const buttons = createMockFaqButtons(1);
      render(
        <FAQQuickButtons
          buttons={buttons}
          onButtonClick={vi.fn()}
          theme={mockTheme}
        />
      );

      const btn = screen.getByTestId('faq-quick-button-1');
      fireEvent.click(btn);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.animationName).toBe('none');
      expect(ripple.style.animationDuration).toBe('0ms');
    });
  });
});
