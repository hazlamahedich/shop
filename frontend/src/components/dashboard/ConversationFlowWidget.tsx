import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  MessageSquare,
  GitBranch,
  HelpCircle,
  Layers,
} from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import type {
  ConversationFlowOverviewData,
  ConversationFlowLengthDistributionData,
  ConversationFlowClarificationData,
  ConversationFlowFrictionData,
  ConversationFlowSentimentData,
  ConversationFlowHandoffData,
  ConversationFlowContextData,
} from '../../types/analytics';
import { StatCard } from './StatCard';

type TabId = 'overview' | 'clarification' | 'friction' | 'sentiment' | 'handoff' | 'context';

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'overview', label: 'Overview', icon: <Activity size={14} /> },
  { id: 'clarification', label: 'Clarification', icon: <HelpCircle size={14} /> },
  { id: 'friction', label: 'Friction', icon: <AlertTriangle size={14} /> },
  { id: 'sentiment', label: 'Sentiment', icon: <MessageSquare size={14} /> },
  { id: 'handoff', label: 'Handoff', icon: <GitBranch size={14} /> },
  { id: 'context', label: 'Context', icon: <Layers size={14} /> },
];

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-white/30">
      <Activity size={24} className="mb-2 opacity-30" />
      <p className="text-xs text-white/40">{message}</p>
    </div>
  );
}

const VISITED_TABS_KEY = 'conversation-flow-visited-tabs';

