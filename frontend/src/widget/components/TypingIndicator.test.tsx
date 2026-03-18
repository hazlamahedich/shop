import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { TypingIndicator } from './TypingIndicator';
import type { WidgetTheme } from '../types/widget';

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

describe('TypingIndicator', () => {
  const originalMatchMedia = window.matchMedia;
  
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
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
    vi.unstubAllGlobals();
    window.matchMedia = originalMatchMedia;
  });

  it('should not render when not visible', () => {
    render(
      <TypingIndicator isVisible={false} botName="TestBot" theme={mockTheme} />
    );
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('should render when visible', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    expect(screen.getByRole('status')).toBeDefined();
  });

  it('should have aria-live="polite"', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const indicator = screen.getByRole('status');
    expect(indicator.getAttribute('aria-live')).toBe('polite');
  });

  it('should announce bot is typing', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    expect(screen.getByLabelText(/TestBot is typing/i)).toBeDefined();
  });

  it('should display bot name', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    expect(screen.getByText('TestBot')).toBeDefined();
  });

  it('should render bouncing dots container', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dotsContainer = screen.getByTestId('typing-dots');
    expect(dotsContainer).toBeDefined();
  });

  it('should render 3 bouncing dots', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dots = screen.getAllByTestId('typing-dot');
    expect(dots).toHaveLength(3);
  });

  it('should apply staggered animation delays (0ms, 150ms, 300ms)', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dots = screen.getAllByTestId('typing-dot');
    
    expect(dots[0].style.animationDelay).toBe('0ms');
    expect(dots[1].style.animationDelay).toBe('150ms');
    expect(dots[2].style.animationDelay).toBe('300ms');
  });

  it('should apply animation with 1.4s duration', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dots = screen.getAllByTestId('typing-dot');
    dots.forEach(dot => {
      expect(dot.style.animationDuration).toBe('1.4s');
    });
  });

  it('should use theme primaryColor for dots', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dots = screen.getAllByTestId('typing-dot');
    // Browser converts hex to rgb, so check if backgroundColor contains the color
    dots.forEach(dot => {
      expect(dot.style.backgroundColor).toMatch(/rgb\(99,\s*102,\s*241\)|#6366f1/);
    });
  });

  it('should set dots to 8px circles', () => {
    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    const dots = screen.getAllByTestId('typing-dot');
    dots.forEach(dot => {
      expect(dot.style.width).toBe('8px');
      expect(dot.style.height).toBe('8px');
      expect(dot.style.borderRadius).toBe('50%');
    });
  });

  it('should respect prefers-reduced-motion', () => {
    // Mock prefers-reduced-motion
    const mockMatchMedia = vi.fn().mockImplementation((query) => ({
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

    render(
      <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
    );
    
    const dots = screen.getAllByTestId('typing-dot');
    dots.forEach(dot => {
      // Animation should be empty when reduced motion is preferred
      expect(dot.style.animation).toBe('');
    });
  });

  describe('AC11: GPU Acceleration', () => {
    it('should use typing-dot-bounce animation name', () => {
      render(
        <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
      );
      const dots = screen.getAllByTestId('typing-dot');
      dots.forEach(dot => {
        expect(dot.style.animationName).toBe('typing-dot-bounce');
      });
    });

    it('should use ease-in-out timing function', () => {
      render(
        <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
      );
      const dots = screen.getAllByTestId('typing-dot');
      dots.forEach(dot => {
        expect(dot.style.animationTimingFunction).toBe('ease-in-out');
      });
    });

    it('should animate infinitely', () => {
      render(
        <TypingIndicator isVisible={true} botName="TestBot" theme={mockTheme} />
      );
      const dots = screen.getAllByTestId('typing-dot');
      dots.forEach(dot => {
        expect(dot.style.animationIterationCount).toBe('infinite');
      });
    });
  });
});
