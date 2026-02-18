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
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
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
});
