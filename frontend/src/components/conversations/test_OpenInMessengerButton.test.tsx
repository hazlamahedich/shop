/**
 * Unit tests for OpenInMessengerButton Component - Story 4-9
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OpenInMessengerButton from './OpenInMessengerButton';
import type { HybridModeState, FacebookPageInfo } from '../../types/conversation';

describe('OpenInMessengerButton', () => {
  const mockProps = {
    conversationId: 123,
    platformSenderId: 'test_psid_12345',
    hybridMode: null,
    facebookPage: {
      pageId: 'test_page_123',
      pageName: 'Test Page',
      isConnected: true,
    } as FacebookPageInfo,
    isLoading: false,
    onHybridModeChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    window.open = vi.fn();
  });

  describe('Rendering', () => {
    it('renders with correct text when hybrid mode is inactive', () => {
      render(<OpenInMessengerButton {...mockProps} />);
      
      expect(screen.getByTestId('open-in-messenger-btn')).toBeInTheDocument();
      expect(screen.getByText('Open in Messenger')).toBeInTheDocument();
    });

    it('renders "Return to Bot" when hybrid mode is active', () => {
      const hybridMode: HybridModeState = {
        enabled: true,
        activatedAt: '2026-02-15T10:00:00Z',
        activatedBy: 'merchant',
        expiresAt: '2026-02-15T12:00:00Z',
      };
      
      render(<OpenInMessengerButton {...mockProps} hybridMode={hybridMode} />);
      
      expect(screen.getByTestId('return-to-bot-btn')).toBeInTheDocument();
      expect(screen.getByText('Return to Bot')).toBeInTheDocument();
    });

    it('shows loading spinner when isLoading is true', () => {
      render(<OpenInMessengerButton {...mockProps} isLoading={true} />);
      
      const button = screen.getByTestId('open-in-messenger-btn');
      expect(button).toBeDisabled();
    });
  });

  describe('Facebook Page Connection', () => {
    it('button is disabled when no Facebook page connection', () => {
      render(
        <OpenInMessengerButton 
          {...mockProps} 
          facebookPage={{ pageId: null, pageName: null, isConnected: false }}
        />
      );
      
      const button = screen.getByTestId('open-in-messenger-btn');
      expect(button).toBeDisabled();
    });

    it('shows tooltip when hovering over disabled button', async () => {
      const user = userEvent.setup();
      render(
        <OpenInMessengerButton 
          {...mockProps} 
          facebookPage={{ pageId: null, pageName: null, isConnected: false }}
        />
      );
      
      const button = screen.getByTestId('open-in-messenger-btn');
      await user.hover(button);
      
      const tooltip = await screen.findByTestId('no-facebook-tooltip');
      expect(tooltip).toBeInTheDocument();
      expect(screen.getByText('Connect a Facebook page to enable Messenger replies')).toBeInTheDocument();
    });
  });

  describe('Click Behavior', () => {
    it('opens Messenger URL in new tab with correct parameters', async () => {
      const onHybridModeChange = vi.fn().mockResolvedValue(undefined);
      
      render(<OpenInMessengerButton {...mockProps} onHybridModeChange={onHybridModeChange} />);
      
      const button = screen.getByTestId('open-in-messenger-btn');
      fireEvent.click(button);
      
      expect(window.open).toHaveBeenCalledWith(
        'https://m.me/test_page_123?thread_id=test_psid_12345',
        '_blank'
      );
      
      await waitFor(() => {
        expect(onHybridModeChange).toHaveBeenCalledWith(true);
      });
    });

    it('calls onHybridModeChange with false when "Return to Bot" is clicked', async () => {
      const onHybridModeChange = vi.fn().mockResolvedValue(undefined);
      const hybridMode: HybridModeState = {
        enabled: true,
        activatedAt: '2026-02-15T10:00:00Z',
        activatedBy: 'merchant',
        expiresAt: '2026-02-15T12:00:00Z',
      };
      
      render(
        <OpenInMessengerButton 
          {...mockProps} 
          hybridMode={hybridMode} 
          onHybridModeChange={onHybridModeChange}
        />
      );
      
      const button = screen.getByTestId('return-to-bot-btn');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(onHybridModeChange).toHaveBeenCalledWith(false);
      });
      
      expect(window.open).not.toHaveBeenCalled();
    });

    it('does not open Messenger URL when button is disabled', () => {
      render(
        <OpenInMessengerButton 
          {...mockProps} 
          facebookPage={{ pageId: null, pageName: null, isConnected: false }}
        />
      );
      
      const button = screen.getByTestId('open-in-messenger-btn');
      fireEvent.click(button);
      
      expect(window.open).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has correct aria-label for "Open in Messenger" button', () => {
      render(<OpenInMessengerButton {...mockProps} />);
      
      const button = screen.getByTestId('open-in-messenger-btn');
      expect(button).toHaveAttribute('aria-label', 'Open conversation in Messenger');
    });

    it('has correct aria-label for "Return to Bot" button', () => {
      const hybridMode: HybridModeState = {
        enabled: true,
        activatedAt: '2026-02-15T10:00:00Z',
        activatedBy: 'merchant',
        expiresAt: '2026-02-15T12:00:00Z',
      };
      
      render(<OpenInMessengerButton {...mockProps} hybridMode={hybridMode} />);
      
      const button = screen.getByTestId('return-to-bot-btn');
      expect(button).toHaveAttribute('aria-label', 'Return control to bot');
    });
  });
});