function useVisitedTabs() {
  const [visited, setVisited] = useState<Set<TabId>>(() => {
    try {
      const stored = localStorage.getItem(VISITED_TABS_KEY);
      return stored ? new Set<TabId>(JSON.parse(stored) as TabId[]) : new Set<TabId>(['overview']);
    } catch {
      return new Set<TabId>(['overview']);
    }
  });

  const markVisited = (tab: TabId) => {
    setVisited((prev) => {
      const next = new Set(prev);
      next.add(tab);
      try {
        localStorage.setItem(VISITED_TABS_KEY, JSON.stringify([...next]));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  };

  return { visited, markVisited };
}

export function ConversationFlowWidget() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { visited, markVisited } = useVisitedTabs();

  const { data: overviewData, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'overview'],
    queryFn: () => analyticsService.getConversationFlowOverview(),
    refetchInterval: 600_000,
    staleTime: 300_000,
    retry: false,
  });

  const { data: lengthData, isLoading: lengthLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'length-distribution'],
    queryFn: () => analyticsService.getConversationFlowLengthDistribution(),
    enabled: visited.has('overview'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: clarificationData, isLoading: clarificationLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'clarification-patterns'],
    queryFn: () => analyticsService.getConversationFlowClarificationPatterns(),
    enabled: visited.has('clarification'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: frictionData, isLoading: frictionLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'friction-points'],
    queryFn: () => analyticsService.getConversationFlowFrictionPoints(),
    enabled: visited.has('friction'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: sentimentData, isLoading: sentimentLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'sentiment-stages'],
    queryFn: () => analyticsService.getConversationFlowSentimentStages(),
    enabled: visited.has('sentiment'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: handoffData, isLoading: handoffLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'handoff-correlation'],
    queryFn: () => analyticsService.getConversationFlowHandoffCorrelation(),
    enabled: visited.has('handoff'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: contextData, isLoading: contextLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'context-utilization'],
    queryFn: () => analyticsService.getConversationFlowContextUtilization(),
    enabled: visited.has('context'),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    markVisited(tab);
  };

  const tabLoading = useMemo(() => {
    switch (activeTab) {
      case 'overview':
        return overviewLoading || (visited.has('overview') && lengthLoading);
      case 'clarification':
        return clarificationLoading;
      case 'friction':
        return frictionLoading;
      case 'sentiment':
        return sentimentLoading;
      case 'handoff':
        return handoffLoading;
      case 'context':
        return contextLoading;
    }
  }, [
    activeTab,
    overviewLoading,
    lengthLoading,
    clarificationLoading,
    frictionLoading,
    sentimentLoading,
    handoffLoading,
    contextLoading,
    visited,
  ]);

  const renderOverviewTab = () => {
    const overview = overviewData?.has_data ? overviewData.data : lengthData?.data;
    if (!overview) {
      return <EmptyState message="No conversation data available" />;
    }
    const d: ConversationFlowOverviewData | ConversationFlowLengthDistributionData = overview;

    const avgTurns = 'avg_turns' in d ? d.avg_turns : 'average_turns' in d ? d.average_turns : '—';
    const p90Turns = 'p90_turns' in d ? d.p90_turns : '—';

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Turns
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{avgTurns}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">P90</div>
            <div className="text-lg font-black text-amber-400">{p90Turns}</div>
          </div>
        </div>
        {'completion_rate' in d && d.completion_rate != null && (
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Completion Rate
            </div>
            <div className="text-lg font-black text-[#00f5d4]">
              {Math.round(d.completion_rate * 100)}%
            </div>
          </div>
        )}
        {d.by_mode && d.by_mode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {d.by_mode.map((m) => (
              <div
                key={m.mode}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{m.mode}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">
                  {m.avg_turns} avg / {m.conversation_count} convs
                </span>
              </div>
            ))}
          </div>
        )}
        {d.daily_trend && d.daily_trend.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Daily Trend
            </div>
            <div className="h-16 flex items-end gap-[2px]">
              {d.daily_trend.slice(-14).map((day) => (
                <div
                  key={day.date}
                  className="flex-1 flex flex-col items-center gap-1"
                  title={`${day.date}: ${day.avg_turns} avg turns`}
                >
                  <div
                    className="w-full bg-[#00f5d4]/20 rounded-t"
                    style={{ height: `${Math.max(4, day.avg_turns * 10)}%` }}
                  />
                  <span className="text-[8px] text-white/20">{day.date.slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderClarificationTab = () => {
    if (!clarificationData?.has_data || !clarificationData.data) {
      return <EmptyState message="No data available" />;
    }
    const d: ConversationFlowClarificationData = clarificationData.data;

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Depth
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avg_clarification_depth}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Success Rate
            </div>
            <div className="text-lg font-black text-purple-400">
              {d.clarification_success_rate}%
            </div>
          </div>
        </div>
        {d.top_sequences.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Sequences
            </div>
            {d.top_sequences.map((seq) => (
              <div
                key={seq.sequence}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40">{seq.sequence}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">{seq.count}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderFrictionTab = () => {
    if (!frictionData?.has_data || !frictionData.data) {
      return <EmptyState message="No data available" />;
    }
    const d: ConversationFlowFrictionData = frictionData.data;

    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Friction
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.total_conversations_analyzed}</div>
        </div>
        {d.friction_points.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Friction Points
            </div>
            {d.friction_points.map((fp, idx) => (
              <div key={idx} className="space-y-1 py-2 px-3 border border-white/5 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-white/40">{fp.intent}</span>
                  <span className="text-[9px] font-black text-amber-400">{fp.frequency}</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500/30 rounded"
                    style={{ width: `${Math.min(100, fp.frequency * 20)}%` }}
                  />
                </div>
                <div className="text-[9px] text-white/20 uppercase">
                  {fp.type.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderSentimentTab = () => {
    if (!sentimentData?.has_data || !sentimentData.data) {
      return <EmptyState message="No data available" />;
    }
    const d: ConversationFlowSentimentData = sentimentData.data;

    return (
      <div className="space-y-3">
        {Object.entries(d.stages).map(([stage, sentiments]) => (
          <div key={stage} className="space-y-2">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              {stage}
            </div>
            <div className="space-y-1">
              {Object.entries(sentiments).map(([sentiment, count]) => (
                <div key={sentiment} className="flex justify-between items-center py-1 px-2">
                  <span className="text-[10px] text-white/40 capitalize">{sentiment}</span>
                  <span className="text-[10px] font-black text-purple-400">{count}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {d.total_negative_shifts > 0 && (
          <div className="mt-3 bg-rose-500/10 rounded-lg p-3 border border-rose-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}
              {d.total_negative_shifts} negative sentiment shifts detected
            </span>
          </div>
        )}
      </div>
    );
  };

  const renderHandoffTab = () => {
    if (!handoffData?.has_data || !handoffData.data) {
      return <EmptyState message="No data available" />;
    }
    const d: ConversationFlowHandoffData = handoffData.data;

    return (
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Before Handoff
            </div>
            <div className="text-lg font-black text-rose-400">{d.avg_handoff_length}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Resolved
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avg_resolved_length}</div>
          </div>
        </div>
        {d.top_triggers.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Handoff Triggers
            </div>
            {d.top_triggers.map((t) => (
              <div
                key={t.intent}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40">{t.intent}</span>
                <span className="text-[10px] font-black text-amber-400">{t.count}</span>
              </div>
            ))}
          </div>
        )}
        {d.handoff_rate_per_intent.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Handoff Rate by Intent
            </div>
            {d.handoff_rate_per_intent.map((h) => (
              <div
                key={h.intent}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40">{h.intent}</span>
                <span className="text-[10px] font-black text-rose-400">{h.handoff_rate}%</span>
              </div>
            ))}
          </div>
        )}
        {d.anonymized_excerpts.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-1">
              Anonymized Excerpts
            </div>
            <p className="text-[9px] text-white/20 italic">{d.privacy_note}</p>
            {d.anonymized_excerpts.map((ex, i) => (
              <div key={i} className="py-1 px-2 border-b border-white/5">
                <span className="text-[10px] text-white/40">
                  &quot;{ex.anonymized_message}&quot;
                </span>
                <span className="text-[10px] text-white/30 ml-2">{ex.intent_detected}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderContextTab = () => {
    if (!contextData?.has_data || !contextData.data) {
      return <EmptyState message="No data available" />;
    }
    const d: ConversationFlowContextData = contextData.data;

    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Utilization Rate
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.utilization_rate}%</div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              With Context
            </div>
            <div className="text-sm font-black text-purple-400">{d.turns_with_context}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Total Turns
            </div>
            <div className="text-sm font-black text-white/40">{d.total_turns}</div>
          </div>
        </div>
        {d.by_mode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {d.by_mode.map((m) => (
              <div
                key={m.mode}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{m.mode}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">{m.utilization_rate}%</span>
              </div>
            ))}
          </div>
        )}
        {d.improvement_opportunities > 0 && (
          <div className="mt-3 bg-amber-500/10 rounded-lg p-3 border border-amber-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}
              {d.improvement_opportunities} conversations with less than 50% context utilization
            </span>
          </div>
        )}
      </div>
    );
  };

  const renderTab = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverviewTab();
      case 'clarification':
        return renderClarificationTab();
      case 'friction':
        return renderFrictionTab();
      case 'sentiment':
        return renderSentimentTab();
      case 'handoff':
        return renderHandoffTab();
      case 'context':
        return renderContextTab();
    }
  };

  const displayTotal =
    overviewData?.data?.total_conversations ?? lengthData?.data?.total_conversations ?? 0;

  return (
    <StatCard
      title="Flow Analytics"
      value={tabLoading ? '...' : displayTotal > 0 ? `${displayTotal} convs` : '—'}
      subValue="CONVERSATION_FLOW"
      icon={<Activity size={18} />}
      accentColor="purple"
      isLoading={tabLoading}
      expandable
      data-testid="conversation-flow-widget"
    >
      <div className="flex gap-2 mb-3 border-b border-white/5">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] transition-colors ${
              activeTab === tab.id
                ? 'text-[#00f5d4] bg-[#00f5d4]/10 border border-[#00f5d4]/20'
                : 'text-white/30 hover:bg-white/5'
            }`}
          >
            {tab.icon}
            <span className="text-[9px] font-black uppercase tracking-wider">{tab.label}</span>
          </button>
        ))}
      </div>
      <div className="mt-3">{renderTab()}</div>
    </StatCard>
  );
}

export default ConversationFlowWidget;
