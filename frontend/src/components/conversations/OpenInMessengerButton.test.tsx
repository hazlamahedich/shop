/**
 * OpenInMessengerButton Component Tests
 * Story 4-9 & 4-10: Tests for hybrid mode button behavior
 *
 * @vitest-environment jsdom
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OpenInMessengerButton from './OpenInMessengerButton';
import type { HybridModeState, FacebookPageInfo } from '../../types/conversation';

const mockHybridModeActive: HybridModeState = {
  enabled: true,
  activatedAt: new Date().toISOString(),
  expiresAt: new Date(Date.now() + 7200000).toISOString(),
  remainingSeconds: 7200,
};

const mockHybridModeInactive: HybridModeState = {
  enabled: false,
  activatedAt: null,
  expiresAt: null,
  remainingSeconds: 0,
};

const mockFacebookPageConnected: FacebookPageInfo = {
  isConnected: true,
  pageId: 'test_page_123',
  pageName: 'Test Page',
};

const mockFacebookPageDisconnected: FacebookPageInfo = {
  isConnected: false,
  pageId: null,
  pageName: null,
};

describe('OpenInMessengerButton', () => {
  const mockOnHybridModeChange = vi.fn();
  const mockOnConversationRefresh = vi.fn();
  const originalOpen = window.open;

  beforeEach(() => {
    vi.clearAllMocks();
    window.open = vi.fn();
  });

  afterEach(() => {
    window.open = originalOpen;
  });

  describe('AC1: Return to Bot Button Visibility', () => {
    it('[P1] shows "Return to Bot" button when hybrid mode is active', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByTestId('return-to-bot-btn')).toBeInTheDocument();
      expect(screen.getByText('Return to Bot')).toBeInTheDocument();
    });

    it('[P1] shows "Open in Messenger" button when hybrid mode is inactive', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeInactive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByTestId('open-in-messenger-btn')).toBeInTheDocument();
      expect(screen.getByText('Open in Messenger')).toBeInTheDocument();
    });

    it('[P1] shows "Open in Messenger" when hybridMode is null', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={null}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByTestId('open-in-messenger-btn')).toBeInTheDocument();
    });
  });

  describe('AC1: Disabled State', () => {
    it('[P1] disables button when Facebook page is not connected', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageDisconnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('[P1] shows tooltip when hovering over disabled button', async () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageDisconnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      const button = screen.getByRole('button');
      await userEvent.hover(button);

      expect(screen.getByTestId('no-facebook-tooltip')).toBeInTheDocument();
      expect(screen.getByText('Connect a Facebook page to enable Messenger replies')).toBeInTheDocument();
    });

    it('[P1] disables button when isLoading prop is true', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          isLoading={true}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  describe('AC2 & AC3: Return to Bot Click Behavior', () => {
    it('[P0] calls onHybridModeChange with false when clicking "Return to Bot"', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);
      mockOnConversationRefresh.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
          onConversationRefresh={mockOnConversationRefresh}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      expect(mockOnHybridModeChange).toHaveBeenCalledWith(false);
    });

    it('[P1] shows toast notification after successful return to bot', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);
      mockOnConversationRefresh.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
          onConversationRefresh={mockOnConversationRefresh}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('return-to-bot-toast')).toBeInTheDocument();
        expect(screen.getByText('Bot is back in control')).toBeInTheDocument();
      });
    });

    it('[P1] calls onConversationRefresh after successful return to bot', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);
      mockOnConversationRefresh.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
          onConversationRefresh={mockOnConversationRefresh}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      await waitFor(() => {
        expect(mockOnConversationRefresh).toHaveBeenCalled();
      });
    });

    it('[P2] toast disappears after 3 seconds', async () => {
      vi.useFakeTimers();
      mockOnHybridModeChange.mockResolvedValue(undefined);
      mockOnConversationRefresh.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
          onConversationRefresh={mockOnConversationRefresh}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      await waitFor(() => {
        expect(screen.getByTestId('return-to-bot-toast')).toBeInTheDocument();
      });

      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(screen.queryByTestId('return-to-bot-toast')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });
  });

  describe('Open in Messenger Click Behavior', () => {
    it('[P1] opens Messenger URL when clicking "Open in Messenger"', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_456"
          hybridMode={mockHybridModeInactive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      await userEvent.click(screen.getByTestId('open-in-messenger-btn'));

      expect(window.open).toHaveBeenCalledWith(
        'https://m.me/test_page_123?thread_id=psid_456',
        '_blank'
      );
    });

    it('[P1] enables hybrid mode after opening Messenger', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_456"
          hybridMode={mockHybridModeInactive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      await userEvent.click(screen.getByTestId('open-in-messenger-btn'));

      await waitFor(() => {
        expect(mockOnHybridModeChange).toHaveBeenCalledWith(true);
      });
    });
  });

  describe('Loading States', () => {
    it('[P1] shows spinner when isToggling is true (return to bot)', async () => {
      mockOnHybridModeChange.mockImplementation(() => new Promise(() => {}));

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('[P1] shows spinner when isLoading prop is true', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          isLoading={true}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('[P2] has correct aria-label for "Return to Bot" button', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Return control to bot'
      );
    });

    it('[P2] has correct aria-label for "Open in Messenger" button', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeInactive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Open conversation in Messenger'
      );
    });

    it('[P2] toast has role="status" and aria-live="polite"', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);
      mockOnConversationRefresh.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
          onConversationRefresh={mockOnConversationRefresh}
        />
      );

      await userEvent.click(screen.getByTestId('return-to-bot-btn'));

      await waitFor(() => {
        const toast = screen.getByTestId('return-to-bot-toast');
        expect(toast).toHaveAttribute('role', 'status');
        expect(toast).toHaveAttribute('aria-live', 'polite');
      });
    });

    it('[P2] is focusable and can be activated with keyboard', async () => {
      mockOnHybridModeChange.mockResolvedValue(undefined);

      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      const button = screen.getByTestId('return-to-bot-btn');
      button.focus();
      expect(button).toHaveFocus();

      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      await waitFor(() => {
        expect(mockOnHybridModeChange).toHaveBeenCalled();
      });
    });
  });

  describe('Visual States', () => {
    it('[P2] applies green styling for "Return to Bot" button', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeActive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      const button = screen.getByTestId('return-to-bot-btn');
      expect(button.className).toContain('bg-green-600');
    });

    it('[P2] applies blue styling for "Open in Messenger" button', () => {
      render(
        <OpenInMessengerButton
          conversationId={123}
          platformSenderId="psid_123"
          hybridMode={mockHybridModeInactive}
          facebookPage={mockFacebookPageConnected}
          onHybridModeChange={mockOnHybridModeChange}
        />
      );

      const button = screen.getByTestId('open-in-messenger-btn');
      expect(button.className).toContain('bg-blue-600');
    });
  });
});
