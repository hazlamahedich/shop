import { Store, RefreshCw, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { useHasStoreConnected, useAuthStore } from '../stores/authStore';
import { RetentionJobStatus } from '../components/retention/RetentionJobStatus';
import { isWidgetVisible } from '../config/dashboardWidgets';

// Dashboard widgets
import { RevenueWidget } from '../components/dashboard/RevenueWidget';
import { ConversationOverviewWidget } from '../components/dashboard/ConversationOverviewWidget';
import { HandoffQueueWidget } from '../components/dashboard/HandoffQueueWidget';
import { AICostWidget } from '../components/dashboard/AICostWidget';
import { GeographicSnapshotWidget } from '../components/dashboard/GeographicSnapshotWidget';
import { TopProductsWidget } from '../components/dashboard/TopProductsWidget';
import { PendingOrdersWidget } from '../components/dashboard/PendingOrdersWidget';
import { KnowledgeBaseWidget } from '../components/dashboard/KnowledgeBaseWidget';
import { BotQualityWidget } from '../components/dashboard/BotQualityWidget';
import { PeakHoursHeatmapWidget } from '../components/dashboard/PeakHoursHeatmapWidget';
import { ConversionFunnelWidget } from '../components/dashboard/ConversionFunnelWidget';
import { KnowledgeGapWidget } from '../components/dashboard/KnowledgeGapWidget';
import { AlertsWidget } from '../components/dashboard/AlertsWidget';
import { BenchmarkComparisonWidget } from '../components/dashboard/BenchmarkComparisonWidget';
import { CustomerSentimentWidget } from '../components/dashboard/CustomerSentimentWidget';
import { analyticsService } from '../services/analyticsService';

function LastUpdatedBadge() {
  const { dataUpdatedAt } = useQuery({ 
    queryKey: ['analytics', 'summary'], 
    queryFn: () => analyticsService.getSummary(),
    enabled: false 
  });

  const label = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'loading…';

  return (
    <span className="flex items-center gap-1.5 text-xs text-gray-400">
      <RefreshCw size={11} className="animate-spin-slow opacity-60" />
      Updated at {label} · auto-refreshes every minute
    </span>
  );
}

function ZoneHeader({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-gray-400">{icon}</span>
      <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      <span className="text-xs text-gray-400">{description}</span>
    </div>
  );
}

const Dashboard = () => {
  const hasStoreConnected = useHasStoreConnected();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  return (
    <>
      <TutorialPrompt />

      <div data-testid="dashboard-content" className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {onboardingMode === 'general' 
                ? 'Your knowledge base at a glance.'
                : 'Your store at a glance — live data from Shopify.'}
            </p>
          </div>
          <LastUpdatedBadge />
        </div>

        {/* No store warning (E-commerce mode only) */}
        {isEcommerce && !hasStoreConnected && (
          <Card>
            <div style={{ padding: 'var(--card-padding)' }}>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                  <Store size={18} />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-amber-800">No e-commerce store connected</p>
                  <p className="text-xs text-amber-700 mt-0.5">
                    Revenue and order stats will appear once you{' '}
                    <a href="/bot-config" className="underline font-medium hover:text-amber-900">
                      connect a Shopify store
                    </a>
                    .
                  </p>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* ═══════════════════════════════════════════════════════════════════
            ZONE 1: ACTION REQUIRED
            Purpose: "What needs my attention NOW?"
            Refresh: 30 seconds
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="bg-red-50/30 rounded-xl p-4 border border-red-100">
          <ZoneHeader 
            icon={<AlertTriangle size={16} />}
            title="Zone 1: Action Required"
            description="What needs my attention NOW?"
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
            {/* Handoff Queue - 2 cols */}
            {isWidgetVisible('handoff-queue', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="handoff-queue-widget-container">
                <HandoffQueueWidget />
              </div>
            )}

            {/* Bot Quality - 1 col */}
            {isEcommerce && (
              <div data-testid="bot-quality-widget-container">
                <BotQualityWidget />
              </div>
            )}

            {/* Alerts - 1 col */}
            {isEcommerce && (
              <div data-testid="alerts-widget-container">
                <AlertsWidget />
              </div>
            )}

            {/* General mode fallback: Knowledge Base */}
            {!isEcommerce && isWidgetVisible('knowledge-base', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="knowledge-base-widget-container">
                <KnowledgeBaseWidget />
              </div>
            )}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════════
            ZONE 2: BUSINESS HEALTH
            Purpose: "How is my business doing?"
            Refresh: 60 seconds
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="bg-blue-50/30 rounded-xl p-4 border border-blue-100">
          <ZoneHeader 
            icon={<Activity size={16} />}
            title="Zone 2: Business Health"
            description="How is my business doing?"
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
            {/* Revenue - 2 cols */}
            {isWidgetVisible('revenue', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="revenue-widget-container">
                <RevenueWidget />
              </div>
            )}

            {/* AI Cost - 2 cols */}
            {isWidgetVisible('ai-cost', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="ai-cost-widget-container">
                <AICostWidget />
              </div>
            )}

            {/* Conversations - 2 cols */}
            {isWidgetVisible('conversation-overview', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="conversation-overview-widget-container">
                <ConversationOverviewWidget />
              </div>
            )}

            {/* Conversion Funnel - 2 cols (E-commerce only) */}
            {isEcommerce && (
              <div className="lg:col-span-2" data-testid="conversion-funnel-widget-container">
                <ConversionFunnelWidget />
              </div>
            )}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════════
            ZONE 3: INSIGHTS & TRENDS
            Purpose: "What patterns should I know?"
            Refresh: 120 seconds
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="bg-purple-50/30 rounded-xl p-4 border border-purple-100">
          <ZoneHeader 
            icon={<TrendingUp size={16} />}
            title="Zone 3: Insights & Trends"
            description="What patterns should I know?"
          />
          
          <div className="space-y-5">
            {/* Peak Hours Heatmap - Full width (E-commerce only) */}
            {isEcommerce && (
              <div data-testid="peak-hours-heatmap-widget-container">
                <PeakHoursHeatmapWidget />
              </div>
            )}

            {/* Knowledge Gap Widget - Full width */}
            <div data-testid="knowledge-gap-widget-container">
              <KnowledgeGapWidget />
            </div>

            {/* P2 Widgets: Benchmark Comparison + Customer Sentiment */}
            {isEcommerce && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <div data-testid="benchmark-comparison-widget-container">
                  <BenchmarkComparisonWidget />
                </div>
                <div data-testid="customer-sentiment-widget-container">
                  <CustomerSentimentWidget />
                </div>
              </div>
            )}

            {/* Bottom row: Top Products + Geographic + Pending Orders (E-commerce only) */}
            {isEcommerce && (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
                {isWidgetVisible('top-products', onboardingMode) && (
                  <div className="lg:col-span-2" data-testid="top-products-widget-container">
                    <TopProductsWidget />
                  </div>
                )}

                {isWidgetVisible('geographic', onboardingMode) && (
                  <div data-testid="geographic-widget-container">
                    <GeographicSnapshotWidget />
                  </div>
                )}

                {isWidgetVisible('pending-orders', onboardingMode) && (
                  <div data-testid="pending-orders-widget-container">
                    <PendingOrdersWidget />
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* GDPR / Data Retention Status */}
        <div>
          <RetentionJobStatus />
        </div>
      </div>
    </>
  );
};

export default Dashboard;
