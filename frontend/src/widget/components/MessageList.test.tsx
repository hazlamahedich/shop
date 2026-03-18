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
    const senderLabels = screen.getAllByText('TestBot');
    expect(senderLabels.length).toBeGreaterThan(0);
  });

  describe('Message Grouping', () => {
    it('should group consecutive bot messages', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:01Z' },
        { messageId: '3', content: 'Bot 3', sender: 'bot', createdAt: '2024-01-01T00:00:02Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const groups = screen.getAllByTestId('message-group');
      expect(groups).toHaveLength(1);
      
      const bubbles = screen.getAllByTestId('message-bubble');
      expect(bubbles).toHaveLength(3);
    });

    it('should create separate groups for different senders', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'User 1', sender: 'user', createdAt: '2024-01-01T00:00:01Z' },
        { messageId: '3', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:02Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const groups = screen.getAllByTestId('message-group');
      expect(groups).toHaveLength(3);
    });

    it('should show timestamp only on last message in group', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:01Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const timestamps = screen.getAllByTestId('message-timestamp');
      expect(timestamps).toHaveLength(1);
    });

    it('should show avatar only on first bot message in group', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:01Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const avatars = screen.getAllByTestId('message-avatar');
      expect(avatars).toHaveLength(1);
    });

    it('should NOT show avatar for user messages', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'User 1', sender: 'user', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'User 2', sender: 'user', createdAt: '2024-01-01T00:00:01Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      expect(screen.queryByTestId('message-avatar')).toBeNull();
    });

    it('should NOT show avatar for system messages', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'System message', sender: 'system', createdAt: '2024-01-01T00:00:00Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      expect(screen.queryByTestId('message-avatar')).toBeNull();
    });

    it('should keep system messages as standalone (never grouped)', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'System', sender: 'system', createdAt: '2024-01-01T00:00:01Z' },
        { messageId: '3', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:02Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const groups = screen.getAllByTestId('message-group');
      expect(groups).toHaveLength(3);
    });

    it('should show relative time format', () => {
      const now = new Date();
      const fiveMinAgo = new Date(now.getTime() - 5 * 60 * 1000).toISOString();
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot', sender: 'bot', createdAt: fiveMinAgo },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const relativeTime = screen.getByTestId('relative-time');
      expect(relativeTime.textContent).toMatch(/5m ago/);
    });

    it('should have hover title for absolute timestamp', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot', sender: 'bot', createdAt: '2024-01-01T12:00:00Z' },
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      const timestamp = screen.getByTestId('message-timestamp');
      expect(timestamp).toHaveAttribute('title');
    });

    it('should render quick replies only on last message in group', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z', quick_replies: [{ id: '1', text: 'Yes' }] },
        { messageId: '2', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:01Z' },
      ];
      
      const onQuickRepliesAvailable = vi.fn();
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
          onQuickRepliesAvailable={onQuickRepliesAvailable}
        />
      );
      
      expect(onQuickRepliesAvailable).not.toHaveBeenCalled();
    });

    it('should render products only on last message in group', () => {
      const messages: WidgetMessage[] = [
        { messageId: '1', content: 'Bot 1', sender: 'bot', createdAt: '2024-01-01T00:00:00Z' },
        { messageId: '2', content: 'Bot 2', sender: 'bot', createdAt: '2024-01-01T00:00:01Z', products: [
          { id: 'p1', variantId: 'v1', title: 'Product', price: 10, available: true }
        ]},
      ];
      render(
        <MessageList
          messages={messages}
          botName="TestBot"
          theme={mockTheme}
        />
      );
      
      expect(screen.getByText('Product')).toBeDefined();
    });
  });
});
