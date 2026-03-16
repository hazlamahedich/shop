import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageAvatar } from './MessageAvatar';
import type { WidgetTheme } from '../types/widget';

const defaultTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'system-ui',
  fontSize: 14,
};

describe('MessageAvatar', () => {
  it('renders with correct initials from botName', () => {
    render(<MessageAvatar sender="bot" botName="ShopBot" theme={defaultTheme} />);
    expect(screen.getByText('SH')).toBeInTheDocument();
  });

  it('renders with correct initials for merchant sender', () => {
    render(<MessageAvatar sender="merchant" botName="ShopBot" theme={defaultTheme} />);
    expect(screen.getByText('ME')).toBeInTheDocument();
  });

  it('uses theme primaryColor for background', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.backgroundColor).toBe('rgb(99, 102, 241)');
  });

  it('has correct accessibility attributes', () => {
    render(<MessageAvatar sender="bot" botName="ShopBot" theme={defaultTheme} />);
    const avatar = screen.getByTestId('message-avatar');
    
    expect(avatar).toHaveAttribute('aria-label', 'ShopBot avatar');
    expect(avatar).toHaveAttribute('role', 'img');
  });

  it('has correct accessibility label for merchant', () => {
    render(<MessageAvatar sender="merchant" botName="ShopBot" theme={defaultTheme} />);
    const avatar = screen.getByTestId('message-avatar');
    
    expect(avatar).toHaveAttribute('aria-label', 'Merchant avatar');
  });

  it('uses default size of 32px', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.width).toBe('32px');
    expect(avatar.style.height).toBe('32px');
  });

  it('accepts custom size prop', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} size={48} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.width).toBe('48px');
    expect(avatar.style.height).toBe('48px');
  });

  it('has data-testid attribute', () => {
    render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    expect(screen.getByTestId('message-avatar')).toBeInTheDocument();
  });

  it('has white text color', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.color).toBe('white');
  });

  it('has circular border radius', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.borderRadius).toBe('50%');
  });

  it('uses font weight 600', () => {
    const { container } = render(<MessageAvatar sender="bot" botName="Bot" theme={defaultTheme} />);
    const avatar = container.firstChild as HTMLElement;
    expect(avatar.style.fontWeight).toBe('600');
  });
});
