/**
 * Tests for FacebookConnection component
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FacebookConnection } from './FacebookConnection';
import { useIntegrationsStore } from '../../stores/integrationsStore';

// Mock the store
vi.mock('../../stores/integrationsStore');

describe('FacebookConnection', () => {
  const mockCheckFacebookStatus = vi.fn();
  const mockInitiateFacebookOAuth = vi.fn();
  const mockDisconnectFacebook = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementation
    (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
      facebookStatus: 'idle',
      facebookConnection: {
        connected: false,
        webhookVerified: false,
      },
      facebookError: undefined,
      checkFacebookStatus: mockCheckFacebookStatus,
      initiateFacebookOAuth: mockInitiateFacebookOAuth,
      disconnectFacebook: mockDisconnectFacebook,
      clearError: mockClearError,
    });
  });

  describe('Not Connected State', () => {
    it('should render connect button when not connected', () => {
      render(<FacebookConnection />);

      expect(screen.getByText('Connect Facebook Page')).toBeInTheDocument();
      expect(screen.getByText(/Connect your facebook page/i)).toBeInTheDocument();
    });

    it('should call checkFacebookStatus on mount', () => {
      render(<FacebookConnection />);

      expect(mockCheckFacebookStatus).toHaveBeenCalledTimes(1);
    });

    it('should call initiateFacebookOAuth when connect button is clicked', async () => {
      const user = userEvent.setup();
      render(<FacebookConnection />);

      const connectButton = screen.getByText('Connect Facebook Page');
      await user.click(connectButton);

      expect(mockClearError).toHaveBeenCalled();
      expect(mockInitiateFacebookOAuth).toHaveBeenCalled();
    });

    it('should disable connect button when connecting', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'connecting',
        facebookConnection: { connected: false, webhookVerified: false },
        facebookError: undefined,
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      const connectButton = screen.getByRole('button', { name: /connecting/i });
      expect(connectButton).toBeDisabled();
    });
  });

  describe('Connected State', () => {
    beforeEach(() => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'connected',
        facebookConnection: {
          connected: true,
          pageId: '123456789',
          pageName: 'Test Store',
          pagePictureUrl: 'https://example.com/picture.jpg',
          connectedAt: '2026-02-03T00:00:00Z',
          webhookVerified: true,
        },
        facebookError: undefined,
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });
    });

    it('should display page information when connected', () => {
      render(<FacebookConnection />);

      expect(screen.getByText('Test Store')).toBeInTheDocument();
      expect(screen.getByText(/123456789/)).toBeInTheDocument();
    });

    it('should show connected badge', () => {
      render(<FacebookConnection />);

      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    it('should show webhook verified status', () => {
      render(<FacebookConnection />);

      expect(screen.getByText('Verified')).toBeInTheDocument();
    });

    it('should call disconnectFacebook when disconnect button is clicked', async () => {
      const user = userEvent.setup();
      render(<FacebookConnection />);

      const disconnectButton = screen.getByText('Disconnect Page');
      await user.click(disconnectButton);

      expect(mockClearError).toHaveBeenCalled();
      expect(mockDisconnectFacebook).toHaveBeenCalled();
    });

    it('should call onConnectionChange callback when connection changes', () => {
      const onConnectionChange = vi.fn();

      render(<FacebookConnection onConnectionChange={onConnectionChange} />);

      // Should be called with true on mount since connected
      expect(onConnectionChange).toHaveBeenCalledWith(true);
    });
  });

  describe('Error State', () => {
    it('should display error alert when error occurs', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'error',
        facebookConnection: { connected: false, webhookVerified: false },
        facebookError: 'OAuth state mismatch',
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      expect(screen.getByText('Connection Error')).toBeInTheDocument();
      expect(screen.getByText('OAuth state mismatch')).toBeInTheDocument();
    });

    it('should display troubleshooting steps on error', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'error',
        facebookConnection: { connected: false, webhookVerified: false },
        facebookError: 'Connection failed',
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      expect(screen.getByText(/Troubleshooting:/i)).toBeInTheDocument();
      expect(screen.getByText(/Make sure you have admin access/i)).toBeInTheDocument();
    });

    it('should clear error when dismissed', async () => {
      const user = userEvent.setup();
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'error',
        facebookConnection: { connected: false, webhookVerified: false },
        facebookError: 'Connection failed',
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      await user.click(dismissButton);

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('Compact Mode', () => {
    it('should render compact layout when compact prop is true', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'connected',
        facebookConnection: {
          connected: true,
          pageId: '123456789',
          pageName: 'Compact Test',
          pagePictureUrl: 'https://example.com/pic.jpg',
          webhookVerified: true,
        },
        facebookError: undefined,
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection compact />);

      expect(screen.getByText('Compact Test')).toBeInTheDocument();
      expect(screen.getByText('Connected')).toBeInTheDocument();
      // Should not have the full layout elements
      expect(screen.queryByText('Connect Your Facebook Page')).not.toBeInTheDocument();
    });

    it('should show connect button in compact mode when not connected', () => {
      render(<FacebookConnection compact />);

      expect(screen.getByText('Connect')).toBeInTheDocument();
      expect(screen.queryByText('Disconnect')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for buttons', () => {
      render(<FacebookConnection />);

      const connectButton = screen.getByRole('button', { name: 'Connect Facebook Page' });
      expect(connectButton).toBeInTheDocument();
    });

    it('should disable buttons during loading state', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'connecting',
        facebookConnection: { connected: false, webhookVerified: false },
        facebookError: undefined,
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      const buttons = screen.queryAllByRole('button');
      const nonDisabledButtons = buttons.filter(btn => !btn.hasAttribute('disabled'));
      expect(nonDisabledButtons.length).toBe(0);
    });

    it('should have proper alt text for page picture', () => {
      (useIntegrationsStore as unknown as jest.Mock).mockReturnValue({
        facebookStatus: 'connected',
        facebookConnection: {
          connected: true,
          pageId: '123456789',
          pageName: 'Test Alt',
          pagePictureUrl: 'https://example.com/pic.jpg',
          webhookVerified: true,
        },
        facebookError: undefined,
        checkFacebookStatus: mockCheckFacebookStatus,
        initiateFacebookOAuth: mockInitiateFacebookOAuth,
        disconnectFacebook: mockDisconnectFacebook,
        clearError: mockClearError,
      });

      render(<FacebookConnection />);

      const image = screen.getByAltText('Test Alt');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/pic.jpg');
    });
  });
});
