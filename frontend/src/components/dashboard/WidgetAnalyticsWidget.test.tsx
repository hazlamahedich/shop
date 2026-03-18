import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WidgetAnalyticsWidget } from './WidgetAnalyticsWidget';

const mockAnalyticsService = {
  getWidgetMetrics: vi.fn(),
  exportWidgetAnalytics: vi.fn(),
};

jest.mock('../../services/analyticsService', () => mockAnalyticsService);

describe('WidgetAnalyticsWidget', () => {
  it('renders loading state initially', () => {
    render(<WidgetAnalyticsWidget />);
    
    expect(screen.getByTestId('widget-analytics-widget')).toBeInTheDocument();
  });

  it('displays metrics when data is loaded', async () => {
    const mockData = {
      metrics: {
        openRate: 25.5,
        messageRate: 10.2,
        quickReplyRate: 5.0,
        voiceInputRate: 2.3,
        proactiveConversionRate: 3.5,
        carouselEngagementRate: 1.5,
      },
      trends: {
        openRateChange: 10,
        messageRateChange: 15,
        quickReplyRateChange: -5,
        voiceInputRateChange: 3,
        proactiveConversionRateChange: 2.5,
        carouselEngagementRateChange: -1.5,
      },
      performance: {
        avgLoadTimeMs: 450,
        p95LoadTimeMs: 1200,
        bundleSizeKb: 85,
      },
    };

    mockAnalyticsService.getWidgetMetrics.mockResolvedValue(mockData);

    render(<WidgetAnalyticsWidget />);

    await screen.findByText('Open Rate').toBeInTheDocument();
    await screen.findByText('Message Rate').toBeInTheDocument();
    await screen.getByTestId('metric-card-openRate').toBeInTheDocument();
  });

  it('handles error state', () => {
    mockAnalyticsService.getWidgetMetrics.mockRejectedValue(new Error('Failed to load'));
    
    render(<WidgetAnalyticsWidget />);

    expect(screen.getByText('Failed to load analytics data')).toBeInTheDocument();
  });

  it('calls export function when export button clicked', async () => {
    const mockBlob = new Blob(['test,data'], { type: 'text/csv' });
    mockAnalyticsService.exportWidgetAnalytics.mockResolvedValue(mockBlob);

    render(<WidgetAnalyticsWidget />);

    const exportButton = screen.getByRole('button', { name: /Export/i });
    await userEvent.click(exportButton);

    expect(mockAnalyticsService.exportWidgetAnalytics).toHaveBeenCalledWith(
      expect.anyMatchingDate(/2024-03-17/),
      expect.anyMatchingDate(/2026-03-17/)
    );
  });
});
