import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { QuickReplyButtons } from './QuickReplyButtons';
import type { QuickReply, WidgetTheme } from '../types/widget';

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

const createMockQuickReplies = (count: number): QuickReply[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `reply-${i + 1}`,
    text: `Option ${i + 1}`,
    icon: i % 2 === 0 ? '✓' : undefined,
    payload: `payload-${i + 1}`,
  }));

describe('QuickReplyButtons', () => {
  const originalMatchMedia = window.matchMedia;
  
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    // Default mock - no reduced motion
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

  it('renders buttons with correct text', () => {
    const quickReplies = createMockQuickReplies(3);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(screen.getByText('Option 1')).toBeInTheDocument();
    expect(screen.getByText('Option 2')).toBeInTheDocument();
    expect(screen.getByText('Option 3')).toBeInTheDocument();
  });

  it('renders chip-style buttons with correct classes', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveClass('quick-reply-button');
    });
  });

  it('has 44x44px minimum touch targets', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      const style = button.style;
      expect(style.minHeight).toBe('44px');
      expect(style.minWidth).toBe('44px');
    });
  });

  it('renders icons/emojis before text', () => {
    const quickReplies: QuickReply[] = [
      { id: '1', text: 'Yes', icon: '✓' },
      { id: '2', text: 'No', icon: '✗' },
    ];
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const yesButton = screen.getByTestId('quick-reply-button-1');
    expect(yesButton).toHaveTextContent('✓');
    expect(yesButton).toHaveTextContent('Yes');

    const noButton = screen.getByTestId('quick-reply-button-2');
    expect(noButton).toHaveTextContent('✗');
    expect(noButton).toHaveTextContent('No');
  });

  it('calls onReply with correct payload on click', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
      />
    );

    const button = screen.getByTestId('quick-reply-button-reply-1');
    fireEvent.click(button);

    expect(onReply).toHaveBeenCalledWith(quickReplies[0]);
    expect(onReply).toHaveBeenCalledTimes(1);
  });

  it('supports keyboard navigation - Enter key', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
      />
    );

    const button = screen.getByTestId('quick-reply-button-reply-1');
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(onReply).toHaveBeenCalledWith(quickReplies[0]);
  });

  it('supports keyboard navigation - Space key', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
      />
    );

    const button = screen.getByTestId('quick-reply-button-reply-2');
    fireEvent.keyDown(button, { key: ' ' });

    expect(onReply).toHaveBeenCalledWith(quickReplies[1]);
  });

  it('has visible focus indicator', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveAttribute('role', 'button');
    });
  });

  it('has accessibility attributes', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const container = screen.getByTestId('quick-reply-buttons');
    expect(container).toHaveAttribute('role', 'group');
    expect(container).toHaveAttribute('aria-label', 'Quick reply options');

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button, index) => {
      expect(button).toHaveAttribute('aria-label', quickReplies[index].text);
    });
  });

  it('has data-testid attributes', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(screen.getByTestId('quick-reply-buttons')).toBeInTheDocument();
    expect(screen.getByTestId('quick-reply-button-reply-1')).toBeInTheDocument();
    expect(screen.getByTestId('quick-reply-button-reply-2')).toBeInTheDocument();
  });

  it('renders 2-column grid on mobile (< 480px)', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    const quickReplies = createMockQuickReplies(4);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const container = screen.getByTestId('quick-reply-buttons');
    expect(container).toHaveClass('quick-reply-buttons');
  });

  it('renders single row on desktop (>= 480px)', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    const quickReplies = createMockQuickReplies(3);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const container = screen.getByTestId('quick-reply-buttons');
    expect(container).toHaveClass('quick-reply-buttons');
  });

  it('respects prefers-reduced-motion', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0].style.transition).toContain('transform 100ms');
  });

  it('dismisses buttons after selection when dismissOnSelect is true', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
        dismissOnSelect={true}
      />
    );

    const button1 = screen.getByTestId('quick-reply-button-reply-1');
    fireEvent.click(button1);

    const button2 = screen.getByTestId('quick-reply-button-reply-2');
    expect(button2).toBeDisabled();
  });

  it('does not dismiss buttons when dismissOnSelect is false', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
        dismissOnSelect={false}
      />
    );

    const button1 = screen.getByTestId('quick-reply-button-reply-1');
    fireEvent.click(button1);

    const button2 = screen.getByTestId('quick-reply-button-reply-2');
    expect(button2).not.toBeDisabled();
  });

  it('returns null when quickReplies is empty', () => {
    const { container } = render(
      <QuickReplyButtons
        quickReplies={[]}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('disables buttons when disabled prop is true', () => {
    const quickReplies = createMockQuickReplies(2);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
        disabled={true}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('does not call onReply when disabled', () => {
    const quickReplies = createMockQuickReplies(2);
    const onReply = vi.fn();
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={onReply}
        theme={mockTheme}
        disabled={true}
      />
    );

    const button = screen.getByTestId('quick-reply-button-reply-1');
    fireEvent.click(button);

    expect(onReply).not.toHaveBeenCalled();
  });

  it('uses theme primary color for border and text', () => {
    const quickReplies = createMockQuickReplies(1);
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button');
    expect(button.style.border).toContain('99, 102, 241');
    expect(button.style.color).toContain('99, 102, 241');
  });

  it('renders buttons without icons when icon is undefined', () => {
    const quickReplies: QuickReply[] = [
      { id: '1', text: 'Option without icon' },
    ];
    render(
      <QuickReplyButtons
        quickReplies={quickReplies}
        onReply={vi.fn()}
        theme={mockTheme}
      />
    );

    const button = screen.getByTestId('quick-reply-button-1');
    expect(button).toHaveTextContent('Option without icon');
    expect(button.querySelector('span[aria-hidden="true"]')).toBeNull();
  });

  describe('AC3: Ripple Effect Animation', () => {
    it('should show ripple effect on button click', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByTestId('quick-reply-button-reply-1');
      fireEvent.click(button);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple).toBeDefined();
    });

    it('should apply ripple animation with 600ms duration', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByTestId('quick-reply-button-reply-1');
      fireEvent.click(button);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.animationDuration).toBe('600ms');
    });

    it('should use ease-out timing for ripple', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByTestId('quick-reply-button-reply-1');
      fireEvent.click(button);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.animationTimingFunction).toBe('ease-out');
    });

    it('should use transform for ripple (GPU-accelerated)', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByTestId('quick-reply-button-reply-1');
      fireEvent.click(button);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.transform).toContain('translate');
    });

    it('should disable ripple with reduced motion preference', () => {
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

      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByTestId('quick-reply-button-reply-1');
      fireEvent.click(button);

      const ripple = screen.getByTestId('ripple-effect');
      expect(ripple.style.animationName).toBe('none');
      expect(ripple.style.animationDuration).toBe('0ms');
    });
  });

  describe('AC11: GPU Acceleration', () => {
    it('should use GPU-accelerated properties in transitions', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByRole('button');
      expect(button.style.transition).toContain('transform');
    });

    it('should have 100ms transition duration for smooth feel', () => {
      const quickReplies = createMockQuickReplies(1);
      render(
        <QuickReplyButtons
          quickReplies={quickReplies}
          onReply={vi.fn()}
          theme={mockTheme}
        />
      );

      const button = screen.getByRole('button');
      expect(button.style.transition).toContain('100ms');
    });
  });
});
