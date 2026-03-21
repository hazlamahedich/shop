import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Bell, AlertTriangle, CheckCheck, Clock, ChevronRight, Crown, Activity } from 'lucide-react';
import { handoffAlertsService, HandoffAlert } from '../../services/handoffAlerts';

const URGENCY_CONFIG = {
  high: {
    dot: 'bg-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.5)]',
    badge: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
    label: 'CRITICAL',
  },
  medium: {
    dot: 'bg-amber-400 shadow-[0_0_15px_rgba(251,191,36,0.5)]',
    badge: 'bg-amber-400/10 text-amber-400 border border-amber-400/20',
    label: 'ELEVATED',
  },
  low: {
    dot: 'bg-[#00f5d4] shadow-[0_0_15px_rgba(0,245,212,0.5)]',
    badge: 'bg-[#00f5d4]/10 text-[#00f5d4] border border-[#00f5d4]/20',
    label: 'STABLE',
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
      className={`group/row flex items-center gap-4 p-3 rounded-2xl transition-all duration-300 hover:bg-white/5 border border-transparent hover:border-white/10 ${
        !alert.isRead ? 'bg-[#00f5d4]/[0.03]' : ''
      }`}
    >
      <div className="flex-shrink-0 relative h-2 w-2">
        <span className={`absolute inset-0 rounded-full ${urgency.dot} z-10`} />
        {!alert.isRead && (
          <span className={`absolute inset-0 rounded-full ${urgency.dot} animate-ping opacity-50`} />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded ${urgency.badge}`}>
            {urgency.label}
          </span>
          {alert.isVip && (
            <span className="flex items-center gap-1 text-[8px] font-black text-amber-400 uppercase tracking-tighter">
              <Crown size={8} /> VIP
            </span>
          )}
        </div>
        <p className="text-[11px] font-bold text-white/70 truncate group-hover/row:text-white transition-colors">
          {alert.conversationPreview ?? 'DATA_STREAM_NULL'}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex flex-col items-end">
           <span className="text-[10px] font-black text-white/80">
              {formatWaitTime(alert.waitTimeSeconds)}
           </span>
           <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest">LATENCY</span>
        </div>
        <button
          onClick={() => onTakeOver(alert.conversationId)}
          className="h-8 w-8 flex items-center justify-center rounded-xl bg-white/5 border border-white/10 text-white/40 hover:bg-[#00f5d4] hover:text-black hover:border-transparent transition-all group/btn shadow-inner"
        >
          <ChevronRight size={14} strokeWidth={3} className="group-hover/btn:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
}

export function HandoffQueueWidget() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['handoffAlerts', 'queue'],
    queryFn: () => handoffAlertsService.getQueue({ limit: 4, sortBy: 'urgency_desc' }),
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
    <div className="relative group/widget h-full bg-white/5 rounded-[2.5rem] border border-white/10 backdrop-blur-3xl overflow-hidden shadow-2xl p-6 transition-all duration-500 hover:border-[#00f5d4]/30" data-testid="handoff-queue-widget">
      {/* HUD Accents */}
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover/widget:opacity-30 transition-opacity">
         <div className="w-12 h-12 border-t-2 border-r-2 border-[#00f5d4] rounded-tr-xl" />
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded-2xl text-[#00f5d4] shadow-[0_0_20px_rgba(0,245,212,0.1)]">
            <Bell size={18} strokeWidth={2.5} />
          </div>
          <div>
            <h3 className="text-xs font-black text-white uppercase tracking-[0.2em]">Signal Queue</h3>
            <p className="text-[10px] font-bold text-[#00f5d4]/60 uppercase tracking-widest mt-0.5">
              {isLoading ? 'SCANNING...' : `${totalWaiting} ACTIVE_SIGNALS`}
            </p>
          </div>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={() => markAllMutation.mutate()}
            className="px-3 py-1.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-[9px] font-black text-rose-400 uppercase tracking-widest hover:bg-rose-500 hover:text-white transition-all"
          >
            PURGE {unreadCount}
          </button>
        )}
      </div>

      <div className="space-y-1">
        {isLoading ? (
          [1, 2, 3].map(i => <div key={i} className="h-14 bg-white/5 rounded-2xl animate-pulse" />)
        ) : isError ? (
          <div className="py-10 text-center border border-rose-500/20 rounded-3xl bg-rose-500/5">
            <AlertTriangle size={24} className="mx-auto text-rose-500/40 mb-2" />
            <span className="text-[10px] font-black text-rose-500/60 uppercase tracking-widest">Neural Link Severed</span>
          </div>
        ) : alerts.length === 0 ? (
          <div className="py-10 text-center border border-white/5 rounded-3xl bg-white/[0.02]">
            <CheckCheck size={24} className="mx-auto text-[#00f5d4]/20 mb-2" />
            <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">Sector Optimal</span>
          </div>
        ) : (
          alerts.map(alert => <AlertRow key={alert.id} alert={alert} onTakeOver={handleTakeOver} />)
        )}
      </div>

      <button
        onClick={() => navigate('/conversations?view=handoff')}
        className="w-full mt-6 flex items-center justify-between px-5 py-3 rounded-2xl bg-white/5 border border-white/5 hover:border-[#00f5d4]/30 hover:bg-[#00f5d4]/10 transition-all group/more"
      >
        <span className="text-[10px] font-black text-white/30 group-hover/more:text-white uppercase tracking-[0.3em]">Full Topology</span>
        <Activity size={12} className="text-[#00f5d4] animate-pulse" />
      </button>
    </div>
  );
}

export default HandoffQueueWidget;
