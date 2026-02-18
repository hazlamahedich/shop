import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MessageList } from './MessageList';
import type { WidgetTheme, WidgetMessage } from '../types/widget';

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

const mockMessages: WidgetMessage[] = [
  {
    messageId: '1',
    content: 'Bot message',
    sender: 'bot',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    messageId: '2',
    content: 'User message',
    sender: 'user',
    createdAt: '2024-01-01T00:00:01Z',
  },
];

describe('MessageList', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('should display welcome message when empty', () => {
    render(
      <MessageList
        messages={[]}
        botName="TestBot"
        welcomeMessage="Welcome!"
        theme={mockTheme}
      />
    );
    expect(screen.getByText('Welcome!')).toBeDefined();
  });

  it('should display default message when empty without welcomeMessage', () => {
    render(
      <MessageList
        messages={[]}
        botName="TestBot"
        theme={mockTheme}
      />
    );
    expect(screen.getByText('Start a conversation')).toBeDefined();
  });

  it('should display messages', () => {
    render(
      <MessageList
        messages={mockMessages}
        botName="TestBot"
        theme={mockTheme}
      />
    );
    expect(screen.getByText('Bot message')).toBeDefined();
    expect(screen.getByText('User message')).toBeDefined();
  });

  it('should have role="log"', () => {
    render(
      <MessageList
        messages={mockMessages}
        botName="TestBot"
        theme={mockTheme}
      />
    );
    expect(screen.getByRole('log')).toBeDefined();
  });

  it('should have aria-live="polite"', () => {
    render(
      <MessageList
        messages={mockMessages}
        botName="TestBot"
        theme={mockTheme}
      />
    );
    const log = screen.getByRole('log');
    expect(log.getAttribute('aria-live')).toBe('polite');
  });

  it('should display bot name for bot messages', () => {
    render(
      <MessageList
        messages={mockMessages}
        botName="TestBot"
        theme={mockTheme}
      />
    );
    expect(screen.getByText('TestBot')).toBeDefined();
  });
});
