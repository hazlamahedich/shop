import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WebhookVerification } from './WebhookVerification';
import { useWebhookVerificationStore } from '@/stores/webhookVerificationStore';

// Mock the store
vi.mock('@/stores/webhookVerificationStore', () => ({
  useWebhookVerificationStore: vi.fn(),
}));

const mockStore = {
  status: null,
  isTestingFacebook: false,
  isTestingShopify: false,
  isResubscribingFacebook: false,
  isResubscribingShopify: false,
  error: undefined,
  lastTestResult: undefined,
  lastResubscribeResult: undefined,
  getStatus: vi.fn(),
  testFacebookWebhook: vi.fn(),
  testShopifyWebhook: vi.fn(),
  resubscribeFacebookWebhook: vi.fn(),
  resubscribeShopifyWebhook: vi.fn(),
  clearError: vi.fn(),
};

describe('WebhookVerification', () => {
  beforeEach(() => {
    vi.mocked(useWebhookVerificationStore).mockReturnValue(mockStore);
    global.confirm = vi.fn(() => true);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockStore.status = null;
    render(<WebhookVerification />);

    expect(screen.getByText(/loading webhook status/i)).toBeInTheDocument();
  });

  it('renders webhook status cards when data is loaded', async () => {
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        lastWebhookAt: '2024-01-15T10:30:00Z',
        subscriptionStatus: 'active',
        topics: ['messages', 'messaging_postbacks'],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: true,
        lastWebhookAt: '2024-01-15T10:30:00Z',
        subscriptionStatus: 'active',
        topics: ['orders/create', 'orders/updated'],
      },
      overallStatus: 'ready',
      canGoLive: true,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getAllByText(/Facebook Messenger/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Shopify/i).length).toBeGreaterThan(0);
    });
  });

  it('displays ready to go live badge when both platforms connected', async () => {
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      overallStatus: 'ready',
      canGoLive: true,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/ready to go live/i)).toBeInTheDocument();
    });
  });

  it('displays partial setup badge when only one platform connected', async () => {
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
        error: 'Shopify store not connected',
      },
      overallStatus: 'partial',
      canGoLive: false,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/partial setup/i)).toBeInTheDocument();
    });
  });

  it('calls testFacebookWebhook when Test Webhook clicked', async () => {
    const user = userEvent.setup({ delay: null });
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      overallStatus: 'partial',
      canGoLive: false,
    };

    mockStore.testFacebookWebhook.mockImplementation(async () => ({
      testId: 'test-123',
      status: 'success' as const,
      message: 'Webhook test successful',
      pageId: '123456',
    }));

    mockStore.getStatus.mockResolvedValue(undefined);

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getAllByText(/test webhook/i).length).toBeGreaterThan(0);
    });

    const facebookTestButtons = screen.getAllByText('Test Webhook');
    await user.click(facebookTestButtons[0]);

    await waitFor(() => {
      expect(mockStore.testFacebookWebhook).toHaveBeenCalledWith(1);
    });
  });

  it('calls resubscribeFacebookWebhook when Resubscribe clicked', async () => {
    const user = userEvent.setup({ delay: null });
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      overallStatus: 'not_connected',
      canGoLive: false,
    };

    mockStore.resubscribeFacebookWebhook.mockImplementation(async () => ({
      platform: 'facebook' as const,
      status: 'success' as const,
      message: 'Webhook re-subscribed successfully',
      topics: [{ topic: 'messages', success: true }],
    }));

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getAllByText(/resubscribe/i).length).toBeGreaterThan(0);
    });

    const resubscribeButtons = screen.getAllByText('Resubscribe');
    await user.click(resubscribeButtons[0]);

    await waitFor(() => {
      expect(mockStore.resubscribeFacebookWebhook).toHaveBeenCalledWith(1);
    });
  });

  it('displays error message when error exists', async () => {
    mockStore.error = 'Failed to load webhook status';
    mockStore.status = null;

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load webhook status/i)).toBeInTheDocument();
    });
  });

  it('clears error when Dismiss clicked', async () => {
    const user = userEvent.setup();
    mockStore.error = 'Test error';
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      overallStatus: 'not_connected',
      canGoLive: false,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/test error/i)).toBeInTheDocument();
    });

    const dismissButton = screen.getByText('Dismiss');
    await user.click(dismissButton);

    expect(mockStore.clearError).toHaveBeenCalled();
  });

  it('calls getStatus when refresh button clicked', async () => {
    const user = userEvent.setup();
    mockStore.getStatus.mockResolvedValue(undefined);
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      overallStatus: 'ready',
      canGoLive: true,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getAllByRole('button').length).toBeGreaterThan(0);
    });

    const buttons = screen.getAllByRole('button');
    const refreshButton = buttons.find(
      (btn) => btn.querySelector('svg') !== null && !btn.textContent?.match(/test|resubscribe/i)
    );

    if (refreshButton) {
      await user.click(refreshButton);
      // Verify getStatus was called via loadStatus
      expect(mockStore.getStatus).toHaveBeenCalled();
    }
  });

  it('displays last test result when available', async () => {
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: true,
        subscriptionStatus: 'active',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      overallStatus: 'partial',
      canGoLive: false,
    };

    mockStore.lastTestResult = {
      testId: 'test-123',
      status: 'success',
      message: 'Facebook webhook test successful',
      pageId: '123456',
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/facebook webhook test successful/i)).toBeInTheDocument();
    });
  });

  it('displays troubleshooting documentation links', async () => {
    mockStore.status = {
      facebook: {
        webhookUrl: 'https://example.com/api/webhooks/facebook',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      shopify: {
        webhookUrl: 'https://example.com/api/webhooks/shopify',
        connected: false,
        subscriptionStatus: 'inactive',
        topics: [],
      },
      overallStatus: 'not_connected',
      canGoLive: false,
    };

    render(<WebhookVerification />);

    await waitFor(() => {
      expect(screen.getByText(/troubleshooting/i)).toBeInTheDocument();
      expect(screen.getByText('Facebook webhook documentation')).toBeInTheDocument();
      expect(screen.getByText('Shopify webhook documentation')).toBeInTheDocument();
    });
  });
});
