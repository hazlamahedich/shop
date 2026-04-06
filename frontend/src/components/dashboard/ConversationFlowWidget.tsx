import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
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

  const isLoading = lengthLoading || clarificationLoading || frictionLoading || sentimentLoading || handoffLoading || contextLoading;

  const currentData = (() => {
    switch (activeTab) {
      case 'overview':
        return lengthData;
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
    if (!lengthData?.has_data) {
      return <EmptyState message="No conversation data yet. Data will appear once customers start chatting." />;
    }
    const d = lengthData.data;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Turns
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avgTurns}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Median
            </div>
            <div className="text-lg font-black text-purple-400">{d.medianTurns}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              P90
            </div>
            <div className="text-lg font-black text-amber-400">{d.p90Turns}</div>
          </div>
        </div>
        {d.byMode && d.byMode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {d.byMode.map((m) => (
              <div
                key={m.mode}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{m.mode}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">
                  {m.avgTurns} avg / {m.conversationCount} convs
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
              {d.dailyTrend.slice(-14).map((day) => (
                <div
                  key={day.date}
                  className="flex-1 flex flex-col items-center gap-1"
                  title={`${day.date}: ${day.avgTurns} avg turns`}
                >
                  <div
                    className="w-full bg-[#00f5d4]/20 rounded-t"
                    style={{ height: `${Math.max(4, day.avgTurns * 10)}%` }}
                  />
                  <span className="text-[8px] text-white/20">{day.date?.slice(5)}</span>
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
      return <EmptyState message="No clarification patterns found in this period" />;
    }
    const d = clarificationData.data;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Depth
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avgClarificationDepth}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Success Rate
            </div>
            <div className="text-lg font-black text-purple-400">{d.clarificationSuccessRate}%</div>
          </div>
        </div>
        {d.topSequences && d.topSequences.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Sequences
            </div>
            {d.topSequences.map((seq) => (
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
    if (!frictionData?.has_data) {
      return <EmptyState message="No significant friction points detected" />;
    }
    const d = frictionData.data;
    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Conversations Analyzed
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.totalConversationsAnalyzed}</div>
        </div>
        {d.frictionPoints && d.frictionPoints.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Friction Points
            </div>
            {d.frictionPoints.map((fp, idx) => (
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
                <div className="text-[9px] text-white/20 uppercase">{fp.type.replace('_', ' ')}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderSentimentTab = () => {
    if (!sentimentData?.has_data) {
      return <EmptyState message="No sentiment data available for this period" />;
    }
    const d = sentimentData.data;
    return (
      <div className="space-y-3">
        {d.stages &&
          Object.entries(d.stages).map(([stage, sentiments]) => (
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
        {d.totalNegativeShifts > 0 && (
          <div className="mt-3 bg-rose-500/10 rounded-lg p-3 border border-rose-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}{d.totalNegativeShifts} negative sentiment shifts detected
            </span>
          </div>
        )}
      </div>
    );
  };

  const renderHandoffTab = () => {
    if (!handoffData?.has_data) {
      return <EmptyState message="No handoff conversations in this period" />;
    }
    const d = handoffData.data;
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Before Handoff
            </div>
            <div className="text-lg font-black text-rose-400">{d.avgHandoffLength}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Avg Resolved
            </div>
            <div className="text-lg font-black text-[#00f5d4]">{d.avgResolvedLength}</div>
          </div>
        </div>
        {d.topTriggers && d.topTriggers.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Top Handoff Triggers
            </div>
            {d.topTriggers.map((t) => (
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
        {d.handoffRatePerIntent && d.handoffRatePerIntent.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              Handoff Rate by Intent
            </div>
            {d.handoffRatePerIntent.map((h) => (
              <div key={h.intent} className="flex justify-between items-center py-1.5 px-2 border-b border-white/5">
                <span className="text-[10px] text-white/40">{h.intent}</span>
                <span className="text-[10px] font-black text-rose-400">{h.handoffRate}%</span>
              </div>
            ))}
          </div>
        )}
        {d.anonymizedExcerpts && d.anonymizedExcerpts.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-1">
              Anonymized Excerpts
            </div>
            <p className="text-[9px] text-white/20 italic">{d.privacyNote}</p>
            {d.anonymizedExcerpts.map((ex, i) => (
              <div key={i} className="py-1 px-2 border-b border-white/5">
                <span className="text-[10px] text-white/40">&quot;{ex.anonymizedMessage}&quot;</span>
                <span className="text-[10px] text-white/30 ml-2">{ex.intentDetected ?? 'N/A'}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderContextTab = () => {
    if (!contextData?.has_data) {
      return <EmptyState message="No context utilization data available" />;
    }
    const d = contextData.data;
    return (
      <div className="space-y-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
            Utilization Rate
          </div>
          <div className="text-lg font-black text-[#00f5d4]">{d.utilizationRate}%</div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              With Context
            </div>
            <div className="text-sm font-black text-purple-400">{d.turnsWithContext}</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Total Turns
            </div>
            <div className="text-sm font-black text-white/40">{d.totalTurns}</div>
          </div>
        </div>
        {d.byMode && d.byMode.length > 0 && (
          <div className="mt-3">
            <div className="text-[9px] font-black text-white/30 uppercase tracking-wider mb-2">
              By Mode
            </div>
            {d.byMode.map((m) => (
              <div
                key={m.mode}
                className="flex justify-between items-center py-1.5 px-2 border-b border-white/5"
              >
                <span className="text-[10px] text-white/40 capitalize">{m.mode}</span>
                <span className="text-[10px] font-black text-[#00f5d4]">{m.utilizationRate}%</span>
              </div>
            ))}
          </div>
        )}
        {d.improvementOpportunities > 0 && (
          <div className="mt-3 bg-amber-500/10 rounded-lg p-3 border border-amber-500/20">
            <AlertTriangle size={10} className="inline" />
            <span className="text-[10px] text-white/40">
              {' '}{d.improvementOpportunities} conversations with less than 50% context utilization
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

  return (
    <StatCard
      title="Flow Analytics"
      value={
        isLoading ? '...' : hasData ? `${lengthData?.data?.totalConversations ?? 0} convs` : 'NODES'
      }
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
