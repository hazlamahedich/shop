import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LLMConfiguration } from './LLMConfiguration';
import { useLLMStore } from '@/stores/llmStore';

// Mock the LLM store
vi.mock('@/stores/llmStore');

describe('LLMConfiguration', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  describe('when not configured', () => {
    beforeEach(() => {
      (useLLMStore as any).mockReturnValue({
        configuration: { provider: null, status: 'idle' },
        isConfiguring: false,
        configureLLM: vi.fn(),
        testLLM: vi.fn(),
        getLLMStatus: vi.fn(),
      });
    });

    it('should render provider selection', () => {
      render(<LLMConfiguration />, { wrapper });

      expect(screen.getByText('LLM Provider Configuration')).toBeInTheDocument();
      expect(screen.getByText('Choose Provider Type')).toBeInTheDocument();
      expect(screen.getByText('Ollama (Free)')).toBeInTheDocument();
      expect(screen.getByText('Cloud Provider')).toBeInTheDocument();
    });

    it('should switch between provider types', async () => {
      render(<LLMConfiguration />, { wrapper });

      const ollamaButton = screen.getByText('Ollama (Free)').closest('button');
      const cloudButton = screen.getByText('Cloud Provider').closest('button');

      expect(ollamaButton).toHaveClass('border-indigo-500');
      expect(cloudButton).not.toHaveClass('border-indigo-500');

      // Click cloud provider
      await userEvent.click(cloudButton!);

      expect(cloudButton).toHaveClass('border-indigo-500');
      expect(ollamaButton).not.toHaveClass('border-indigo-500');
    });
  });

  describe('when configured', () => {
    beforeEach(() => {
      (useLLMStore as any).mockReturnValue({
        configuration: {
          provider: 'ollama',
          ollamaModel: 'llama3',
          status: 'active',
          configuredAt: '2026-02-03T12:00:00Z',
          lastTestAt: '2026-02-03T12:30:00Z',
          testResult: { success: true, latency_ms: 45 },
        },
        isConfiguring: false,
        configureLLM: vi.fn(),
        testLLM: vi.fn(),
        getLLMStatus: vi.fn(),
      });
    });

    it('should show configured status', () => {
      render(<LLMConfiguration />, { wrapper });

      expect(screen.getAllByText('Configured').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/ollama/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/llama3/i).length).toBeGreaterThan(0);
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should show test connection button', () => {
      render(<LLMConfiguration />, { wrapper });

      expect(screen.getByText('Test Connection')).toBeInTheDocument();
    });
  });
});
