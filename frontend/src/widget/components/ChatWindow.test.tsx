import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/react';
import { ChatWindow } from './ChatWindow';
import type { WidgetTheme, WidgetMessage, WidgetConfig } from '../types/widget';

vi.mock('focus-trap-react', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

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

const mockConfig: WidgetConfig = {
  enabled: true,
  botName: 'TestBot',
  welcomeMessage: 'Hello!',
  theme: mockTheme,
  allowedDomains: [],
};

const mockMessages: WidgetMessage[] = [
  {
    messageId: '1',
    content: 'Hello!',
    sender: 'bot',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    messageId: '2',
    content: 'Hi there!',
    sender: 'user',
    createdAt: '2024-01-01T00:00:01Z',
  },
];

describe('ChatWindow', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('should not render when closed', () => {
    render(
      <ChatWindow
        isOpen={false}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('should render when open', () => {
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    expect(screen.getByRole('dialog')).toBeDefined();
  });

  it('should display bot name in header', () => {
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    expect(screen.getByText('TestBot')).toBeDefined();
  });

  it('should call onClose when close button clicked', () => {
    const handleClose = vi.fn();
    render(
      <ChatWindow
        isOpen={true}
        onClose={handleClose}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    fireEvent.click(screen.getByLabelText(/close chat window/i));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should display messages', () => {
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={mockMessages}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    expect(screen.getByText('Hello!')).toBeDefined();
    expect(screen.getByText('Hi there!')).toBeDefined();
  });

  it('should display error when present', () => {
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error="Test error"
      />
    );
    expect(screen.getByRole('alert')).toBeDefined();
    expect(screen.getByText('Test error')).toBeDefined();
  });

  it('should have aria-modal attribute', () => {
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={vi.fn()}
        error={null}
      />
    );
    expect(screen.getByRole('dialog').getAttribute('aria-modal')).toBe('true');
  });

  it('should send message on form submit', async () => {
    const handleSend = vi.fn().mockResolvedValue(undefined);
    render(
      <ChatWindow
        isOpen={true}
        onClose={vi.fn()}
        theme={mockTheme}
        config={mockConfig}
        messages={[]}
        isTyping={false}
        onSendMessage={handleSend}
        error={null}
      />
    );
    const input = screen.getByLabelText(/type a message/i);
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByLabelText(/send message/i));
    await waitFor(() => {
      expect(handleSend).toHaveBeenCalledWith('Test message');
    });
  });
});
