import React from 'react';
import { RefreshCw, Activity, Cpu, Layers, AlertTriangle, DollarSign, ShoppingBag, TrendingUp, Target } from 'lucide-react';
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

// NEW: Narrative flow components
import { NarrativeSection } from '../components/dashboard/NarrativeSection';
import { NarrativeFlowConnector } from '../components/dashboard/NarrativeFlowConnector';

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

const Dashboard = () => {
  const hasStoreConnected = useHasStoreConnected();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

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


        <div className="grid grid-cols-1 gap-6">
          {!isEcommerce ? (
            /* KNOWLEDGE & INTELLIGENCE STORY - Narrative Flow Layout */
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {/* ACT 1: Hero Row - "How are we performing?" */}
              <NarrativeSection
                title="How are we performing?"
                description="System health at a glance"
                icon={Activity}
                color="mantis"
              >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <KnowledgeEffectivenessWidget />
                  <AICostWidget />
                  <CustomerSentimentWidget />
                </div>
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 2: Key Insights - "What are people asking?" */}
              <NarrativeSection
                title="What are people asking?"
                description="User intent and knowledge coverage"
                icon={Cpu}
                color="purple"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TopTopicsWidget />
                  <KnowledgeBaseWidget />
                </div>
                <ConversationOverviewWidget />
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 3: Deep Analysis - "How do we improve?" */}
              <NarrativeSection
                title="How do we improve?"
                description="Identify gaps and optimization opportunities"
                icon={Layers}
                color="orange"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <KnowledgeGapWidget />
                  <ResponseTimeWidget />
                </div>
                <FAQUsageWidget />
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 4: Action Items - "What needs attention?" */}
              <NarrativeSection
                title="What needs attention?"
                description="Operational tasks and alerts"
                icon={AlertTriangle}
                color="red"
              >
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <AlertsWidget />
                  <HandoffQueueWidget />
                  <BotQualityWidget />
                </div>
              </NarrativeSection>
            </div>
          ) : (
            /* E-COMMERCE MODE - Narrative Flow Layout */
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {/* ACT 1: Business Pulse - "How's the business performing right now?" */}
              <NarrativeSection
                title="How's the business performing right now?"
                description="Business Pulse - Real-time financial health"
                icon={DollarSign}
                color="blue"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <RevenueWidget />
                  <FinancialOverviewWidget />
                </div>
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 2: Customer Journey - "What are customers doing on my store?" */}
              <NarrativeSection
                title="What are customers doing on my store?"
                description="Customer Journey - Behavior and conversion insights"
                icon={TrendingUp}
                color="purple"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ConversionFunnelWidget />
                  <TopProductsWidget />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                  <div className="md:col-span-2">
                    <ConversationOverviewWidget />
                  </div>
                  <PeakHoursHeatmapWidget />
                </div>
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 3: Action Center - "What needs my attention right now?" */}
              <NarrativeSection
                title="What needs my attention right now?"
                description="Action Center - Orders requiring immediate attention"
                icon={ShoppingBag}
                color="orange"
              >
                <div className="grid grid-cols-1 gap-6">
                  <PendingOrdersWidget />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  <HandoffQueueWidget />
                  <AlertsWidget />
                </div>
              </NarrativeSection>

              <NarrativeFlowConnector />

              {/* ACT 4: Growth Opportunities - "How can I improve and grow?" */}
              <NarrativeSection
                title="How can I improve and grow?"
                description="Growth Opportunities - Strategic improvement areas"
                icon={Target}
                color="red"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <BenchmarkComparisonWidget />
                  <CustomerSentimentWidget />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                  <BotQualityWidget />
                  <GeographicSnapshotWidget />
                </div>
              </NarrativeSection>
            </div>
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
