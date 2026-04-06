export const WIDGET_CONFIG = {
  // E-commerce only (hide in General mode)
  revenue: { modes: ['ecommerce'] as const, name: 'Revenue', view: 'business' as const },
  financial_overview: { modes: ['ecommerce'] as const, name: 'Financial Overview', view: 'business' as const },
  conversion_funnel: { modes: ['ecommerce'] as const, name: 'Conversion Funnel', view: 'business' as const },
  top_products: { modes: ['ecommerce'] as const, name: 'Top Products', view: 'business' as const },
  pending_orders: { modes: ['ecommerce'] as const, name: 'Pending Orders', view: 'business' as const },
  benchmark_comparison: { modes: ['ecommerce'] as const, name: 'Benchmark Comparison', view: 'business' as const },
  customer_sentiment: { modes: ['ecommerce', 'general'] as const, name: 'Customer Sentiment', view: 'business' as const },
  bot_quality: { modes: ['ecommerce', 'general'] as const, name: 'Bot Quality', view: 'business' as const },
  geographic_snapshot: { modes: ['ecommerce'] as const, name: 'Geographic Snapshot', view: 'business' as const },

  // Answer Performance widgets (E-commerce only)
  answer_quality_score: { modes: ['ecommerce'] as const, name: 'Answer Quality Score', view: 'answers' as const },
  query_performance: { modes: ['ecommerce'] as const, name: 'Query Performance', view: 'answers' as const },
  customer_feedback: { modes: ['ecommerce'] as const, name: 'Customer Feedback', view: 'answers' as const },
  top_questions: { modes: ['ecommerce'] as const, name: 'Top Questions', view: 'answers' as const },
  question_categories: { modes: ['ecommerce'] as const, name: 'Question Categories', view: 'answers' as const },
  failed_queries: { modes: ['ecommerce'] as const, name: 'Failed Queries', view: 'answers' as const },
  knowledge_base_status: { modes: ['ecommerce', 'general'] as const, name: 'Knowledge Base Status', view: 'answers' as const },
  coverage_gaps: { modes: ['ecommerce', 'general'] as const, name: 'Coverage Gaps', view: 'answers' as const },
  document_performance: { modes: ['ecommerce'] as const, name: 'Document Performance', view: 'answers' as const },
  high_impact_improvements: { modes: ['ecommerce'] as const, name: 'High-Impact Improvements', view: 'answers' as const },
  performance_alerts: { modes: ['ecommerce'] as const, name: 'Performance Alerts', view: 'answers' as const },
  quick_actions: { modes: ['ecommerce'] as const, name: 'Quick Actions', view: 'answers' as const },

  // General mode widgets
  knowledge_effectiveness: { modes: ['general'] as const, name: 'Knowledge Effectiveness', view: 'business' as const },
  top_topics: { modes: ['general'] as const, name: 'Top Topics', view: 'business' as const },
  knowledge_gap: { modes: ['general'] as const, name: 'Knowledge Gap', view: 'business' as const },
  response_time: { modes: ['general'] as const, name: 'Response Time', view: 'business' as const },
  faq_usage: { modes: ['general'] as const, name: 'FAQ Usage', view: 'business' as const },
  ai_cost: { modes: ['general'] as const, name: 'AI Cost', view: 'business' as const },
  knowledge_base: { modes: ['general'] as const, name: 'Knowledge Base', view: 'business' as const },
  alerts: { modes: ['general', 'ecommerce'] as const, name: 'Alerts', view: 'business' as const },
  handoff_queue: { modes: ['general', 'ecommerce'] as const, name: 'Handoff Queue', view: 'business' as const },
  conversation_overview: { modes: ['general', 'ecommerce'] as const, name: 'Conversation Overview', view: 'business' as const },
  conversation_flow: { modes: ['ecommerce', 'general'] as const, name: 'Conversation Flow', view: 'business' as const },
  peak_hours: { modes: ['general', 'ecommerce'] as const, name: 'Peak Hours', view: 'business' as const },
} as const;

export type WidgetId = keyof typeof WIDGET_CONFIG;
export type OnboardingMode = 'general' | 'ecommerce'
export type DashboardView = 'business' | 'answers'

export function isWidgetVisible(
  widgetId: WidgetId,
  mode: OnboardingMode | undefined,
  view?: DashboardView
): boolean {
  if (!mode) return true; // Graceful degradation - show all if mode undefined
  const config = WIDGET_CONFIG[widgetId]
  if (!config) return false

  // Check mode compatibility
  const modeMatch = (config.modes as readonly OnboardingMode[]).includes(mode)
  if (!modeMatch) return false

  // Check view compatibility (if view is specified)
  if (view && 'view' in config) {
    return config.view === view
  }

  return true
}
