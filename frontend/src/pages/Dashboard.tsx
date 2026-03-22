import { useState } from 'react';
import { RefreshCw, Activity, Cpu, Layers, Store } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { GlassCard } from '../components/ui/GlassCard';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { useHasStoreConnected, useAuthStore } from '../stores/authStore';
import { RetentionJobStatus } from '../components/retention/RetentionJobStatus';

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
import { FeedbackAnalyticsWidget } from '../components/dashboard/FeedbackAnalyticsWidget';
import { KnowledgeEffectivenessWidget } from '../components/dashboard/KnowledgeEffectivenessWidget';
import { TopTopicsWidget } from '../components/dashboard/TopTopicsWidget';
import { RevenueWidget } from '../components/dashboard/RevenueWidget';
import { AICostWidget } from '../components/dashboard/AICostWidget';
import { PendingOrdersWidget } from '../components/dashboard/PendingOrdersWidget';
import { BenchmarkComparisonWidget } from '../components/dashboard/BenchmarkComparisonWidget';
import { CustomerSentimentWidget } from '../components/dashboard/CustomerSentimentWidget';
import { ResponseTimeWidget } from '../components/dashboard/ResponseTimeWidget';
import { FAQUsageWidget } from '../components/dashboard/FAQUsageWidget';
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
    <span className="flex items-center gap-1.5 text-[10px] text-white/40 font-bold uppercase tracking-widest">
      <RefreshCw size={11} className="animate-spin-slow text-[#00f5d4]/60" />
      Syncing: {label}
    </span>
  );
}

