import { Store, RefreshCw, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { GlassCard } from '../components/ui/GlassCard';
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
import { WidgetAnalyticsWidget } from '../components/dashboard/WidgetAnalyticsWidget';
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
    <span className="flex items-center gap-1.5 text-xs text-white/40 font-medium tracking-tight">
      <RefreshCw size={11} className="animate-spin-slow text-[var(--mantis-glow)]/60" />
      Updated at {label} · auto-refreshes every minute
    </span>
  );
}

function ZoneHeader({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex items-center gap-3 mb-8">
      <div className="p-2.5 rounded-xl bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 text-[var(--mantis-glow)] shadow-[0_0_15px_rgba(34,197,94,0.1)]">
        {icon}
      </div>
      <div>
        <h3 className="text-xl font-bold text-white tracking-tight mantis-glow-text">{title}</h3>
        <p className="text-[10px] text-white/40 font-bold uppercase tracking-[0.2em]">{description}</p>
      </div>
    </div>
  );
}

const Dashboard = () => {
  const hasStoreConnected = useHasStoreConnected();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  return (
    <div className="space-y-10">
      <TutorialPrompt />

      <div data-testid="dashboard-content" className="space-y-10">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-white/5 pb-8">
          <div>
            <h2 className="text-4xl font-black text-white tracking-tight mantis-glow-text">Dashboard</h2>
            <p className="text-base text-white/60 mt-1 font-medium">
              {onboardingMode === 'general' 
                ? 'Your knowledge base at a glance.'
                : 'Your store at a glance — live data from Shopify.'}
            </p>
          </div>
          <div className="bg-white/5 px-4 py-2 rounded-xl backdrop-blur-md border border-white/10">
            <LastUpdatedBadge />
          </div>
        </div>

        {/* No store warning (E-commerce mode only) */}
        {isEcommerce && !hasStoreConnected && (
          <GlassCard accent="amber" className="bg-amber-500/5 border-amber-500/20">
            <div className="flex items-center gap-5">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-amber-500/20 text-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
                <Store size={24} />
              </div>
              <div className="flex-1">
                <p className="text-lg font-bold text-amber-500 tracking-tight">No e-commerce store connected</p>
                <p className="text-sm text-amber-200/60 mt-1 font-medium">
                  Revenue and order stats will appear once you{' '}
                  <a href="/bot-config" className="text-white hover:text-amber-400 font-bold underline decoration-amber-500/30 underline-offset-4">
                    connect a Shopify store
                  </a>
                  .
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        {/* ═══════════════════════════════════════════════════════════════════
            ZONE 1: ACTION REQUIRED
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="glass-card p-8 border-none shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full -mr-32 -mt-32 blur-[100px] transition-all duration-700 group-hover:bg-emerald-500/10" />
          
          <ZoneHeader 
            icon={<AlertTriangle size={18} />}
            title="Action Required"
            description="What needs my attention NOW?"
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 relative z-10">
            {/* Handoff Queue - 2 cols */}
            {isWidgetVisible('handoff-queue', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="handoff-queue-widget-container">
                <HandoffQueueWidget />
              </div>
            )}

            {/* Bot Quality - 1 col */}
            {isWidgetVisible('bot-quality', onboardingMode) && (
              <div data-testid="bot-quality-widget-container">
                <BotQualityWidget />
              </div>
            )}

            {/* Alerts - 1 col */}
            {isWidgetVisible('alerts', onboardingMode) && (
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
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="glass-card p-8 border-none shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-violet-500/5 rounded-full -mr-32 -mt-32 blur-[100px] transition-all duration-700 group-hover:bg-violet-500/10" />

          <ZoneHeader 
            icon={<Activity size={18} />}
            title="Business Health"
            description="How is my business doing?"
          />
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 relative z-10">
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
            {isWidgetVisible('conversion-funnel', onboardingMode) && (
              <div className="lg:col-span-2" data-testid="conversion-funnel-widget-container">
                <ConversionFunnelWidget />
              </div>
            )}
          </div>
        </section>

        {/* ═══════════════════════════════════════════════════════════════════
            ZONE 3: INSIGHTS & TRENDS
        ═══════════════════════════════════════════════════════════════════ */}
        <section className="glass-card p-8 border-none shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-teal-500/5 rounded-full -mr-32 -mt-32 blur-[100px] transition-all duration-700 group-hover:bg-teal-500/10" />

          <ZoneHeader 
            icon={<TrendingUp size={18} />}
            title="Insights & Trends"
            description="What patterns should I know?"
          />
          
          <div className="space-y-6 relative z-10">
            {/* Peak Hours Heatmap - Full width */}
            {isWidgetVisible('peak-hours', onboardingMode) && (
              <div data-testid="peak-hours-heatmap-widget-container">
                <PeakHoursHeatmapWidget />
              </div>
            )}

            {/* Knowledge Gap Widget - Full width */}
            <div data-testid="knowledge-gap-widget-container">
              <KnowledgeGapWidget />
            </div>

            {/* Widget Analytics - Full width */}
            <div data-testid="widget-analytics-widget-container">
              <WidgetAnalyticsWidget />
            </div>

            {/* P2 Widgets: Benchmark Comparison + Customer Sentiment */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {isWidgetVisible('benchmark-comparison', onboardingMode) && (
                <div data-testid="benchmark-comparison-widget-container">
                  <BenchmarkComparisonWidget />
                </div>
              )}
              {isWidgetVisible('customer-sentiment', onboardingMode) && (
                <div data-testid="customer-sentiment-widget-container">
                  <CustomerSentimentWidget />
                </div>
              )}
            </div>

            {/* Bottom row: Top Products + Geographic + Pending Orders (E-commerce only) */}
            {isEcommerce && (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
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
        <div className="pt-10">
          <RetentionJobStatus />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
