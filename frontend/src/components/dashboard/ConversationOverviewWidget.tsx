import { useQuery } from '@tanstack/react-query';
import { MessageSquare, TrendingUp, TrendingDown, Clock, Activity } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { handoffAlertsService } from '../../services/handoffAlerts';
import { conversationsService } from '../../services/conversations';
import { StatCard } from './StatCard';
import { TimelineChart, PeakHoursHeatmapStrip } from '../charts/TimelineChart';

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

  // Generate mock timeline data (in real implementation, this comes from API)
  const generateTimelineData = () => {
    const now = new Date();
    const data = [];
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hour = time.getHours();
      // Simulate: more conversations during business hours (9-17)
      const isBusinessHour = hour >= 9 && hour <= 17;
      const baseValue = isBusinessHour ? activeCount * 0.8 : activeCount * 0.3;
      const variance = 0.7 + Math.random() * 0.6;
      const value = Math.round(baseValue * variance);

      data.push({
        time: time.toLocaleTimeString('en-US', { hour: 'numeric', hour12: true }),
        value,
        label: value > activeCount * 0.8 ? 'Peak' : undefined,
        color: value > activeCount * 0.8 ? '#fb923c' : undefined,
      });
    }
    return data;
  };

  // Generate mock peak hours data
  const generatePeakHoursData = () => {
    return Array.from({ length: 24 }, (_, hour) => {
      const isBusinessHour = hour >= 9 && hour <= 17;
      const baseValue = isBusinessHour ? 80 : 20;
      const variance = 0.5 + Math.random();
      return Math.round(baseValue * variance);
    });
  };

  const timelineData = generateTimelineData();
  const peakHoursData = generatePeakHoursData();

  return (
    <StatCard
      title="Network Pulse"
      value={isLoading ? '...' : activeCount.toString()}
      subValue="ACTIVE_NODES"
      icon={<MessageSquare size={18} />}
      accentColor="purple"
      isLoading={isLoading}
      trend={momTrend ?? undefined}
      data-testid="conversation-overview-widget"
      expandable
    >
      {/* Timeline Chart - 24h Conversation Volume */}
      {!isLoading && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              VOLUME_TIMELINE (24H)
            </span>
            <Activity size={12} className="text-white/20" />
          </div>
          <TimelineChart
            data={timelineData}
            height={100}
            color="#a78bfa"
            showGrid={false}
            showYAxis={false}
            margin={{ top: 5, right: 5, left: 5, bottom: 20 }}
            ariaLabel="Conversation volume over last 24 hours"
          />
        </div>
      )}

      {/* Peak Hours Heatmap Strip */}
      {!isLoading && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              PEAK_DENSITY_PATTERN
            </span>
            <Clock size={12} className="text-white/20" />
          </div>
          <PeakHoursHeatmapStrip
            data={peakHoursData}
            height={30}
          />
          <div className="flex items-center justify-between mt-1">
            <span className="text-[8px] text-white/20">00:00</span>
            <span className="text-[8px] text-white/20">12:00</span>
            <span className="text-[8px] text-white/20">23:00</span>
          </div>
        </div>
      )}

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
