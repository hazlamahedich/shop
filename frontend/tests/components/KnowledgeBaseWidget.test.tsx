/**
 * KnowledgeBaseWidget Component Tests
 *
 * Story 8-10: Frontend Dashboard Mode-Aware Widgets
 * Tests the Knowledge Base status widget for dashboard
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { KnowledgeBaseWidget } from '../../src/components/dashboard/KnowledgeBaseWidget';
import { knowledgeBaseApi } from '../../src/services/knowledgeBase';
import type { KnowledgeBaseStats } from '../../src/types/knowledgeBase';

// Mock the knowledge base API
vi.mock('../../src/services/knowledgeBase', () => ({
  knowledgeBaseApi: {
    getStats: vi.fn(),
  },
}));

describe('KnowledgeBaseWidget', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('should show loading state', async () => {
    vi.mocked(knowledgeBaseApi.getStats).mockImplementation(
      () => new Promise(() => {})
    );

    renderWithQueryClient(<KnowledgeBaseWidget />);

    // Check for spinner icon (animate-spin class)
    await waitFor(() => {
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  it('should show error state with retry button', async () => {
    vi.mocked(knowledgeBaseApi.getStats).mockRejectedValue(
      new Error('Failed to fetch stats')
    );

    renderWithQueryClient(<KnowledgeBaseWidget />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  it('should show empty state with upload CTA', async () => {
    const stats: KnowledgeBaseStats = {
      totalDocs: 0,
      processingCount: 0,
      readyCount: 0,
      errorCount: 0,
      lastUploadDate: null,
    };

    vi.mocked(knowledgeBaseApi.getStats).mockResolvedValue(stats);

    renderWithQueryClient(<KnowledgeBaseWidget />);

    await waitFor(() => {
      expect(screen.getByText(/knowledge base/i)).toBeInTheDocument();
      expect(screen.getByText(/upload your first document/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /upload document/i })).toBeInTheDocument();
    });
  });

  it('should show stats when data is loaded', async () => {
    const stats: KnowledgeBaseStats = {
      totalDocs: 5,
      processingCount: 1,
      readyCount: 3,
      errorCount: 1,
      lastUploadDate: '2026-03-13T10:00:00Z',
    };

    vi.mocked(knowledgeBaseApi.getStats).mockResolvedValue(stats);

    renderWithQueryClient(<KnowledgeBaseWidget />);

    await waitFor(() => {
      expect(screen.getByText(/knowledge base/i)).toBeInTheDocument();
    });

    // Check for the stats more flexibly
    const statElements = screen.getAllByText('5');
    expect(statElements.length).toBeGreaterThan(0);
    
    expect(screen.getByText(/total documents/i)).toBeInTheDocument();
  });

  it('should show manage link', async () => {
    const stats: KnowledgeBaseStats = {
      totalDocs: 2,
      processingCount: 0,
      readyCount: 2,
      errorCount: 0,
      lastUploadDate: null,
    };

    vi.mocked(knowledgeBaseApi.getStats).mockResolvedValue(stats);

    renderWithQueryClient(<KnowledgeBaseWidget />);

    await waitFor(() => {
      const manageLink = screen.getByRole('link', { name: /manage/i });
      expect(manageLink).toHaveAttribute('href', '/knowledge-base');
    });
  });
});
