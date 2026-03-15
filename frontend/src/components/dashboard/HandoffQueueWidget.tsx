import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Bell, AlertTriangle, CheckCheck, Clock, ChevronRight, Crown } from 'lucide-react';
import { handoffAlertsService, HandoffAlert } from '../../services/handoffAlerts';

const URGENCY_CONFIG = {
  high: {
    dot: 'bg-red-500',
    badge: 'bg-red-100 text-red-700 border border-red-200',
    label: 'High',
  },
  medium: {
    dot: 'bg-yellow-400',
    badge: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
    label: 'Medium',
  },
  low: {
    dot: 'bg-green-400',
    badge: 'bg-green-100 text-green-700 border border-green-200',
    label: 'Low',
  },
};

function formatWaitTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

function AlertRow({
  alert,
  onTakeOver,
}: {
  alert: HandoffAlert;
  onTakeOver: (id: number) => void;
}) {
  const urgency = URGENCY_CONFIG[alert.urgencyLevel] ?? URGENCY_CONFIG.low;
  return (
    <div
      className={`group flex items-start gap-3 rounded-xl p-3 transition-colors duration-150 hover:bg-gray-50 ${
        !alert.isRead ? 'bg-blue-50/40' : ''
      }`}
    >
      {/* Urgency dot */}
      <div className="mt-1.5 flex-shrink-0">
        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${urgency.dot} ring-2 ring-white shadow`}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span
            className={`text-[10px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${urgency.badge}`}
          >
            {urgency.label}
          </span>
          {alert.isVip && (
            <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
              <Crown size={9} />
              VIP
            </span>
          )}
          {alert.handoffReason && (
            <span className="text-[10px] text-gray-400 capitalize">
              · {alert.handoffReason.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-700 truncate">
          {alert.conversationPreview ?? 'No preview available'}
        </p>
        <div className="flex items-center gap-2 mt-0.5 text-xs text-gray-400">
          <div className="flex items-center gap-1">
            <Clock size={10} />
            <span>Waiting {formatWaitTime(alert.waitTimeSeconds)}</span>
          </div>
          {alert.customerLtv !== null && alert.customerLtv > 0 && (
            <span className="text-gray-500">
              ${alert.customerLtv.toFixed(0)} LTV
            </span>
          )}
        </div>
      </div>

      {/* Take Over button */}
      <button
        onClick={() => onTakeOver(alert.conversationId)}
        className="flex-shrink-0 invisible group-hover:visible flex items-center gap-0.5 rounded-lg bg-blue-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
        aria-label={`Take over conversation ${alert.conversationId}`}
      >
        Take Over <ChevronRight size={11} />
      </button>
    </div>
  );
}

export function HandoffQueueWidget() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['handoffAlerts', 'queue'],
    queryFn: () => handoffAlertsService.getQueue({ limit: 5, sortBy: 'urgency_desc' }),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const markAllMutation = useMutation({
    mutationFn: () => handoffAlertsService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['handoffAlerts'] });
    },
  });

  const alerts = data?.data ?? [];
  const unreadCount = data?.meta.unreadCount ?? 0;
  const totalWaiting = data?.meta.totalWaiting ?? 0;

  function handleTakeOver(conversationId: number) {
    navigate(`/conversations/${conversationId}`);
  }

  return (
    <div
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm"
      data-testid="handoff-queue-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-red-400 to-orange-300 opacity-60" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-50 text-red-600 ring-4 ring-red-100">
              <Bell size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 leading-none">Handoff Queue</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {isLoading ? '…' : `${totalWaiting} waiting`}
                {unreadCount > 0 && (
                  <span className="ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">
                    {unreadCount}
                  </span>
                )}
              </p>
            </div>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={() => markAllMutation.mutate()}
              disabled={markAllMutation.isPending}
              className="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors disabled:opacity-50"
              aria-label="Mark all handoff alerts as read"
            >
              <CheckCheck size={13} />
              Mark all read
            </button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 rounded-xl bg-gray-100 animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <AlertTriangle size={24} className="text-gray-300 mb-2" />
            <p className="text-sm text-gray-400">Could not load handoff queue.</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-50 mb-3">
              <CheckCheck size={22} className="text-green-500" />
            </div>
            <p className="text-sm font-medium text-gray-700">All clear!</p>
            <p className="text-xs text-gray-400 mt-1">No pending handoffs right now.</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} onTakeOver={handleTakeOver} />
            ))}
          </div>
        )}

        {/* View all link */}
        {alerts.length > 0 && (
          <button
            onClick={() => navigate('/handoff-queue')}
            className="mt-3 w-full rounded-xl border border-gray-100 py-2 text-xs font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-colors"
          >
            View full queue →
          </button>
        )}
      </div>
    </div>
  );
}

export default HandoffQueueWidget;
