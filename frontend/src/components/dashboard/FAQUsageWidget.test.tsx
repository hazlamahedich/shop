import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FAQUsageWidget } from './FAQUsageWidget';

vi.mock('../../services/analyticsService', () => ({
  analyticsService: {
    getFaqUsage: vi.fn(),
  },
}));

const mockFaqData = {
  faqs: [
    { id: 1, question: 'What are your hours?', clickCount: 42, conversionRate: 15.5, isUnused: false, change: { clickChange: 12 } },
    { id: 2, question: 'How do I return items?', clickCount: 28, conversionRate: 8.2, isUnused: false, change: { clickChange: -5 } },
    { id: 3, question: 'Unused FAQ', clickCount: 0, conversionRate: 0, isUnused: true, change: null },
    { id: 4, question: 'FAQ with no change data', clickCount: 15, conversionRate: 5.0, isUnused: false, change: null },
  ],
  summary: { totalClicks: 86, avgConversionRate: 7.175, unusedCount: 1 },
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        refetchOnWindowFocus: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <FAQUsageWidget />
    </QueryClientProvider>
  );
};

describe('FAQUsageWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders widget with FAQ data', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-usage-widget')).toBeInTheDocument();
      });
      expect(screen.getByText('FAQ Usage')).toBeInTheDocument();
      expect(screen.getByText('86')).toBeInTheDocument();
    });

    it('displays all FAQ items', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-item-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-item-2')).toBeInTheDocument();
      expect(screen.getByTestId('faq-item-3')).toBeInTheDocument();
    });

    it('displays summary statistics', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('total-clicks')).toBeInTheDocument();
      });
      expect(screen.getByTestId('avg-conversion')).toBeInTheDocument();
      expect(screen.getByTestId('unused-faqs')).toBeInTheDocument();
    });

    it('shows loading state initially', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockImplementation(() => new Promise(() => {}));

      createWrapper();

      expect(screen.getByText('...')).toBeInTheDocument();
    });

    it('shows empty state when no FAQs', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue({
        faqs: [],
        summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 },
      });

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-usage-empty')).toBeInTheDocument();
      });
      expect(screen.getByText('No FAQ data available yet')).toBeInTheDocument();
    });

    it('shows error state on fetch failure', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockRejectedValue(new Error('Network error'));

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-usage-error')).toBeInTheDocument();
      });
      expect(screen.getByText('SIGNAL_DECODE_ERROR')).toBeInTheDocument();
    });
  });

  describe('FAQ Item Display', () => {
    it('shows click count for each FAQ', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-clicks-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-clicks-1')).toHaveTextContent('42');
      expect(screen.getByTestId('faq-clicks-2')).toHaveTextContent('29');
    });

    it('shows conversion rate for each FAQ', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-conversion-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-conversion-1')).toHaveTextContent('15.5');
      expect(screen.getByTestId('faq-conversion-2')).toHaveTextContent('8.2');
    });

    it('shows unused warning for FAQs with 0 clicks', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('unused-faq-warning-3')).toBeInTheDocument();
      });
      expect(screen.getByText('No clicks in 30 days')).toBeInTheDocument();
    });

    it('shows trend indicators when change data exists', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-change-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-change-2')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('changes time range when selector is changed', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('time-range-selector')).toBeInTheDocument();
      });

      const selector = screen.getByTestId('time-range-selector');
      await userEvent.selectOptions(selector, '7');

      expect(analyticsService.getFaqUsage).toHaveBeenCalled();
    });

    it('triggers refresh when refresh button is clicked', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('refresh-button')).toBeInTheDocument();
      });

      const refreshButton = screen.getByTestId('refresh-button');
      await userEvent.click(refreshButton);

      expect(analyticsService.getFaqUsage).toHaveBeenCalledTimes(2);
    });
  });

  describe('Accessibility', () => {
    it('has correct test IDs for all interactive elements', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(mockFaqData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-usage-widget')).toBeInTheDocument();
      });
      expect(screen.getByTestId('time-range-selector')).toBeInTheDocument();
      expect(screen.getByTestId('refresh-button')).toBeInTheDocument();
      expect(screen.getByTestId('csv-export-button')).toBeInTheDocument();
      expect(screen.getByTestId('manage-faqs-link')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles very long FAQ questions with truncation', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      const longQuestionData = {
        faqs: [
          {
            id: 1,
            question: 'This is a very long FAQ question that should be truncated because it exceeds the normal display width and shows ellipsis at the end of the text',
            clickCount: 10,
            conversionRate: 5.0,
            isUnused: false,
            change: null,
          },
        ],
        summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 },
      };
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(longQuestionData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-item-1')).toBeInTheDocument();
      });
    });

    it('handles zero conversion rate', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      const zeroData = {
        faqs: [
          { id: 1, question: 'Test', clickCount: 10, conversionRate: 0, isUnused: false, change: null },
        ],
        summary: { totalClicks: 10, avgConversionRate: 0, unusedCount: 0 },
      };
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(zeroData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-conversion-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-conversion-1')).toHaveTextContent('0.0');
    });

    it('handles large click counts', async () => {
      const { analyticsService } = await import('../../services/analyticsService');
      const largeData = {
        faqs: [
          { id: 1, question: 'Test', clickCount: 1234567, conversionRate: 5.0, isUnused: false, change: null },
        ],
        summary: { totalClicks: 1234567, avgConversionRate: 5.0, unusedCount: 0 },
      };
      vi.mocked(analyticsService.getFaqUsage).mockResolvedValue(largeData);

      createWrapper();

      await waitFor(() => {
        expect(screen.getByTestId('faq-clicks-1')).toBeInTheDocument();
      });
      expect(screen.getByTestId('faq-clicks-1')).toHaveTextContent('1234567');
    });
  });
});
