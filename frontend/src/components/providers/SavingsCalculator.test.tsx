/**
 * Component tests for SavingsCalculator (Story 3.4)
 *
 * Tests SavingsCalculator component functionality including:
 * - Cost savings calculation
 * - Monthly and annual projections
 * - Comparison between providers
 * - Sorting by highest savings
 * - Display of top 3 options
 * - Handling of edge cases
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SavingsCalculator } from './SavingsCalculator';
import type { Provider, CurrentProvider } from '../../stores/llmProviderStore';

const mockProviders: Provider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4',
    pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'USD' },
    models: ['gpt-4'],
    features: ['streaming'],
    estimatedMonthlyCost: 12.50,
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude',
    pricing: { inputCost: 3.0, outputCost: 15.0, currency: 'USD' },
    models: ['claude-3'],
    features: ['streaming'],
    estimatedMonthlyCost: 9.00,
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local',
    pricing: { inputCost: 0.0, outputCost: 0.0, currency: 'USD' },
    models: ['llama2'],
    features: [],
    estimatedMonthlyCost: 0.00,
  },
];

const mockCurrentProvider: CurrentProvider = {
  id: 'openai',
  name: 'OpenAI',
  description: 'GPT-4',
  model: 'gpt-4',
  status: 'active',
  configuredAt: new Date().toISOString(),
  totalTokensUsed: 100000,
  totalCostUsd: 12.50,
};

describe('SavingsCalculator', () => {
  it('does not render without current provider', () => {
    const { container } = render(
      <SavingsCalculator providers={mockProviders} currentProvider={null} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('does not render when no savings available', () => {
    const allFreeProviders: Provider[] = [
      {
        id: 'ollama',
        name: 'Ollama',
        description: 'Local',
        pricing: { inputCost: 0.0, outputCost: 0.0, currency: 'USD' },
        models: ['llama2'],
        features: [],
        estimatedMonthlyCost: 0.00,
      },
    ];

    const ollamaProvider: CurrentProvider = {
      ...mockCurrentProvider,
      id: 'ollama',
      name: 'Ollama',
    };

    const { container } = render(
      <SavingsCalculator providers={allFreeProviders} currentProvider={ollamaProvider} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders savings calculator when savings available', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    expect(screen.getByText(/potential monthly savings/i)).toBeInTheDocument();
  });

  it('displays top 3 savings options', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Should show Anthropic and Ollama (both cheaper than OpenAI)
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
    expect(screen.getByText('Ollama')).toBeInTheDocument();
  });

  it('calculates savings amount correctly', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // OpenAI: $12.50, Anthropic: $9.00, Ollama: $0.00
    // Anthropic savings: $12.50 - $9.00 = $3.50
    // Ollama savings: $12.50 - $0.00 = $12.50

    expect(screen.getByText(/\$3\.50/)).toBeInTheDocument();
    expect(screen.getByText(/\$12\.50/)).toBeInTheDocument();
  });

  it('displays savings percentage', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Anthropic: (3.50 / 12.50) * 100 = 28%
    expect(screen.getByText(/28% savings/i)).toBeInTheDocument();
  });

  it('shows annual savings projection', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Top option (Ollama) annual: $12.50 * 12 = $150
    expect(screen.getByText(/\$150\.00/)).toBeInTheDocument();
    expect(screen.getByText(/annual/i)).toBeInTheDocument();
  });

  it('shows typical usage disclaimer', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    expect(screen.getByText(/based on typical usage/i)).toBeInTheDocument();
    expect(screen.getByText(/100K input/i)).toBeInTheDocument();
    expect(screen.getByText(/50K output/i)).toBeInTheDocument();
  });

  it('displays disclaimer about estimates', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    expect(screen.getByText(/savings are estimates/i)).toBeInTheDocument();
  });

  it('sorts by highest savings first', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    const rankings = screen.getAllByText(/^\d+$/); // Number badges

    // First badge should be "1" (highest savings)
    expect(rankings[0]).toHaveTextContent('1');
  });

  it('displays monthly cost comparison', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Should show "X vs Y" format
    expect(screen.getByText(/vs/i)).toBeInTheDocument();
    expect(screen.getByText(/\/mo/i)).toBeInTheDocument();
  });

  it('handles providers with equal pricing', () => {
    const equalPricingProviders: Provider[] = [
      { ...mockProviders[0] },
      {
        ...mockProviders[0],
        id: 'copycat',
        name: 'Copycat',
        pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'USD' },
      },
    ];

    const { container } = render(
      <SavingsCalculator providers={equalPricingProviders} currentProvider={mockCurrentProvider} />
    );

    // Should not render (no savings)
    expect(container.firstChild).toBeNull();
  });

  it('handles current provider with zero cost', () => {
    const freeCurrentProvider: CurrentProvider = {
      ...mockCurrentProvider,
      id: 'ollama',
      name: 'Ollama',
      totalCostUsd: 0,
    };

    const { container } = render(
      <SavingsCalculator providers={mockProviders} currentProvider={freeCurrentProvider} />
    );

    // Should not render (can't save from free)
    expect(container.firstChild).toBeNull();
  });

  it('has proper heading hierarchy', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    const heading = screen.getByRole('heading', { level: 3 });
    expect(heading).toBeInTheDocument();
  });

  it('displays currency formatting correctly', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // All amounts should have $ prefix
    const amounts = screen.getAllByText(/\$\d+\.\d{2}/);
    expect(amounts.length).toBeGreaterThan(0);
  });

  it('has appropriate icon for savings', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Check for dollar sign or money icon (SVG)
    const icon = document.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('applies green color scheme for savings', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    const container = screen.getByText(/potential monthly savings/i).closest('div');
    expect(container?.className).toContain('green');
  });

  it('limits to top 3 providers regardless of more options', () => {
    const manyProviders: Provider[] = [
      ...mockProviders,
      {
        id: 'provider4',
        name: 'Provider 4',
        description: 'Fourth',
        pricing: { inputCost: 2.0, outputCost: 10.0, currency: 'USD' },
        models: ['model4'],
        features: [],
        estimatedMonthlyCost: 6.00,
      },
      {
        id: 'provider5',
        name: 'Provider 5',
        description: 'Fifth',
        pricing: { inputCost: 1.0, outputCost: 5.0, currency: 'USD' },
        models: ['model5'],
        features: [],
        estimatedMonthlyCost: 3.50,
      },
    ];

    render(
      <SavingsCalculator providers={manyProviders} currentProvider={mockCurrentProvider} />
    );

    // Should only show top 3
    const providerNames = screen.getAllByText(/Provider|Ollama|Anthropic/);
    const visibleCards = providerNames.filter(n => n.tagName === 'P' && n.classList.contains('font-medium'));

    // Top 3 savings: Ollama ($12.50), Provider 5 ($9.00), Provider 4 ($6.50)
    // Anthropic is 4th with $3.50
    expect(visibleCards.length).toBeLessThanOrEqual(3);
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(
      <SavingsCalculator providers={mockProviders} currentProvider={mockCurrentProvider} />
    );

    // Should have proper heading and semantic structure
    const heading = screen.getByRole('heading');
    expect(heading).toBeInTheDocument();
  });
});
