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
      className={`group flex items-start gap-3 rounded-xl p-3 transition-colors duration-150 hover:bg-white/[0.03] ${
        !alert.isRead ? 'bg-emerald-500/[0.03]' : ''
      }`}
    >
      {/* Urgency dot */}
      <div className="mt-1.5 flex-shrink-0">
        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${urgency.dot} ring-2 ring-[#0a0a0a] shadow-[0_0_10px_rgba(0,0,0,0.5)]`}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span
            className={`text-[9px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${urgency.badge}`}
          >
            {urgency.label}
          </span>
          {alert.isVip && (
            <span className="inline-flex items-center gap-0.5 text-[9px] font-black px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20 uppercase tracking-wider">
              <Crown size={9} />
              VIP
            </span>
          )}
          {alert.handoffReason && (
            <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">
              · {alert.handoffReason.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        <p className="text-sm font-medium text-white/80 truncate">
          {alert.conversationPreview ?? 'No preview available'}
        </p>
        <div className="flex items-center gap-2 mt-0.5 text-[10px] font-bold text-white/40 uppercase tracking-wider">
          <div className="flex items-center gap-1">
            <Clock size={10} />
            <span>Waiting {formatWaitTime(alert.waitTimeSeconds)}</span>
          </div>
          {alert.customerLtv !== null && alert.customerLtv > 0 && (
            <span className="text-emerald-500/60 uppercase tracking-widest font-black">
              · ${alert.customerLtv.toFixed(0)} LTV
            </span>
          )}
        </div>
      </div>

      {/* Take Over button */}
      <button
        onClick={() => onTakeOver(alert.conversationId)}
        className="flex-shrink-0 invisible group-hover:visible flex items-center gap-0.5 rounded-lg bg-emerald-500 px-2.5 py-1 text-[9px] font-black uppercase tracking-wider text-black hover:bg-emerald-400 transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)]"
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
      className="relative overflow-hidden rounded-2xl bg-[#0a0a0a]/40 border border-white/[0.05] shadow-2xl backdrop-blur-md"
      data-testid="handoff-queue-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-emerald-500/40 via-emerald-400/20 to-transparent opacity-60" />

      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
              <Bell size={18} />
            </div>
            <div>
              <h3 className="text-sm font-black text-white uppercase tracking-widest leading-none">Handoff Queue</h3>
              <p className="text-[10px] text-white/40 font-bold uppercase tracking-widest mt-1.5 flex items-center gap-2">
                {isLoading ? 'Scanning...' : `${totalWaiting} in queue`}
                {unreadCount > 0 && (
                  <span className="flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-emerald-500 px-1 text-[8px] font-black text-black shadow-[0_0_10px_rgba(16,185,129,0.5)]">
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
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[9px] font-black text-emerald-500/40 hover:bg-emerald-500/10 hover:text-emerald-500 transition-all disabled:opacity-50 uppercase tracking-widest border border-transparent hover:border-emerald-500/20"
              aria-label="Mark all handoff alerts as read"
            >
              <CheckCheck size={13} />
              Mark Clear
            </button>
          )}
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-white/[0.02] border border-white/[0.03] animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-8 text-center bg-red-500/[0.02] border border-red-500/10 rounded-2xl">
            <AlertTriangle size={24} className="text-red-500/40 mb-3" />
            <p className="text-[10px] font-extrabold text-red-500/60 uppercase tracking-widest">Neural Link Severed</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center bg-emerald-500/[0.01] border border-white/[0.03] rounded-2xl">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/5 border border-emerald-500/20 mb-4 shadow-[0_0_20px_rgba(16,185,129,0.05)]">
              <CheckCheck size={24} className="text-emerald-500" />
            </div>
            <p className="text-xs font-black text-white uppercase tracking-[0.2em] mb-1">Grid Clear</p>
            <p className="text-[9px] font-bold text-white/30 uppercase tracking-widest">No spectral handoffs active.</p>
          </div>
        ) : (
          <div className="space-y-1">
            {alerts.map((alert) => (
              <AlertRow key={alert.id} alert={alert} onTakeOver={handleTakeOver} />
            ))}
          </div>
        )}

        {/* View all link */}
        {alerts.length > 0 && (
          <button
            onClick={() => navigate('/handoff-queue')}
            className="mt-4 w-full rounded-xl border border-white/[0.05] bg-white/[0.02] py-2.5 text-[9px] font-black text-white/30 hover:bg-emerald-500/5 hover:text-emerald-500 hover:border-emerald-500/20 transition-all uppercase tracking-[0.3em]"
          >
            Access Full Mesh →
          </button>
        )}
      </div>
    </div>
  );
}

export default HandoffQueueWidget;
