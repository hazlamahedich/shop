/**
 * Component tests for ProviderCard (Story 3.4)
 *
 * Tests ProviderCard component functionality including:
 * - Display of provider information
 * - Active state styling
 * - Click handling for provider selection
 * - Accessibility features (ARIA, keyboard navigation)
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderCard } from './ProviderCard';
import type { Provider } from '../../stores/llmProviderStore';
import { useLLMProviderStore } from '../../stores/llmProviderStore';

// Mock the store
vi.mock('../../stores/llmProviderStore', () => ({
  useLLMProviderStore: vi.fn(),
  // Keep actual Provider type import
  Provider: vi.fn(),
}));

const mockProvider: Provider = {
  id: 'openai',
  name: 'OpenAI',
  description: 'GPT-4 and other models',
  pricing: {
    inputCost: 5.0,
    outputCost: 15.0,
    currency: 'USD',
  },
  models: ['gpt-4', 'gpt-3.5-turbo'],
  features: ['streaming', 'function-calling'],
  isActive: false,
  estimatedMonthlyCost: 12.50,
};

const mockSelectProvider = vi.fn();

describe('ProviderCard', () => {
  beforeEach(() => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      selectProvider: mockSelectProvider,
    } as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders provider name and description', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('GPT-4 and other models')).toBeInTheDocument();
  });

  it('displays pricing information correctly', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    expect(screen.getByText(/\$5\.00/)).toBeInTheDocument(); // input cost
    expect(screen.getByText(/\$15\.00/)).toBeInTheDocument(); // output cost
  });

  it('shows active indicator when provider is active', () => {
    const { rerender } = render(
      <ProviderCard provider={mockProvider} isActive={false} />
    );

    // Initially no active badge
    expect(screen.queryByText('Current')).not.toBeInTheDocument();

    // When active
    rerender(<ProviderCard provider={mockProvider} isActive={true} />);

    expect(screen.getByText('Current')).toBeInTheDocument();
  });

  it('shows estimated monthly cost when available', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    expect(screen.getByText(/\$12\.50/)).toBeInTheDocument();
    expect(screen.getByText(/est\. monthly/i)).toBeInTheDocument();
  });

  it('displays provider features as tags', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    expect(screen.getByText('streaming')).toBeInTheDocument();
    expect(screen.getByText('function-calling')).toBeInTheDocument();
  });

  it('calls selectProvider callback when clicked', async () => {
    const user = userEvent.setup();

    render(<ProviderCard provider={mockProvider} isActive={false} />);

    const card = screen.getByRole('option', { name: /openai/i });
    await user.click(card);

    expect(mockSelectProvider).toHaveBeenCalledWith('openai');
  });

  it('is keyboard accessible', async () => {
    const user = userEvent.setup();

    render(<ProviderCard provider={mockProvider} isActive={false} />);

    const card = screen.getByRole('option', { name: /openai/i });
    card.focus();
    expect(card).toHaveFocus();

    await user.keyboard('{Enter}');
    expect(mockSelectProvider).toHaveBeenCalled();
  });

  it('applies correct aria-selected for active state', () => {
    const { rerender } = render(
      <ProviderCard provider={mockProvider} isActive={false} />
    );

    expect(screen.getByRole('option')).toHaveAttribute('aria-selected', 'false');

    rerender(<ProviderCard provider={mockProvider} isActive={true} />);

    expect(screen.getByRole('option')).toHaveAttribute('aria-selected', 'true');
  });

  it('displays available models', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
  });

  it('applies correct styling for active state', () => {
    const { rerender } = render(
      <ProviderCard provider={mockProvider} isActive={false} />
    );

    const card = screen.getByRole('option');
    expect(card.className).not.toContain('border-blue-500');

    rerender(<ProviderCard provider={mockProvider} isActive={true} />);

    const activeCard = screen.getByRole('option');
    expect(activeCard.className).toContain('border-blue-500');
  });

  it('handles missing estimated monthly cost gracefully', () => {
    const providerWithoutCost = { ...mockProvider, estimatedMonthlyCost: undefined };

    render(<ProviderCard provider={providerWithoutCost} isActive={false} />);

    expect(screen.queryByText(/est\. monthly/i)).not.toBeInTheDocument();
  });

  it('handles empty features array', () => {
    const providerWithoutFeatures = { ...mockProvider, features: [] };

    render(<ProviderCard provider={providerWithoutFeatures} isActive={false} />);

    // Should not crash and should still render basic info
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
  });

  it('has tabIndex 0 for keyboard accessibility', () => {
    render(<ProviderCard provider={mockProvider} isActive={false} />);

    const card = screen.getByRole('option');
    expect(card).toHaveAttribute('tabIndex', '0');
  });
});
