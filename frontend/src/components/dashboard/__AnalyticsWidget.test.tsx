import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WidgetAnalyticsWidget } from './WidgetAnalyticsWidget';

const mockAnalyticsService = {
  getWidgetMetrics: jest.fn(),
  exportWidgetAnalytics: jest.fn(),
};

const mockUseQuery = jest.fn();

  .mockReturnValue({
    data: {
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
    },
  });
});

export default mockAnalyticsService;
export { mockAnalyticsService };
export { WidgetAnalyticsWidget }
export default WidgetAnalyticsWidget;
