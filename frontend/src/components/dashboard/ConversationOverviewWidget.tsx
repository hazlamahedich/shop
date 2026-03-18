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
    <div className="flex justify-between items-center py-1 border-b border-white/5 last:border-0">
      <span className="text-xs text-white/40">{label}</span>
      <div className="flex items-center gap-1.5">
        <span className={`text-xs font-semibold ${color}`}>{value}</span>
        {trend !== null && trend !== undefined && (
          <span
            className={`text-[10px] font-medium flex items-center ${
              trend >= 0 ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {trend >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {Math.abs(trend).toFixed(0)}%
          </span>
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
  const total30d = convStats?.conversations?.total ?? (typeof convStats?.total === 'number' ? convStats.total : 0);
  const handoffCount = typeof convStats?.handoff === 'number' ? convStats.handoff : 0;
  const satisfactionRate =
    typeof convStats?.satisfactionRate === 'number'
      ? `${Math.round(convStats.satisfactionRate * 100)}%`
      : 'N/A';
  const momTrend = orderStats?.momComparison?.conversationsChangePercent ?? null;

  return (
    <StatCard
      title="Conversations"
      value={isLoading ? '—' : activeCount}
      subValue={`${total30d} total in last 30 days`}
      icon={<MessageSquare size={18} />}
      accentColor="green"
      isLoading={isLoading}
      trend={momTrend ?? undefined}
      data-testid="conversation-overview-widget"
    >
      <div className="space-y-0.5">
        <MiniStat
          label="Active right now"
          value={activeCount}
          color="text-emerald-400"
        />
        <MiniStat
          label="Unread handoffs"
          value={unreadCount}
          color={unreadCount > 0 ? 'text-rose-400' : 'text-white/60'}
        />
        <MiniStat
          label="Handoffs (30d)"
          value={handoffCount}
          color={handoffCount > 0 ? 'text-amber-400' : 'text-white/60'}
        />
        <MiniStat
          label="Satisfaction score"
          value={satisfactionRate}
          color="text-blue-400"
        />
      </div>
    </StatCard>
  );
}

export default ConversationOverviewWidget;
