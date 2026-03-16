export const WIDGET_CONFIG = {
  // E-commerce only (hide in General mode)
  'revenue': { modes: ['ecommerce'] as const, name: 'Revenue' },
  'top-products': { modes: ['ecommerce'] as const, name: 'Top Products' },
  'pending-orders': { modes: ['ecommerce'] as const, name: 'Pending Orders' },
  'geographic': { modes: ['ecommerce'] as const, name: 'Geographic Snapshot' },
  
  // General mode specific (new widget)
  'knowledge-base': { modes: ['general'] as const, name: 'Knowledge Base Status' },
  
  // Both modes (always visible)
  'conversation-overview': { modes: ['general', 'ecommerce'] as const, name: 'Conversation Overview' },
  'handoff-queue': { modes: ['general', 'ecommerce'] as const, name: 'Handoff Queue' },
  'ai-cost': { modes: ['general', 'ecommerce'] as const, name: 'AI Cost' },
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
