/**
 * Component tests for ProviderComparison (Story 3.4)
 *
 * Tests ProviderComparison component functionality including:
 * - Provider comparison table rendering
 * - Pricing information display
 * - Feature comparison
 * - Model availability comparison
 * - Accessibility features (ARIA labels, table semantics)
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProviderComparison } from './ProviderComparison';
import type { Provider } from '../../stores/llmProviderStore';

const mockProviders: Provider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4 models',
    pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'USD' },
    models: ['gpt-4', 'gpt-3.5-turbo'],
    features: ['streaming', 'function-calling', 'vision'],
    estimatedMonthlyCost: 12.50,
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude models',
    pricing: { inputCost: 3.0, outputCost: 15.0, currency: 'USD' },
    models: ['claude-3-opus', 'claude-3-sonnet'],
    features: ['streaming', 'function-calling'],
    estimatedMonthlyCost: 9.00,
  },
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local models',
    pricing: { inputCost: 0.0, outputCost: 0.0, currency: 'USD' },
    models: ['llama2', 'mistral'],
    features: ['streaming'],
    estimatedMonthlyCost: 0.00,
  },
];

describe('ProviderComparison', () => {
  it('renders comparison table', () => {
    render(<ProviderComparison providers={mockProviders} />);

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders all providers in table', () => {
    render(<ProviderComparison providers={mockProviders} />);

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Anthropic')).toBeInTheDocument();
    expect(screen.getByText('Ollama')).toBeInTheDocument();
  });

  it('displays pricing information correctly', () => {
    render(<ProviderComparison providers={mockProviders} />);

    // Input costs
    expect(screen.getByText(/\$5\.00/)).toBeInTheDocument(); // OpenAI input
    expect(screen.getByText(/\$3\.00/)).toBeInTheDocument(); // Anthropic input
    expect(screen.getByText(/\$0\.00/)).toBeInTheDocument(); // Ollama input

    // Output costs
    expect(screen.getByText(/\$15\.00/)).toBeInTheDocument(); // OpenAI output
  });

  it('shows provider features in table', () => {
    render(<ProviderComparison providers={mockProviders} />);

    expect(screen.getByText('streaming')).toBeInTheDocument();
    expect(screen.getByText('function-calling')).toBeInTheDocument();
    expect(screen.getByText('vision')).toBeInTheDocument();
  });

  it('displays available models', () => {
    render(<ProviderComparison providers={mockProviders} />);

    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('claude-3-opus')).toBeInTheDocument();
    expect(screen.getByText('llama2')).toBeInTheDocument();
  });

  it('has proper table headers with ARIA labels', () => {
    render(<ProviderComparison providers={mockProviders} />);

    expect(screen.getByRole('columnheader', { name: /provider/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /input cost/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /output cost/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /features/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /models/i })).toBeInTheDocument();
  });

  it('handles empty providers array', () => {
    const { container } = render(<ProviderComparison providers={[]} />);

    expect(container.firstChild).toBeNull();
  });

  it('handles providers with no features', () => {
    const providersWithoutFeatures: Provider[] = [
      {
        id: 'basic',
        name: 'Basic Provider',
        description: 'No features',
        pricing: { inputCost: 1.0, outputCost: 2.0, currency: 'USD' },
        models: ['basic-model'],
        features: [],
      },
    ];

    render(<ProviderComparison providers={providersWithoutFeatures} />);

    expect(screen.getByText('Basic Provider')).toBeInTheDocument();
    // Should not crash
  });

  it('displays currency symbol correctly', () => {
    render(<ProviderComparison providers={mockProviders} />);

    // All prices should have $ prefix
    const prices = screen.getAllByText(/\$\d+\.\d{2}/);
    expect(prices.length).toBeGreaterThan(0);
  });

  it('formats costs to 2 decimal places', () => {
    render(<ProviderComparison providers={mockProviders} />);

    // Check for exact decimal formatting
    expect(screen.getByText('$5.00')).toBeInTheDocument();
    expect(screen.getByText('$3.00')).toBeInTheDocument();
  });

  it('has proper table caption for accessibility', () => {
    render(<ProviderComparison providers={mockProviders} />);

    const table = screen.getByRole('table');
    expect(table).toHaveAttribute('caption');
  });

  it('renders feature badges', () => {
    render(<ProviderComparison providers={mockProviders} />);

    // Features should be visually distinct (badges)
    const features = screen.getAllByText('streaming');
    expect(features.length).toBeGreaterThan(0);
  });

  it('sorts providers consistently', () => {
    render(<ProviderComparison providers={mockProviders} />);

    const tableRows = screen.getAllByRole('row');
    // Header row + data rows
    expect(tableRows.length).toBe(mockProviders.length + 1);
  });

  it('handles providers with missing optional fields', () => {
    const minimalProviders: Provider[] = [
      {
        id: 'minimal',
        name: 'Minimal Provider',
        description: 'Minimal info',
        pricing: { inputCost: 0, outputCost: 0, currency: 'USD' },
        models: [],
        features: [],
      },
    ];

    const { container } = render(
      <ProviderComparison providers={minimalProviders} />
    );

    expect(container.firstChild).not.toBeNull();
  });

  it('displays monthly cost estimate if available', () => {
    render(<ProviderComparison providers={mockProviders} />);

    // Check if monthly cost is displayed
    expect(screen.getByText(/\$12\.50/)).toBeInTheDocument();
    expect(screen.getByText(/\$9\.00/)).toBeInTheDocument();
  });

  it('handles different currencies', () => {
    const providersWithEUR: Provider[] = [
      {
        ...mockProviders[0],
        pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'EUR' },
      },
    ];

    render(<ProviderComparison providers={providersWithEUR} />);

    // Should display EUR symbol or handle currency
    expect(screen.getByText(/EUR/i)).toBeInTheDocument();
  });

  it('is responsive on mobile viewports', () => {
    // Test with mobile viewport
    globalThis.innerWidth = 375;
    globalThis.dispatchEvent(new Event('resize'));

    const { container } = render(
      <ProviderComparison providers={mockProviders} />
    );

    expect(container.firstChild).not.toBeNull();
  });

  it('has proper semantic table structure', () => {
    render(<ProviderComparison providers={mockProviders} />);

    const table = screen.getByRole('table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    expect(thead).toBeInTheDocument();
    expect(tbody).toBeInTheDocument();
  });
});
