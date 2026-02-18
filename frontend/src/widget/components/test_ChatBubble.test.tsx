import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { ChatBubble } from './ChatBubble';
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

describe('ChatBubble', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('should render floating button', () => {
    render(<ChatBubble isOpen={false} onClick={vi.fn()} theme={mockTheme} />);
    expect(screen.getByRole('button', { name: /open chat/i })).toBeDefined();
  });

  it('should display close label when open', () => {
    render(<ChatBubble isOpen={true} onClick={vi.fn()} theme={mockTheme} />);
    expect(screen.getByRole('button', { name: /close chat/i })).toBeDefined();
  });

  it('should call onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<ChatBubble isOpen={false} onClick={handleClick} theme={mockTheme} />);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should respond to Enter key', () => {
    const handleClick = vi.fn();
    render(<ChatBubble isOpen={false} onClick={handleClick} theme={mockTheme} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should respond to Space key', () => {
    const handleClick = vi.fn();
    render(<ChatBubble isOpen={false} onClick={handleClick} theme={mockTheme} />);
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should apply bottom-right position by default', () => {
    render(<ChatBubble isOpen={false} onClick={vi.fn()} theme={mockTheme} />);
    const button = screen.getByRole('button');
    expect(button.style.right).toBe('20px');
  });

  it('should apply bottom-left position when specified', () => {
    const leftTheme = { ...mockTheme, position: 'bottom-left' as const };
    render(<ChatBubble isOpen={false} onClick={vi.fn()} theme={leftTheme} />);
    const button = screen.getByRole('button');
    expect(button.style.left).toBe('20px');
  });

  it('should apply primary color as background', () => {
    render(<ChatBubble isOpen={false} onClick={vi.fn()} theme={mockTheme} />);
    const button = screen.getByRole('button');
    expect(button.style.backgroundColor).toMatch(/6366f1|rgb\(99, 102, 241\)/);
  });

  it('should have aria-expanded attribute', () => {
    render(<ChatBubble isOpen={true} onClick={vi.fn()} theme={mockTheme} />);
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-expanded')).toBe('true');
  });
});