type TabType = 'live' | 'rag' | 'market';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState<TabType>('live');
  const hasStoreConnected = useHasStoreConnected();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  const tabs: { id: TabType; label: string; icon: React.ElementType }[] = [
    { id: 'live', label: 'Live Ops', icon: Activity },
    { id: 'rag', label: 'RAG Intel', icon: Cpu },
  ];

  return (
    <div className="space-y-6 min-h-screen bg-[#0d0d12]/50">
      <TutorialPrompt />

      <div data-testid="dashboard-content" className="space-y-6">
        {/* Mantis HUD Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 pb-6 border-b border-white/5 relative">
          <div className="absolute -left-6 top-1/2 -translate-y-1/2 w-1 h-12 bg-[#00f5d4] shadow-[0_0_20px_rgba(0,245,212,0.5)] rounded-r-full" />
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-black text-white tracking-tighter uppercase font-heading">
                {onboardingMode === 'general' ? 'Knowledge Hub' : 'Command Center'}
              </h2>
              <div className="px-2 py-0.5 bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded text-[10px] font-black text-[#00f5d4] tracking-widest uppercase">
                {onboardingMode === 'general' ? 'RAG HUD' : 'v2.0 HUD'}
              </div>
            </div>
            <p className="text-xs text-white/30 mt-1 font-bold uppercase tracking-widest">
              {onboardingMode === 'general' 
                ? 'System intelligence and knowledge distribution'
                : 'Real-time commerce telemetry from Shopify'}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-white/5 px-4 py-2 rounded-2xl backdrop-blur-xl border border-white/10 shadow-inner">
              <LastUpdatedBadge />
            </div>
          </div>
        </div>

        {/* High-Tech Tab Navigation - Only for Ecommerce */}
        {isEcommerce && (
          <div className="flex items-center gap-1 p-1 bg-white/5 rounded-2xl border border-white/10 w-fit backdrop-blur-md">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all duration-300 ${
                  activeTab === tab.id
                    ? 'bg-[#00f5d4] text-black shadow-[0_0_20px_rgba(0,245,212,0.3)]'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
              >
                <tab.icon size={14} strokeWidth={3} />
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {isEcommerce && !hasStoreConnected && activeTab === 'market' && (
          <GlassCard accent="mantis" className="bg-[#00f5d4]/5 border-[#00f5d4]/20 animate-pulse">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-[#00f5d4]/20 text-[#00f5d4]">
                <Store size={20} />
              </div>
              <div>
                <p className="text-sm font-black text-[#00f5d4] uppercase tracking-wide">Telemetry Locked</p>
                <p className="text-[11px] text-[#00f5d4]/50 mt-0.5 font-bold uppercase tracking-tight">
                  Connect Shopify to initialize commerce data flows.
                  <a href="/bot-config" className="ml-2 text-white hover:text-[#00f5d4] underline transition-colors">
                    Access Configuration
                  </a>
                </p>
              </div>
            </div>
          </GlassCard>
        )}

        <div className="grid grid-cols-1 gap-6">
          {!isEcommerce ? (
            /* CONSOLIDATED KNOWLEDGE HUB VIEW */
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {/* Primary Analytics & Sentiment */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-1">
                  <AICostWidget />
                </div>
                <div className="md:col-span-2">
                  <CustomerSentimentWidget />
                </div>
              </div>

              {/* RAG Core Efficiency & Base Knowledge */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="md:col-span-2">
                  <KnowledgeBaseWidget />
                </div>
                <div>
                  <KnowledgeEffectivenessWidget />
                </div>
              </div>

              {/* Gaps & Intelligence (Response metrics) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <KnowledgeGapWidget />
                <ResponseTimeWidget />
              </div>

              {/* FAQ Usage Widget */}
              <FAQUsageWidget />

              {/* Operational Status Section (within hub) */}
              <div className="pt-6 border-t border-white/5">
                <div className="flex items-center gap-2 mb-6">
                  <Activity size={14} className="text-[#00f5d4]" />
                  <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em]">Operational Pulse</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <HandoffQueueWidget />
                  <AlertsWidget />
                  <BotQualityWidget />
                </div>
              </div>
            </div>
          ) : (
            /* STANDARD COMMERCE DASHBOARD (TABBED) */
            <>
              {activeTab === 'live' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                  {/* Operational Telemetry (Top Row) */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="md:col-span-1">
                      <RevenueWidget />
                    </div>
                    <div className="md:col-span-1">
                      <AICostWidget />
                    </div>
                    <div className="md:col-span-2">
                      <PendingOrdersWidget />
                    </div>
                  </div>

                  {/* Signals & Distribution (Middle Row) */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="md:col-span-2">
                      <HandoffQueueWidget />
                    </div>
                    <div className="md:col-span-2">
                      <ConversationOverviewWidget />
                    </div>
                  </div>

                  {/* Quality & Sentiment Zone */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <BenchmarkComparisonWidget />
                    <CustomerSentimentWidget />
                    <FinancialOverviewWidget />
                  </div>

                  {/* Behavior & Analytics (E-commerce Section) */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <PeakHoursHeatmapWidget />
                    <TopProductsWidget />
                    <ConversionFunnelWidget />
                  </div>

                  {/* Geographic Distribution */}
                  <div className="grid grid-cols-1 gap-6">
                    <GeographicSnapshotWidget />
                  </div>

                  {/* Real-time Alerts & Stability (Bottom Row) */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <AlertsWidget />
                    <BotQualityWidget />
                    <QualityMetricsWidget />
                  </div>
                </div>
              )}

              {activeTab === 'rag' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                  {/* Neural Core Status */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="md:col-span-2">
                      <KnowledgeBaseWidget />
                    </div>
                    <div>
                      <KnowledgeEffectivenessWidget />
                    </div>
                  </div>

                  {/* Semantic Analysis & Gaps */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <KnowledgeGapWidget />
                    <TopTopicsWidget />
                    <FeedbackAnalyticsWidget />
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="pt-6">
          <div className="flex items-center gap-2 mb-4">
            <Layers size={14} className="text-[#00f5d4]" />
            <span className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em]">Background Processes</span>
          </div>
          <RetentionJobStatus />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
