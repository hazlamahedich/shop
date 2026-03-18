/**
 * Store tests for llmProviderStore (Story 3.4)
 *
 * Tests Zustand store functionality including:
 * - State management
 * - Action creators
 * - Provider loading
 * - Provider selection
 * - Provider switching
 * - Validation
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useLLMProviderStore } from './llmProviderStore';

// Mock the API service
vi.mock('../services/llmProvider', () => ({
  getProviders: vi.fn(),
  switchProvider: vi.fn(),
  validateProviderConfig: vi.fn(),
}));

import { getProviders, switchProvider, validateProviderConfig } from '../services/llmProvider';

const mockProvidersResponse = {
  data: {
    providers: [
      {
        id: 'openai',
        name: 'OpenAI',
        description: 'GPT-4',
        pricing: { inputCost: 5.0, outputCost: 15.0, currency: 'USD' },
        models: ['gpt-4'],
        features: ['streaming'],
        isActive: true,
      },
      {
        id: 'anthropic',
        name: 'Anthropic',
        description: 'Claude',
        pricing: { inputCost: 3.0, outputCost: 15.0, currency: 'USD' },
        models: ['claude-3'],
        features: ['streaming'],
      },
    ],
    currentProvider: {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT-4',
      model: 'gpt-4',
      status: 'active',
      configuredAt: '2024-01-01T00:00:00Z',
      totalTokensUsed: 100000,
      totalCostUsd: 12.50,
    },
  },
};

describe('llmProviderStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state to initial values
    useLLMProviderStore.setState({
      currentProvider: null,
      previousProviderId: null,
      availableProviders: [],
      isLoading: false,
      isSwitching: false,
      switchError: null,
      selectedProvider: null,
      validationInProgress: false,
    });
  });

  it('has initial state', () => {
    const { result } = renderHook(() => useLLMProviderStore());

    expect(result.current.currentProvider).toBeNull();
    expect(result.current.availableProviders).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSwitching).toBe(false);
    expect(result.current.switchError).toBeNull();
    expect(result.current.selectedProvider).toBeNull();
    expect(result.current.validationInProgress).toBe(false);
  });

  it('loads providers successfully', async () => {
    vi.mocked(getProviders).mockResolvedValue(mockProvidersResponse as any);

    const { result } = renderHook(() => useLLMProviderStore());

    await act(async () => {
      await result.current.loadProviders();
    });

    expect(result.current.currentProvider).toEqual(mockProvidersResponse.data.currentProvider);
    expect(result.current.availableProviders).toEqual(mockProvidersResponse.data.providers);
    expect(result.current.isLoading).toBe(false);
  });

  it('sets loading state during loadProviders', async () => {
    vi.mocked(getProviders).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockProvidersResponse as any), 100))
    );

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.loadProviders();
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('handles loadProviders error', async () => {
    const error = new Error('Failed to load');
    vi.mocked(getProviders).mockRejectedValue(error);

    const { result } = renderHook(() => useLLMProviderStore());

    await act(async () => {
      await result.current.loadProviders();
    });

    expect(result.current.switchError).toBe('Failed to load');
    expect(result.current.isLoading).toBe(false);
  });

  it('selects a provider for configuration', () => {
    const { result } = renderHook(() => useLLMProviderStore());

    // First load providers
    act(() => {
      result.current.availableProviders = mockProvidersResponse.data.providers;
      result.current.currentProvider = mockProvidersResponse.data.currentProvider;
    });

    act(() => {
      result.current.selectProvider('anthropic');
    });

    expect(result.current.selectedProvider).toEqual(mockProvidersResponse.data.providers[1]);
  });

  it('does not select current provider', async () => {
    vi.mocked(getProviders).mockResolvedValue(mockProvidersResponse as any);

    const { result } = renderHook(() => useLLMProviderStore());

    // Load providers to properly initialize state
    await act(async () => {
      await result.current.loadProviders();
    });

    act(() => {
      result.current.selectProvider('openai'); // Current provider
    });

    expect(result.current.selectedProvider).toBeNull();
  });

  it('closes config modal', () => {
    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.selectedProvider = mockProvidersResponse.data.providers[0];
      result.current.switchError = 'Some error';
      result.current.validationInProgress = true;
    });

    act(() => {
      result.current.closeConfigModal();
    });

    expect(result.current.selectedProvider).toBeNull();
    expect(result.current.switchError).toBeNull();
    expect(result.current.validationInProgress).toBe(false);
  });

  it('switches provider successfully', async () => {
    const mockSwitchResponse = {
      data: {
        provider: {
          id: 'anthropic',
          name: 'Anthropic',
          model: 'claude-3',
        },
        switchedAt: new Date().toISOString(),
      },
    };

    vi.mocked(switchProvider).mockResolvedValue(mockSwitchResponse as any);
    vi.mocked(getProviders).mockResolvedValue(mockProvidersResponse as any);

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.currentProvider = mockProvidersResponse.data.currentProvider;
    });

    await act(async () => {
      await result.current.switchProvider({ providerId: 'anthropic' });
    });

    expect(switchProvider).toHaveBeenCalledWith({ providerId: 'anthropic' });
    expect(result.current.isSwitching).toBe(false);
    expect(result.current.selectedProvider).toBeNull();
  });

  it('stores previousProviderId on switch', async () => {
    const mockSwitchResponse = {
      data: {
        provider: {
          id: 'anthropic',
          name: 'Anthropic',
        },
        switchedAt: new Date().toISOString(),
      },
    };

    vi.mocked(switchProvider).mockResolvedValue(mockSwitchResponse as any);
    vi.mocked(getProviders).mockResolvedValue(mockProvidersResponse as any);

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.currentProvider = mockProvidersResponse.data.currentProvider;
      result.current.previousProviderId = null;
    });

    await act(async () => {
      await result.current.switchProvider({ providerId: 'anthropic' });
    });

    expect(result.current.previousProviderId).toBe('openai');
  });

  it('handles switchProvider error', async () => {
    const error = new Error('Switch failed');
    vi.mocked(switchProvider).mockRejectedValue(error);

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.currentProvider = mockProvidersResponse.data.currentProvider;
    });

    await act(async () => {
      await expect(result.current.switchProvider({ providerId: 'anthropic' })).rejects.toThrow();
    });

    expect(result.current.isSwitching).toBe(false);
    expect(result.current.switchError).toBe('Switch failed');
  });

  it('validates provider configuration', async () => {
    const validationResult = {
      data: {
        valid: true,
        provider: {
          id: 'openai',
          name: 'OpenAI',
          testResponse: 'OK',
          latencyMs: 100,
        },
        validatedAt: new Date().toISOString(),
      },
    };

    vi.mocked(validateProviderConfig).mockResolvedValue(validationResult as any);

    const { result } = renderHook(() => useLLMProviderStore());

    let capturedResult;
    await act(async () => {
      capturedResult = await result.current.validateProvider({
        providerId: 'openai',
        apiKey: 'test-key',
      });
    });

    expect(validateProviderConfig).toHaveBeenCalledWith({
      providerId: 'openai',
      apiKey: 'test-key',
    });
    expect(capturedResult).toEqual(validationResult.data);
    expect(result.current.validationInProgress).toBe(false);
  });

  it('handles validation error', async () => {
    const error = new Error('Validation failed');
    vi.mocked(validateProviderConfig).mockRejectedValue(error);

    const { result } = renderHook(() => useLLMProviderStore());

    await act(async () => {
      await expect(
        result.current.validateProvider({ providerId: 'openai' })
      ).rejects.toThrow();
    });

    expect(result.current.validationInProgress).toBe(false);
    expect(result.current.switchError).toBe('Validation failed');
  });

  it('clears error', () => {
    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.switchError = 'Some error';
    });

    act(() => {
      result.current.clearError();
    });

    expect(result.current.switchError).toBeNull();
  });

  it('sets validationInProgress during validation', async () => {
    vi.mocked(validateProviderConfig).mockImplementation(
      () => new Promise<any>(resolve => setTimeout(() => resolve({ data: {} }), 100))
    );

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.validateProvider({ providerId: 'openai' });
    });

    expect(result.current.validationInProgress).toBe(true);

    await waitFor(() => {
      expect(result.current.validationInProgress).toBe(false);
    });
  });

  it('sets isSwitching during provider switch', async () => {
    vi.mocked(switchProvider).mockImplementation(
      () => new Promise<any>(resolve => setTimeout(() => resolve({ data: {} }), 100))
    );

    const { result } = renderHook(() => useLLMProviderStore());

    act(() => {
      result.current.switchProvider({ providerId: 'anthropic' });
    });

    expect(result.current.isSwitching).toBe(true);
    expect(result.current.validationInProgress).toBe(true);

    await waitFor(() => {
      expect(result.current.isSwitching).toBe(false);
      expect(result.current.validationInProgress).toBe(false);
    });
  });

  it('preserves provider state across hook instances', async () => {
    vi.mocked(getProviders).mockResolvedValue(mockProvidersResponse as any);

    const { result: result1 } = renderHook(() => useLLMProviderStore());

    await act(async () => {
      await result1.current.loadProviders();
    });

    // Create another hook instance
    const { result: result2 } = renderHook(() => useLLMProviderStore());

    // State should be shared
    expect(result2.current.currentProvider).toEqual(result1.current.currentProvider);
    expect(result2.current.availableProviders).toEqual(result1.current.availableProviders);
  });
});
