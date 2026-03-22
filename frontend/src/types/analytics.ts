/**
 * FAQ Usage Types (Story 10-10)
 *
 * TypeScript interfaces for FAQ Usage Widget API responses.
 */

export interface FaqUsageItem {
  id: number;
  question: string;
  clickCount: number;
  conversionRate: number;
  followupCount: number;
  isUnused: boolean;
  previousPeriod: {
    clickCount: number;
    conversionRate: number;
  };
  change: {
    clickChange: number | null;
    conversionChange: number | null;
  };
}

export interface FaqUsageSummary {
  totalFaqs: number;
  totalClicks: number;
  avgConversionRate: number;
  unusedCount: number;
}

export interface FaqUsageData {
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  faqs: FaqUsageItem[];
  summary: FaqUsageSummary;
  lastUpdated: string;
}
