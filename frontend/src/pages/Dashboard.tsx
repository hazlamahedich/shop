import React, { useState } from 'react';
import { RefreshCw, Activity, Cpu, Layers, AlertTriangle, DollarSign, ShoppingBag, TrendingUp, Target, Brain, MessageSquare, Database, AlertCircle } from 'lucide-react';
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
import { PaymentIssuesWidget } from '../components/dashboard/PaymentIssuesWidget';
import { BenchmarkComparisonWidget } from '../components/dashboard/BenchmarkComparisonWidget';
import { CustomerSentimentWidget } from '../components/dashboard/CustomerSentimentWidget';
import { ResponseTimeWidget } from '../components/dashboard/ResponseTimeWidget';
import { FAQUsageWidget } from '../components/dashboard/FAQUsageWidget';
import { analyticsService } from '../services/analyticsService';

// Answer Performance Widgets
import { AnswerQualityScoreWidget } from '../components/dashboard/AnswerQualityScoreWidget';
import { QueryPerformanceWidget } from '../components/dashboard/QueryPerformanceWidget';
import { CustomerFeedbackWidget } from '../components/dashboard/CustomerFeedbackWidget';
import { TopQuestionsWidget } from '../components/dashboard/TopQuestionsWidget';
import { DocumentPerformanceWidget } from '../components/dashboard/DocumentPerformanceWidget';
import { HighImpactImprovementsWidget } from '../components/dashboard/HighImpactImprovementsWidget';
import { QuestionCategoriesWidget } from '../components/dashboard/QuestionCategoriesWidget';
import { FailedQueriesWidget } from '../components/dashboard/FailedQueriesWidget';
import { PerformanceAlertsWidget } from '../components/dashboard/PerformanceAlertsWidget';
import { QuickActionsWidget } from '../components/dashboard/QuickActionsWidget';
import { ConversationFlowWidget } from '../components/dashboard/ConversationFlowWidget';

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

  // State for Answer Performance view toggle (e-commerce only)
  const [activeView, setActiveView] = useState<'business' | 'answers'>('business');

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
                {onboardingMode === 'general' ? 'Knowledge Hub' : 'Store Dashboard'}
              </h2>
              <div className="px-2 py-0.5 bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded text-[10px] font-black text-[#00f5d4] tracking-widest uppercase">
                {onboardingMode === 'general' ? 'Knowledge' : 'Store'}
              </div>
            </div>
            <p className="text-xs text-white/30 mt-1 font-bold uppercase tracking-widest">
              {onboardingMode === 'general'
                ? 'System intelligence and knowledge distribution'
                : 'Real-time store data from Shopify'}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="bg-white/5 px-4 py-2 rounded-2xl backdrop-blur-xl border border-white/10 shadow-inner">
              <LastUpdatedBadge />
            </div>
          </div>
        </div>

        {/* View Toggle - E-commerce Mode Only */}
        {isEcommerce && (
          <div className="flex items-center justify-center mb-6">
            <div className="glass-panel p-1 rounded-xl flex gap-1">
              <button
                onClick={() => setActiveView('business')}
                className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                  activeView === 'business'
                    ? 'bg-[#00f5d4]/20 text-[#00f5d4] shadow-lg'
                    : 'text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                Business Metrics
              </button>
              <button
                onClick={() => setActiveView('answers')}
                className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                  activeView === 'answers'
                    ? 'bg-[#00f5d4]/20 text-[#00f5d4] shadow-lg'
                    : 'text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                Answer Performance
              </button>
            </div>
          </div>
        )}

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
                <ConversationFlowWidget />
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
                <div className="mt-6">
                  <PaymentIssuesWidget />
                </div>
              </NarrativeSection>
            </div>
          ) : (
            /* E-COMMERCE MODE - Narrative Flow Layout with Dual View */
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
              {activeView === 'business' ? (
                <>
                  {/* BUSINESS METRICS VIEW */}
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
                    <ConversationFlowWidget />
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
                    <div className="mt-6">
                      <PaymentIssuesWidget />
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
                </>
              ) : (
                <>
                  {/* ANSWER PERFORMANCE VIEW */}
                  {/* ACT 1: Intelligence Quality - "How well are we answering customer questions?" */}
                  <NarrativeSection
                    title="How well are we answering customer questions?"
                    description="Track the quality and accuracy of AI-powered responses"
                    icon={Brain}
                    color="mantis"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="md:col-span-1">
                        <AnswerQualityScoreWidget />
                      </div>
                      <div className="md:col-span-2">
                        <QueryPerformanceWidget />
                      </div>
                    </div>
                    <CustomerFeedbackWidget />
                  </NarrativeSection>

                  <NarrativeFlowConnector />

                  {/* ACT 2: Customer Intent - "What are customers asking about?" */}
                  <NarrativeSection
                    title="What are customers asking about?"
                    description="Understand customer questions and identify knowledge gaps"
                    icon={MessageSquare}
                    color="purple"
                  >
                    <TopQuestionsWidget />
                    <QuestionCategoriesWidget />
                    <FailedQueriesWidget />
                  </NarrativeSection>

                  <NarrativeFlowConnector />

                  {/* ACT 3: Knowledge Coverage - "How healthy is our knowledge base?" */}
                  <NarrativeSection
                    title="How healthy is our knowledge base?"
                    description="Monitor documentation coverage and identify gaps"
                    icon={Database}
                    color="orange"
                  >
                    <KnowledgeBaseWidget />
                    <KnowledgeGapWidget />
                    <DocumentPerformanceWidget />
                  </NarrativeSection>

                  <NarrativeFlowConnector />

                  {/* ACT 4: Action Items - "What needs improvement right now?" */}
                  <NarrativeSection
                    title="What needs improvement right now?"
                    description="Prioritized actions to boost answer quality"
                    icon={AlertCircle}
                    color="red"
                  >
                    <HighImpactImprovementsWidget />
                    <PerformanceAlertsWidget />
                    <QuickActionsWidget />
                  </NarrativeSection>
                </>
              )}
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
