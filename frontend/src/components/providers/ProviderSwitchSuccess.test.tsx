/**
 * Component tests for ProviderSwitchSuccess (Story 3.4)
 *
 * Tests ProviderSwitchSuccess component functionality including:
 * - Success notification display
 * - Auto-dismiss after timeout
 * - Screen reader announcements
 * - Provider switch tracking
 * - Accessibility features (ARIA live region, role)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderSwitchSuccess } from './ProviderSwitchSuccess';
import { useLLMProviderStore } from '../../stores/llmProviderStore';

// Mock the store
vi.mock('../../stores/llmProviderStore', () => ({
  useLLMProviderStore: vi.fn(),
}));

const mockCurrentProvider = {
  id: 'openai',
  name: 'OpenAI',
  description: 'GPT-4',
  model: 'gpt-4',
  status: 'active',
  configuredAt: new Date().toISOString(),
  totalTokensUsed: 100000,
  totalCostUsd: 12.50,
};

describe('ProviderSwitchSuccess', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('does not render when no provider switch occurred', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: null,
      previousProviderId: null,
    } as any);

    const { container } = render(<ProviderSwitchSuccess />);

    expect(container.firstChild).toBeNull();
  });

  it('renders success message when provider switches', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    expect(screen.getByText(/successfully switched/i)).toBeInTheDocument();
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
  });

  it('announces to screen readers', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveAttribute('aria-live', 'polite');
  });

  it('auto-dismisses after 5 seconds', async () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    expect(screen.getByRole('alert')).toBeInTheDocument();

    // Fast-forward time
    vi.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  it('displays previous and current provider names', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText(/anthropic/i)).toBeInTheDocument();
  });

  it('has appropriate ARIA attributes', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'polite');
    expect(alert).toHaveAttribute('aria-atomic', 'true');
  });

  it('does not re-announce for same provider', () => {
    const mockStore = {
      currentProvider: mockCurrentProvider,
      previousProviderId: 'openai', // Same as current
    };

    vi.mocked(useLLMProviderStore).mockReturnValue(mockStore as any);

    const { rerender } = render(<ProviderSwitchSuccess />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    // Re-render with same values
    rerender(<ProviderSwitchSuccess />);

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('displays appropriate icon', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    // Check for success icon (SVG)
    const icon = document.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('applies correct styling classes', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    const container = screen.getByRole('alert');
    expect(container.className).toContain('bg-green');
    expect(container.className).toContain('border');
  });

  it('handles null previous provider', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: null,
    } as any);

    const { container } = render(<ProviderSwitchSuccess />);

    // Should not render without previous provider (first setup)
    expect(container.firstChild).toBeNull();
  });

  it('clears timeout on unmount', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    const clearTimeoutSpy = vi.spyOn(globalThis, 'clearTimeout');

    const { unmount } = render(<ProviderSwitchSuccess />);
    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it('respects user preference for reduced motion', () => {
    // Mock reduced motion preference
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
      matches: true,
      media: '(prefers-reduced-motion: reduce)',
    }));

    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    // Component should still render
    expect(screen.getByRole('alert')).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it('has focusable close button', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    expect(closeButton).toBeInTheDocument();
    expect(closeButton).toHaveAttribute('type', 'button');
  });

  it('closes when close button is clicked', async () => {
    const user = userEvent.setup();
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  it('displays informative message about provider switch', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: mockCurrentProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    expect(screen.getByText(/switched from/i)).toBeInTheDocument();
    expect(screen.getByText(/to/i)).toBeInTheDocument();
  });

  it('handles provider with special characters in name', () => {
    const specialNameProvider = {
      ...mockCurrentProvider,
      name: 'AI-Provider 2.0 (Beta)',
    };

    vi.mocked(useLLMProviderStore).mockReturnValue({
      currentProvider: specialNameProvider,
      previousProviderId: 'anthropic',
    } as any);

    render(<ProviderSwitchSuccess />);

    expect(screen.getByText(/AI-Provider 2\.0 \(Beta\)/i)).toBeInTheDocument();
  });
});
