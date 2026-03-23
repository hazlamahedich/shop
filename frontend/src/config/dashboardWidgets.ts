export const WIDGET_CONFIG = {
  // E-commerce only (hide in General mode)
  revenue: { modes: ['ecommerce'] as const, name: 'Revenue' },
  // 'top-products': { modes: ['ecommerce'] as const, name: 'Top Products' },
    // 'conversion-funnel': { modes: ['ecommerce'] as const, name: 'Conversion Funnel' },
    // 'pending-orders': { modes: ['ecommerce'] as const, name: 'Pending Orders' },
    // 'peak-hours': { modes: ['general', 'ecommerce'] as const, name: 'Peak Hours' },
    // 'benchmark-comparison': { modes: ['general', 'ecommerce'] as const, name: 'Benchmark Comparison' },
    // 'customer-sentiment': { modes: ['general', 'ecommerce'] as const, name: 'Customer Sentiment' },
    // 'knowledge-gap': { modes: ['general', 'ecommerce'] as const, name: 'Knowledge Gap' },
    // 'knowledge-effectiveness': { modes: ['general'] as const, name: 'Knowledge Effectiveness' },
    // 'top-topics': { modes: ['general'] as const, name: 'Top Topics' },
    // 'response-time': { modes: ['general'] as const, name: 'Response Time' },
    // 'faq-usage': { modes: ['general'] as const, name: 'FAQ Usage' },
} as const;

export type WidgetId = keyof typeof WIDGET_CONFIG;
export type OnboardingMode = 'general' | 'ecommerce';

export function isWidgetVisible(
  widgetId: WidgetId, 
  mode: OnboardingMode | undefined
): boolean {
  if (!mode) return true; // Graceful degradation - show all if mode undefined
  const config = WIDGET_CONFIG[widgetId];
  if (!config) return false;
  return (config.modes as readonly OnboardingMode[]).includes(mode);
}
