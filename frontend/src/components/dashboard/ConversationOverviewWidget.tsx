import { useQuery } from '@tanstack/react-query';
import { MessageSquare } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { handoffAlertsService } from '../../services/handoffAlerts';
import { conversationsService } from '../../services/conversations';
import { StatCard } from './StatCard';

function MiniStat({
  label,
  value,
  color = 'text-gray-900',
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div className="flex justify-between items-center py-1 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className={`text-xs font-semibold ${color}`}>{value}</span>
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
  const activeCount = activeData?.activeCount ?? 0;
  const unreadCount = unreadData?.unreadCount ?? 0;
  const total30d = typeof convStats?.total === 'number' ? convStats.total : 0;
  const handoffCount = typeof convStats?.handoff === 'number' ? convStats.handoff : 0;
  const satisfactionRate =
    typeof convStats?.satisfactionRate === 'number'
      ? `${Math.round(convStats.satisfactionRate * 100)}%`
      : 'N/A';

  return (
    <StatCard
      title="Conversations"
      value={isLoading ? '—' : activeCount}
      subValue={`${total30d} total in last 30 days`}
      icon={<MessageSquare size={18} />}
      accentColor="green"
      isLoading={isLoading}
      data-testid="conversation-overview-widget"
    >
      <div className="space-y-0.5">
        <MiniStat
          label="Active right now"
          value={activeCount}
          color="text-green-700"
        />
        <MiniStat
          label="Unread handoffs"
          value={unreadCount}
          color={unreadCount > 0 ? 'text-red-600' : 'text-gray-700'}
        />
        <MiniStat
          label="Handoffs (30d)"
          value={handoffCount}
          color={handoffCount > 0 ? 'text-orange-600' : 'text-gray-700'}
        />
        <MiniStat
          label="Satisfaction score"
          value={satisfactionRate}
          color="text-blue-600"
        />
      </div>
    </StatCard>
  );
}

export default ConversationOverviewWidget;
