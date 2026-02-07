/**
 * Component tests for ProviderConfigModal (Story 3.4)
 *
 * Tests ProviderConfigModal component functionality including:
 * - Form rendering for provider configuration
 * - API key input with visibility toggle
 * - Server URL input for custom providers
 * - Model selection dropdown
 * - Validation and error handling
 * - Cost estimate display
 * - Accessibility features (focus trap, ARIA)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProviderConfigModal } from './ProviderConfigModal';
import { useLLMProviderStore } from '../../stores/llmProviderStore';

// Mock the store
vi.mock('../../stores/llmProviderStore', () => ({
  useLLMProviderStore: vi.fn(),
}));

const mockStore = {
  selectedProvider: {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4 models',
    pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'USD' },
    models: ['gpt-4', 'gpt-3.5-turbo'],
    features: ['streaming'],
    estimatedMonthlyCost: 12.50,
  },
  switchProvider: vi.fn(),
  validateProvider: vi.fn(),
  closeConfigModal: vi.fn(),
  isSwitching: false,
  validationInProgress: false,
  switchError: null,
};

describe('ProviderConfigModal', () => {
  beforeEach(() => {
    vi.mocked(useLLMProviderStore).mockReturnValue(mockStore as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders modal when provider is selected', () => {
    render(<ProviderConfigModal />);

    expect(screen.getByText(/configure openai/i)).toBeInTheDocument();
    expect(screen.getByText(/api key/i)).toBeInTheDocument();
  });

  it('displays provider name in title', () => {
    render(<ProviderConfigModal />);

    expect(screen.getByText('OpenAI')).toBeInTheDocument();
  });

  it('shows cost estimate section', () => {
    render(<ProviderConfigModal />);

    expect(screen.getByText(/estimated monthly cost/i)).toBeInTheDocument();
    expect(screen.getByText(/\$12\.50/)).toBeInTheDocument();
  });

  it('renders API key input field', () => {
    render(<ProviderConfigModal />);

    const input = screen.getByLabelText(/api key/i) as HTMLInputElement;
    expect(input).toBeInTheDocument();
    expect(input.type).toBe('password');
  });

  it('toggles API key visibility', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    const input = screen.getByLabelText(/api key/i) as HTMLInputElement;
    const toggleButton = screen.getByRole('button', { name: /show/i });

    expect(input.type).toBe('password');

    await user.click(toggleButton);

    expect(input.type).toBe('text');

    await user.click(toggleButton);

    expect(input.type).toBe('password');
  });

  it('renders server URL input for custom providers', () => {
    const customProvider = {
      ...mockStore.selectedProvider,
      id: 'custom-server',
    };
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      selectedProvider: customProvider,
    } as any);

    render(<ProviderConfigModal />);

    expect(screen.getByLabelText(/server url/i)).toBeInTheDocument();
  });

  it('renders model selection dropdown', () => {
    render(<ProviderConfigModal />);

    expect(screen.getByLabelText(/model/i)).toBeInTheDocument();
  });

  it('displays available models in dropdown', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    const select = screen.getByLabelText(/model/i);
    await user.click(select);

    expect(screen.getByText('gpt-4')).toBeInTheDocument();
    expect(screen.getByText('gpt-3.5-turbo')).toBeInTheDocument();
  });

  it('calls switchProvider when form is submitted', async () => {
    const user = userEvent.setup();
    mockStore.switchProvider.mockResolvedValue(undefined);

    render(<ProviderConfigModal />);

    const apiKeyInput = screen.getByLabelText(/api key/i);
    await user.type(apiKeyInput, 'test-api-key');

    const submitButton = screen.getByRole('button', { name: /switch provider/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockStore.switchProvider).toHaveBeenCalledWith({
        providerId: 'openai',
        apiKey: 'test-api-key',
      });
    });
  });

  it('shows loading state during switch', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      isSwitching: true,
    } as any);

    render(<ProviderConfigModal />);

    const submitButton = screen.getByRole('button', { name: /switching/i });
    expect(submitButton).toBeDisabled();
  });

  it('displays error message when switch fails', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      switchError: 'Invalid API key',
    } as any);

    render(<ProviderConfigModal />);

    expect(screen.getByText(/invalid api key/i)).toBeInTheDocument();
  });

  it('closes modal when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockStore.closeConfigModal).toHaveBeenCalled();
  });

  it('closes modal on escape key press', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    await user.keyboard('{Escape}');

    expect(mockStore.closeConfigModal).toHaveBeenCalled();
  });

  it('has proper focus management', async () => {
    render(<ProviderConfigModal />);

    // Focus should be trapped in modal
    const firstInput = screen.getByLabelText(/api key/i);
    expect(firstInput).toHaveFocus();
  });

  it('validates API key is required', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    const submitButton = screen.getByRole('button', { name: /switch provider/i });
    await user.click(submitButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/api key is required/i)).toBeInTheDocument();
    });
  });

  it('shows validation in progress state', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      validationInProgress: true,
    } as any);

    render(<ProviderConfigModal />);

    expect(screen.getByText(/validating/i)).toBeInTheDocument();
  });

  it('calls validateProvider when validate button is clicked', async () => {
    const user = userEvent.setup();
    mockStore.validateProvider.mockResolvedValue({
      valid: true,
      provider: {
        id: 'openai',
        name: 'OpenAI',
        testResponse: 'Valid',
        latencyMs: 100,
      },
      validatedAt: new Date().toISOString(),
    });

    render(<ProviderConfigModal />);

    const apiKeyInput = screen.getByLabelText(/api key/i);
    await user.type(apiKeyInput, 'test-api-key');

    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      expect(mockStore.validateProvider).toHaveBeenCalledWith({
        providerId: 'openai',
        apiKey: 'test-api-key',
      });
    });
  });

  it('displays validation success message', async () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      validationResult: {
        valid: true,
        provider: {
          id: 'openai',
          name: 'OpenAI',
          testResponse: 'Success',
          latencyMs: 150,
        },
        validatedAt: new Date().toISOString(),
      },
    } as any);

    render(<ProviderConfigModal />);

    expect(screen.getByText(/configuration valid/i)).toBeInTheDocument();
    expect(screen.getByText(/150ms latency/i)).toBeInTheDocument();
  });

  it('does not render when no provider is selected', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      selectedProvider: null,
    } as any);

    const { container } = render(<ProviderConfigModal />);

    expect(container.firstChild).toBeNull();
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<ProviderConfigModal />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby');
  });

  it('handles model selection', async () => {
    const user = userEvent.setup();
    render(<ProviderConfigModal />);

    const select = screen.getByLabelText(/model/i);
    await user.click(select);

    const gpt4Option = screen.getByText('gpt-4');
    await user.click(gpt4Option);

    // Verify selection
    expect(screen.getByRole('option', { name: 'gpt-4', selected: true })).toBeInTheDocument();
  });

  it('handles server URL input for custom providers', async () => {
    const user = userEvent.setup();
    const customProvider = {
      ...mockStore.selectedProvider,
      id: 'ollama',
    };
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      selectedProvider: customProvider,
    } as any);

    render(<ProviderConfigModal />);

    const serverInput = screen.getByLabelText(/server url/i);
    await user.type(serverInput, 'http://localhost:11434');

    expect(serverInput).toHaveValue('http://localhost:11434');
  });

  it('disables submit button during validation', () => {
    vi.mocked(useLLMProviderStore).mockReturnValue({
      ...mockStore,
      validationInProgress: true,
    } as any);

    render(<ProviderConfigModal />);

    const submitButton = screen.getByRole('button', { name: /switch provider/i });
    expect(submitButton).toBeDisabled();
  });
});
