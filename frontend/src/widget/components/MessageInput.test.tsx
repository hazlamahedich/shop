import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { MessageInput } from './MessageInput';
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

describe('MessageInput', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('should render input and send button', () => {
    render(
      <MessageInput
        value=""
        onChange={vi.fn()}
        onSend={vi.fn()}
        disabled={false}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    expect(screen.getByLabelText(/type a message/i)).toBeDefined();
    expect(screen.getByLabelText(/send message/i)).toBeDefined();
  });

  it('should call onChange when input changes', () => {
    const handleChange = vi.fn();
    render(
      <MessageInput
        value=""
        onChange={handleChange}
        onSend={vi.fn()}
        disabled={false}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    fireEvent.change(screen.getByLabelText(/type a message/i), {
      target: { value: 'Hello' },
    });
    expect(handleChange).toHaveBeenCalledWith('Hello');
  });

  it('should call onSend when form submitted', () => {
    const handleSend = vi.fn();
    render(
      <MessageInput
        value="Test"
        onChange={vi.fn()}
        onSend={handleSend}
        disabled={false}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    fireEvent.click(screen.getByLabelText(/send message/i));
    expect(handleSend).toHaveBeenCalledTimes(1);
  });

  it('should call onSend on Enter key', () => {
    const handleSend = vi.fn();
    render(
      <MessageInput
        value="Test"
        onChange={vi.fn()}
        onSend={handleSend}
        disabled={false}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    fireEvent.keyDown(screen.getByLabelText(/type a message/i), { key: 'Enter' });
    expect(handleSend).toHaveBeenCalledTimes(1);
  });

  it('should disable button when input is empty', () => {
    render(
      <MessageInput
        value=""
        onChange={vi.fn()}
        onSend={vi.fn()}
        disabled={false}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    expect(screen.getByLabelText(/send message/i)).toBeDisabled();
  });

  it('should disable button when disabled prop is true', () => {
    render(
      <MessageInput
        value="Test"
        onChange={vi.fn()}
        onSend={vi.fn()}
        disabled={true}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    expect(screen.getByLabelText(/send message/i)).toBeDisabled();
  });

  it('should disable input when disabled prop is true', () => {
    render(
      <MessageInput
        value=""
        onChange={vi.fn()}
        onSend={vi.fn()}
        disabled={true}
        placeholder="Type a message"
        theme={mockTheme}
      />
    );
    expect(screen.getByLabelText(/type a message/i)).toBeDisabled();
  });
});
