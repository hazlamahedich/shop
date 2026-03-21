import { useQuery } from '@tanstack/react-query';
import { MessageSquare, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { handoffAlertsService } from '../../services/handoffAlerts';
import { conversationsService } from '../../services/conversations';
import { StatCard } from './StatCard';

function MiniStat({
  label,
  value,
  color = 'text-white',
  trend,
}: {
  label: string;
  value: string | number;
  color?: string;
  trend?: number | null;
}) {
  return (
    <div className="flex justify-between items-center py-2.5 px-3 border-b border-white/5 last:border-0 group/stat hover:bg-white/5 transition-colors rounded-lg">
      <span className="text-[10px] font-black text-white/20 uppercase tracking-widest group-hover/stat:text-white/40 transition-colors">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-[11px] font-black uppercase ${color}`}>{value}</span>
        {trend !== null && trend !== undefined && (
          <div
            className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded border ${
              trend >= 0 
                ? 'text-[#00f5d4] border-[#00f5d4]/20 bg-[#00f5d4]/5' 
                : 'text-rose-400 border-rose-400/20 bg-rose-400/5'
            }`}
          >
            {trend >= 0 ? <TrendingUp size={10} strokeWidth={3} /> : <TrendingDown size={10} strokeWidth={3} />}
            <span className="text-[9px] font-black">{Math.abs(trend).toFixed(0)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function ConversationOverviewWidget() {
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsService.getSummary(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: activeData, isLoading: activeLoading } = useQuery({
    queryKey: ['conversations', 'activeCount'],
    queryFn: () => conversationsService.getActiveCount(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const { data: unreadData, isLoading: unreadLoading } = useQuery({
    queryKey: ['handoffAlerts', 'unreadCount'],
    queryFn: () => handoffAlertsService.getUnreadCount(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const isLoading = summaryLoading || activeLoading || unreadLoading;

  const convStats = summaryData?.conversationStats;
  const orderStats = summaryData?.orderStats;
  const activeCount = activeData?.activeCount ?? 0;
  const unreadCount = unreadData?.unreadCount ?? 0;
  const handoffCount = typeof convStats?.handoff === 'number' ? convStats.handoff : 0;
  const satisfactionRate =
    typeof convStats?.satisfactionRate === 'number'
      ? `${Math.round(convStats.satisfactionRate * 100)}%`
      : 'N/A';
  const momTrend = orderStats?.momComparison?.conversationsChangePercent ?? null;

  return (
    <StatCard
      title="Network Pulse"
      value={isLoading ? '...' : activeCount.toString()}
      subValue="ACTIVE_NODES"
      icon={<MessageSquare size={18} />}
      accentColor="mantis"
      isLoading={isLoading}
      trend={momTrend ?? undefined}
      data-testid="conversation-overview-widget"
    >
      <div className="space-y-1 mt-4">
        <MiniStat
          label="Realtime Convs"
          value={activeCount}
          color="text-[#00f5d4]"
        />
        <MiniStat
          label="Unread Alerts"
          value={unreadCount}
          color={unreadCount > 0 ? 'text-rose-400' : 'text-white/20'}
        />
        <MiniStat
          label="Handoff Total"
          value={handoffCount}
          color={handoffCount > 0 ? 'text-yellow-400' : 'text-white/20'}
        />
        <MiniStat
          label="Vibe Check"
          value={satisfactionRate}
          color={satisfactionRate !== 'N/A' ? 'text-purple-400' : 'text-white/20'}
        />
      </div>
      
      {/* Mantis HUD Pulse Bar */}
      <div className="mt-5 space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]">Flow_Distribution</span>
          <span className="text-[9px] font-black text-[#00f5d4] uppercase tracking-widest">Active_Mesh</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex border border-white/5 shadow-inner">
          <div className="h-full bg-gradient-to-r from-[#00f5d4] to-[#00f5d4]/40 shadow-[0_0_10px_rgba(0,245,212,0.5)]" style={{ width: '65%' }} />
          <div className="h-full bg-white/20" style={{ width: '15%' }} />
          <div className="h-full bg-rose-500/40" style={{ width: '20%' }} />
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
         <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.3em]">SIGNAL_LOCK_ACTIVE</span>
         <div className="flex gap-1">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="w-1 h-1 rounded-full bg-[#00f5d4] animate-pulse" style={{ animationDelay: `${i * 200}ms` }} />
            ))}
         </div>
      </div>
    </StatCard>
  );
}

export default ConversationOverviewWidget;
