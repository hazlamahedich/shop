import { useState } from 'react';
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ApiData = any;

function getNestedData(raw: ApiData): ApiData {
  if (!raw) return null;
  if (raw.data && typeof raw.data === 'object') return raw.data;
  const rest: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(raw)) {
    if (k !== 'has_data' && k !== 'message') rest[k] = v;
  }
  if (raw.has_data === true && Object.keys(rest).length > 0) return rest;
  return raw.data ?? null;
}

function getTotalConversations(raw: ApiData): number {
  if (!raw) return 0;
  if (raw.total_conversations != null) return raw.total_conversations;
  if (raw.data?.totalConversations != null) return raw.data.totalConversations;
  if (raw.data?.total_conversations != null) return raw.data.total_conversations;
  return 0;
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-white/30">
      <Activity size={24} className="mb-2 opacity-30" />
      <p className="text-xs text-white/40">{message}</p>
    </div>
  );
}

export function ConversationFlowWidget() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

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
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: clarificationData, isLoading: clarificationLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'clarification-patterns'],
    queryFn: () => analyticsService.getConversationFlowClarificationPatterns(),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: frictionData, isLoading: frictionLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'friction-points'],
    queryFn: () => analyticsService.getConversationFlowFrictionPoints(),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: sentimentData, isLoading: sentimentLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'sentiment-stages'],
    queryFn: () => analyticsService.getConversationFlowSentimentStages(),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: handoffData, isLoading: handoffLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'handoff-correlation'],
    queryFn: () => analyticsService.getConversationFlowHandoffCorrelation(),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const { data: contextData, isLoading: contextLoading } = useQuery({
    queryKey: ['analytics', 'conversation-flow', 'context-utilization'],
    queryFn: () => analyticsService.getConversationFlowContextUtilization(),
    refetchInterval: 600_000,
    staleTime: 300_000,
  });

  const isLoading =
    overviewLoading || lengthLoading || clarificationLoading || frictionLoading || sentimentLoading || handoffLoading || contextLoading;

  const currentData = (() => {
    switch (activeTab) {
      case 'overview':
        return overviewData?.has_data ? overviewData : lengthData;
      case 'clarification':
        return clarificationData;
      case 'friction':
        return frictionData;
      case 'sentiment':
        return sentimentData;
      case 'handoff':
        return handoffData;
      case 'context':
        return contextData;
      default:
        return lengthData;
    }
  })();

  const hasData = currentData?.has_data === true;

  const renderOverviewTab = () => {
    const raw = overviewData?.has_data ? overviewData : lengthData;
    if (!raw?.has_data) {
      return <EmptyState message="No conversation data available" />;
    }
    const d = getNestedData(raw);
    if (!d) return <EmptyState message="No conversation data available" />;

    const avgTurns = d.avgTurns ?? d.average_turns ?? d.avgTurnsByMode?.[0]?.avgTurns ?? '—';
    const p90Turns = d.p90Turns ?? d.p90_turns ?? '—';
    const totalConversations = d.totalConversations ?? d.total_conversations ?? 0;

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
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              P90
            </div>
            <div className="text-lg font-black text-amber-400">{p90Turns}</div>
          </div>
        </div>
        {d.completion_rate != null && (
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Completion Rate
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{Math.round((d.completion_rate ?? d.completionRate ?? 0) * 100)}%</div>
          </div>
        )}
        {d.byMode && d.byMode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {(d.byMode as Array<Record<string, any>>).map((m: Record<string, any>) => (
              <div
                key={String(m.mode)}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{String(m.mode)}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">
                  {m.avgTurns ?? m.average_turns} avg / {m.conversationCount ?? m.conversation_count} convs
                </span>
              </div>
            ))}
          </div>
        )}
        {d.dailyTrend && d.dailyTrend.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Daily Trend
            </div>
            <div className="h-16 flex items-end gap-[2px]">
              {(d.dailyTrend as Array<Record<string, any>>).slice(-14).map((day: Record<string, any>) => (
                <div
                  key={String(day.date)}
                  className="flex-1 flex flex-col items-center gap-1"
                  title={`${day.date}: ${day.avgTurns ?? day.average_turns} avg turns`}
                >
                  <div
                    className="w-full bg-[#00f5d4]/20 rounded-t"
                    style={{ height: `${Math.max(4, (day.avgTurns ?? day.average_turns ?? 0) * 10)}%` }}
                  />
                  <span className="text-[8px] text-white/20">{String(day.date ?? '').slice(5)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderClarificationTab = () => {
    if (!clarificationData?.has_data) {
      return <EmptyState message="No data available" />;
    }
    const d = getNestedData(clarificationData);
    if (!d) return <EmptyState message="No data available" />;

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Depth
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avgClarificationDepth ?? d.avg_clarification_depth}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Success Rate
            </div>
            <div className="text-lg font-black text-purple-400">{d.clarificationSuccessRate ?? d.clarification_success_rate}%</div>
          </div>
        </div>
        {d.topSequences && d.topSequences.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Sequences
            </div>
            {(d.topSequences as Array<Record<string, any>>).map((seq: Record<string, any>) => (
              <div
                key={String(seq.sequence)}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40">{String(seq.sequence)}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">{seq.count}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderFrictionTab = () => {
    if (!frictionData?.has_data) {
      return <EmptyState message="No data available" />;
    }
    const d = getNestedData(frictionData);
    if (!d) return <EmptyState message="No data available" />;

    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Friction
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.totalConversationsAnalyzed ?? d.total_conversations_analyzed}</div>
        </div>
        {d.frictionPoints && d.frictionPoints.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Friction Points
            </div>
            {(d.frictionPoints as Array<Record<string, any>>).map((fp: Record<string, any>, idx: number) => (
              <div key={idx} className="space-y-1 py-2 px-3 border border-white/5 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-white/40">{fp.intent}</span>
                  <span className="text-[9px] font-black text-amber-400">{fp.frequency}</span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-500/30 rounded"
                    style={{ width: `${Math.min(100, (fp.frequency ?? 0) * 20)}%` }}
                  />
                </div>
                <div className="text-[9px] text-white/20 uppercase">{String(fp.type ?? '').replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderSentimentTab = () => {
    if (!sentimentData?.has_data) {
      return <EmptyState message="No data available" />;
    }
    const d = getNestedData(sentimentData);
    if (!d) return <EmptyState message="No data available" />;

    return (
      <div className="space-y-3">
        {d.stages &&
          Object.entries(d.stages as Record<string, Record<string, number>>).map(([stage, sentiments]) => (
            <div key={stage} className="space-y-2">
              <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
                {stage}
              </div>
              <div className="space-y-1">
                {Object.entries(sentiments).map(([sentiment, count]) => (
                  <div key={sentiment} className="flex justify-between items-center py-1 px-2">
                    <span className="text-[10px] text-white/40 capitalize">{sentiment}</span>
                    <span className="text-[10px] font-black text-purple-400">{String(count)}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        {(d.totalNegativeShifts ?? d.total_negative_shifts ?? 0) > 0 && (
          <div className="mt-3 bg-rose-500/10 rounded-lg p-3 border border-rose-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}{d.totalNegativeShifts ?? d.total_negative_shifts} negative sentiment shifts detected
            </span>
          </div>
        )}
      </div>
    );
  };

  const renderHandoffTab = () => {
    if (!handoffData?.has_data) {
      return <EmptyState message="No data available" />;
    }
    const d = getNestedData(handoffData);
    if (!d) return <EmptyState message="No data available" />;

    return (
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Before Handoff
            </div>
            <div className="text-lg font-black text-rose-400">{d.avgHandoffLength ?? d.avg_handoff_length}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Resolved
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avgResolvedLength ?? d.avg_resolved_length}</div>
          </div>
        </div>
        {d.topTriggers && d.topTriggers.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Handoff Triggers
            </div>
            {(d.topTriggers as Array<Record<string, any>>).map((t: Record<string, any>) => (
              <div
                key={String(t.intent)}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40">{t.intent}</span>
                <span className="text-[10px] font-black text-amber-400">{t.count}</span>
              </div>
            ))}
          </div>
        )}
        {d.handoffRatePerIntent && d.handoffRatePerIntent.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Handoff Rate by Intent
            </div>
            {(d.handoffRatePerIntent as Array<Record<string, any>>).map((h: Record<string, any>) => (
              <div key={String(h.intent)} className="flex justify-between items-center py-1.5 px-2 border-b border-white/5">
                <span className="text-[10px] text-white/40">{h.intent}</span>
                <span className="text-[10px] font-black text-rose-400">{h.handoffRate ?? h.handoff_rate}%</span>
              </div>
            ))}
          </div>
        )}
        {d.anonymizedExcerpts && d.anonymizedExcerpts.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-1">
              Anonymized Excerpts
            </div>
            <p className="text-[9px] text-white/20 italic">{d.privacyNote ?? d.privacy_note}</p>
            {(d.anonymizedExcerpts as Array<Record<string, any>>).map((ex: Record<string, any>, i: number) => (
              <div key={i} className="py-1 px-2 border-b border-white/5">
                <span className="text-[10px] text-white/40">&quot;{ex.anonymizedMessage ?? ex.anonymized_message}&quot;</span>
                <span className="text-[10px] text-white/30 ml-2">{ex.intentDetected ?? ex.intent_detected ?? 'N/A'}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderContextTab = () => {
    if (!contextData?.has_data) {
      return <EmptyState message="No data available" />;
    }
    const d = getNestedData(contextData);
    if (!d) return <EmptyState message="No data available" />;

    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Utilization Rate
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.utilizationRate ?? d.utilization_rate}%</div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              With Context
            </div>
            <div className="text-sm font-black text-purple-400">{d.turnsWithContext ?? d.turns_with_context}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Total Turns
            </div>
            <div className="text-sm font-black text-white/40">{d.totalTurns ?? d.total_turns}</div>
          </div>
        </div>
        {d.byMode && d.byMode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {(d.byMode as Array<Record<string, any>>).map((m: Record<string, any>) => (
              <div
                key={String(m.mode)}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{String(m.mode)}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">{m.utilizationRate ?? m.utilization_rate}%</span>
              </div>
            ))}
          </div>
        )}
        {(d.improvementOpportunities ?? d.improvement_opportunities ?? 0) > 0 && (
          <div className="mt-3 bg-amber-500/10 rounded-lg p-3 border border-amber-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}{d.improvementOpportunities ?? d.improvement_opportunities} conversations with less than 50% context utilization
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

  const displayTotal = getTotalConversations(overviewData) || getTotalConversations(lengthData);

  return (
    <StatCard
      title="Flow Analytics"
      value={isLoading ? '...' : hasData ? `${displayTotal} convs` : '—'}
      subValue="CONVERSATION_FLOW"
      icon={<Activity size={18} />}
      accentColor="purple"
      isLoading={isLoading}
      expandable
      data-testid="conversation-flow-widget"
    >
      <div className="flex gap-2 mb-3 border-b border-white/5">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
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
