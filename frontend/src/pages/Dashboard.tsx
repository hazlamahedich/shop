import { Store, RefreshCw, AlertTriangle, Activity, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { GlassCard } from '../components/ui/GlassCard';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { useHasStoreConnected, useAuthStore } from '../stores/authStore';
import { RetentionJobStatus } from '../components/retention/RetentionJobStatus';
import { isWidgetVisible } from '../config/dashboardWidgets';

import { HandoffQueueWidget } from '../components/dashboard/HandoffQueueWidget';
import { BotQualityWidget } from '../components/dashboard/BotQualityWidget';
import { AlertsWidget } from '../components/dashboard/AlertsWidget';
import { KnowledgeBaseWidget } from '../components/dashboard/KnowledgeBaseWidget';
import { ConversationOverviewWidget } from '../components/dashboard/ConversationOverviewWidget';
import { ConversionFunnelWidget } from '../components/dashboard/ConversionFunnelWidget';
import { PeakHoursHeatmapWidget } from '../components/dashboard/PeakHoursHeatmapWidget';
import { KnowledgeGapWidget } from '../components/dashboard/KnowledgeGapWidget';
import { TopProductsWidget } from '../components/dashboard/TopProductsWidget';
import { GeographicSnapshotWidget } from '../components/dashboard/GeographicSnapshotWidget';
import { FinancialOverviewWidget } from '../components/dashboard/FinancialOverviewWidget';
import { QualityMetricsWidget } from '../components/dashboard/QualityMetricsWidget';
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
      Updated at {label}
    </span>
  );
}

function CompactZoneHeader({ icon, title, description, colorClass }: { icon: React.ReactNode; title: string; description: string; colorClass?: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className={`w-5 h-5 rounded flex items-center justify-center ${colorClass || 'bg-white/10'}`}>
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <span className="text-[10px] text-white/40 font-normal">{description}</span>
    </div>
  );
}

const Dashboard = () => {
  const hasStoreConnected = useHasStoreConnected();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  return (
    <div className="space-y-6">
      <TutorialPrompt />

      <div data-testid="dashboard-content" className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Dashboard</h2>
            <p className="text-sm text-white/50 mt-0.5">
              {onboardingMode === 'general' 
                ? 'Your knowledge base at a glance.'
                : 'Your store at a glance — live data from Shopify.'}
            </p>
          </div>
          <div className="bg-white/5 px-3 py-1.5 rounded-lg backdrop-blur-md border border-white/10">
            <LastUpdatedBadge />
          </div>
        </div>

        {isEcommerce && !hasStoreConnected && (
          <GlassCard accent="amber" className="bg-amber-500/5 border-amber-500/20">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-amber-500/20 text-amber-500">
                <Store size={20} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-amber-500">No e-commerce store connected</p>
                <p className="text-xs text-amber-200/60 mt-0.5">
                  Revenue stats will appear once you{' '}
                  <a href="/bot-config" className="text-white hover:text-amber-400 font-bold underline">
                    connect a Shopify store
                  </a>
                  .
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        <section className="glass-card p-5 border-none shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-red-500/5 rounded-full -mr-24 -mt-24 blur-[80px]" />
          
          <CompactZoneHeader 
            icon={<AlertTriangle size={12} className="text-red-400" />}
            title="Action Required"
            description="What needs attention now"
            colorClass="bg-red-500/20"
          />
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative z-10">
            {isWidgetVisible('handoff-queue', onboardingMode) && (
              <div className="md:col-span-2" data-testid="handoff-queue-widget-container">
                <HandoffQueueWidget />
              </div>
            )}

            {isWidgetVisible('bot-quality', onboardingMode) && (
              <div data-testid="bot-quality-widget-container">
                <BotQualityWidget />
              </div>
            )}

            {isWidgetVisible('alerts', onboardingMode) && (
              <div data-testid="alerts-widget-container">
                <AlertsWidget />
              </div>
            )}

            {!isEcommerce && isWidgetVisible('knowledge-base', onboardingMode) && (
              <div className="md:col-span-2" data-testid="knowledge-base-widget-container">
                <KnowledgeBaseWidget />
              </div>
            )}
          </div>
        </section>

        <section className="glass-card p-5 border-none shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/5 rounded-full -mr-24 -mt-24 blur-[80px]" />

          <CompactZoneHeader 
            icon={<Activity size={12} className="text-blue-400" />}
            title="Business Health"
            description="Key metrics at a glance"
            colorClass="bg-blue-500/20"
          />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 relative z-10">
            {isWidgetVisible('ai-cost', onboardingMode) && (
              <div data-testid="financial-overview-widget-container">
                <FinancialOverviewWidget />
              </div>
            )}

            {isWidgetVisible('conversation-overview', onboardingMode) && (
              <div data-testid="conversation-overview-widget-container">
                <ConversationOverviewWidget />
              </div>
            )}

            {isEcommerce && isWidgetVisible('conversion-funnel', onboardingMode) && (
              <div data-testid="conversion-funnel-widget-container">
                <ConversionFunnelWidget />
              </div>
            )}
          </div>
        </section>

        <section className="glass-card p-5 border-none shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-48 h-48 bg-teal-500/5 rounded-full -mr-24 -mt-24 blur-[80px]" />

          <CompactZoneHeader 
            icon={<TrendingUp size={12} className="text-teal-400" />}
            title="Insights & Trends"
            description="Patterns and analytics"
            colorClass="bg-teal-500/20"
          />
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 relative z-10">
            {isWidgetVisible('peak-hours', onboardingMode) && (
              <div data-testid="peak-hours-heatmap-widget-container">
                <PeakHoursHeatmapWidget />
              </div>
            )}

            {isWidgetVisible('customer-sentiment', onboardingMode) && isWidgetVisible('benchmark-comparison', onboardingMode) && (
              <div data-testid="quality-metrics-widget-container">
                <QualityMetricsWidget />
              </div>
            )}

            <div data-testid="knowledge-gap-widget-container">
              <KnowledgeGapWidget />
            </div>

            {isEcommerce && isWidgetVisible('top-products', onboardingMode) && (
              <div data-testid="top-products-widget-container">
                <TopProductsWidget />
              </div>
            )}

            {isEcommerce && isWidgetVisible('geographic', onboardingMode) && (
              <div data-testid="geographic-widget-container">
                <GeographicSnapshotWidget />
              </div>
            )}
          </div>
        </section>

        <div className="pt-6">
          <RetentionJobStatus />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
