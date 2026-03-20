export const WIDGET_CONFIG = {
  // E-commerce only (hide in General mode)
  'revenue': { modes: ['ecommerce'] as const, name: 'Revenue' },
  'top-products': { modes: ['ecommerce'] as const, name: 'Top Products' },
  'pending-orders': { modes: ['ecommerce'] as const, name: 'Pending Orders' },
  'geographic': { modes: ['ecommerce'] as const, name: 'Geographic Snapshot' },
  'conversion-funnel': { modes: ['ecommerce'] as const, name: 'Conversion Funnel' },
  
  // General mode specific
  'knowledge-base': { modes: ['general'] as const, name: 'Knowledge Base Status' },
  'feedback-analytics': { modes: ['general'] as const, name: 'Feedback Ratings' },
  
  // Both modes (always visible)
  'conversation-overview': { modes: ['general', 'ecommerce'] as const, name: 'Conversation Overview' },
  'handoff-queue': { modes: ['general', 'ecommerce'] as const, name: 'Handoff Queue' },
  'ai-cost': { modes: ['general', 'ecommerce'] as const, name: 'AI Cost' },
  'bot-quality': { modes: ['general', 'ecommerce'] as const, name: 'Bot Quality' },
  'alerts': { modes: ['general', 'ecommerce'] as const, name: 'Alerts' },
  'peak-hours': { modes: ['general', 'ecommerce'] as const, name: 'Peak Hours' },
  'benchmark-comparison': { modes: ['general', 'ecommerce'] as const, name: 'Benchmark Comparison' },
  'customer-sentiment': { modes: ['general', 'ecommerce'] as const, name: 'Customer Sentiment' },
  'knowledge-gap': { modes: ['general', 'ecommerce'] as const, name: 'Knowledge Gap' },
  'knowledge-effectiveness': { modes: ['general'] as const, name: 'Knowledge Effectiveness' },
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
