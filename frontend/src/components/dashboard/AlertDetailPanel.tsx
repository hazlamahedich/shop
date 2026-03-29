import React, { useEffect } from 'react';
import { X, ArrowRight, TrendingDown, Users, Cpu, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type AlertSeverity = 'critical' | 'warning' | 'info';

interface AlertDetailPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onDismiss?: () => void;
  alertId: string;
  alertType: 'handoff' | 'bot-quality' | 'conversion-drop';
  severity: AlertSeverity;
  data?: Record<string, unknown>;
  timestamp?: string;
}

const severityConfig = {
  critical: {
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
    text: 'text-rose-200',
    accent: 'rose',
    glow: 'shadow-[0_0_40px_rgba(244,63,94,0.15)]',
  },
  warning: {
    bg: 'bg-yellow-400/10',
    border: 'border-yellow-400/20',
    text: 'text-yellow-200',
    accent: 'yellow',
    glow: 'shadow-[0_0_40px_rgba(250,204,21,0.15)]',
  },
  info: {
    bg: 'bg-[#00f5d4]/10',
    border: 'border-[#00f5d4]/20',
    text: 'text-[#00f5d4]',
    accent: 'mantis',
    glow: 'shadow-[0_0_40px_rgba(0,245,212,0.15)]',
  },
};

export function AlertDetailPanel({
  isOpen,
  onClose,
  onDismiss,
  alertId,
  alertType,
  severity,
  data,
  timestamp,
}: AlertDetailPanelProps) {
  const navigate = useNavigate();
  const config = severityConfig[severity];

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const renderContent = () => {
    switch (alertType) {
      case 'handoff':
        return <HandoffAlertContent data={data} onClose={onClose} />;
      case 'bot-quality':
        return <BotQualityAlertContent data={data} onClose={onClose} />;
      case 'conversion-drop':
        return <ConversionDropContent data={data} onClose={onClose} />;
      default:
        return null;
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-full md:w-[480px] bg-[#0d0d12] border-l border-white/10 z-50
          ${config.glow} animate-in slide-in-from-right duration-300 ease-out
          flex flex-col`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`alert-title-${alertId}`}
      >
        {/* Header */}
        <div className={`flex items-center justify-between px-6 py-4 border-b ${config.border}`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${config.bg} ${config.text}`}>
              <AlertTriangle size={18} strokeWidth={2.5} />
            </div>
            <div>
              <h2
                id={`alert-title-${alertId}`}
                className={`text-sm font-black uppercase tracking-widest ${config.text}`}
              >
                {alertType === 'handoff' && 'INTERCEPT REQUIRED'}
                {alertType === 'bot-quality' && 'NEURAL LINK DEGRADED'}
                {alertType === 'conversion-drop' && 'FUNNEL LEAKAGE'}
              </h2>
              <p className="text-[10px] text-white/40 font-bold uppercase tracking-wider mt-0.5">
                {severity.toUpperCase()} PRIORITY
              </p>
              {timestamp && (
                <p className="text-[9px] text-white/30 font-medium uppercase tracking-wider flex items-center gap-1">
                  <Clock size={8} strokeWidth={2} />
                  {new Date(timestamp).toLocaleString()}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors text-white/40 hover:text-white"
            aria-label="Close panel"
          >
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {renderContent()}
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${config.border} bg-white/[0.02]`}>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20
                text-white/70 hover:text-white transition-all text-[10px] font-black uppercase tracking-widest"
            >
              <X size={12} strokeWidth={2.5} />
              Close Panel
            </button>
            {onDismiss && (
              <button
                onClick={() => {
                  onDismiss();
                  onClose();
                }}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                  bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 hover:border-rose-500/30
                  text-rose-200 hover:text-white transition-all text-[10px] font-black uppercase tracking-widest"
              >
                <CheckCircle size={12} strokeWidth={2.5} />
                Dismiss Alert
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

// ────────────────────────────────────────────────────────────────
// Alert Type Components
// ────────────────────────────────────────────────────────────────

function HandoffAlertContent({
  data,
  onClose,
}: {
  data?: Record<string, unknown>;
  onClose: () => void;
}) {
  const unreadCount = (data?.unreadCount as number) ?? 0;
  const navigate = useNavigate();

  const handleTakeToHandoff = () => {
    onClose();
    navigate('/conversations?view=handoff');
  };

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div>
        <p className="text-white/60 text-xs leading-relaxed">
          <span className="text-white font-bold">{unreadCount} customer(s)</span> are
          currently waiting for human assistance. The automated system has reached its
          resolution threshold.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-[10px] text-white/40 font-bold uppercase tracking-wider mb-1">
            Waiting Now
          </p>
          <p className="text-2xl font-black text-white">{unreadCount}</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 border border-white/10">
          <p className="text-[10px] text-white/40 font-bold uppercase tracking-wider mb-1">
            Urgency Level
          </p>
          <p className="text-2xl font-black text-rose-400">
            {unreadCount > 5 ? 'HIGH' : 'MED'}
          </p>
        </div>
      </div>

      {/* Action Steps */}
      <div className="space-y-3">
        <p className="text-[10px] text-white/40 font-black uppercase tracking-widest">
          Recommended Actions
        </p>
        <div className="space-y-2">
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Review conversation context for each waiting customer</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Respond in queue order (oldest first)</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Document resolution for knowledge base improvement</span>
          </div>
        </div>
      </div>

      {/* Primary Action */}
      <button
        onClick={handleTakeToHandoff}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg
          bg-[#00f5d4] hover:bg-[#00f5d4]/90 text-black font-black text-[11px] uppercase tracking-widest
          transition-all shadow-[0_0_20px_rgba(0,245,212,0.3)] hover:shadow-[0_0_30px_rgba(0,245,212,0.4)]"
      >
        <Users size={14} strokeWidth={2.5} />
        Access Handoff Queue
        <ArrowRight size={12} strokeWidth={2.5} />
      </button>
    </div>
  );
}

function BotQualityAlertContent({
  data,
  onClose,
}: {
  data?: Record<string, unknown>;
  onClose: () => void;
}) {
  const botQuality = data as {
    healthStatus?: string;
    avgResponseTimeSeconds?: number;
    fallbackRate?: number;
    resolutionRate?: number;
    totalConversations?: number;
  } | undefined;

  const responseTime = botQuality?.avgResponseTimeSeconds ?? 0;
  const fallbackRate = botQuality?.fallbackRate ?? 0;
  const resolutionRate = botQuality?.resolutionRate ?? 0;

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    return `${Math.round(seconds / 60)}m`;
  };

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div>
        <p className="text-white/60 text-xs leading-relaxed">
          Bot performance metrics have degraded below optimal thresholds. Response
          times are elevated and/or resolution rates have dropped.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="space-y-3">
        <p className="text-[10px] text-white/40 font-black uppercase tracking-widest">
          Current Metrics
        </p>

        <div className="bg-white/5 rounded-lg p-4 border border-white/10 space-y-3">
          <MetricRow
            label="Avg Response Time"
            value={formatTime(responseTime)}
            status={responseTime > 60 ? 'critical' : 'warning'}
          />
          <MetricRow
            label="Fallback Rate"
            value={`${(fallbackRate * 100).toFixed(1)}%`}
            status={fallbackRate > 0.3 ? 'critical' : 'warning'}
          />
          <MetricRow
            label="Resolution Rate"
            value={`${(resolutionRate * 100).toFixed(1)}%`}
            status={resolutionRate < 0.7 ? 'critical' : 'warning'}
          />
        </div>
      </div>

      {/* Action Steps */}
      <div className="space-y-3">
        <p className="text-[10px] text-white/40 font-black uppercase tracking-widest">
          Diagnostic Steps
        </p>
        <div className="space-y-2">
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Check recent conversation logs for patterns</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Review knowledge base for missing information</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Verify LLM provider connectivity and performance</span>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
        <p className="text-[10px] text-amber-200 leading-relaxed">
          <strong className="font-black">Note:</strong> This alert is based on data from the
          last 30 days. If recent improvements have been made, metrics will update
          automatically.
        </p>
      </div>
    </div>
  );
}

function ConversionDropContent({
  data,
  onClose,
}: {
  data?: Record<string, unknown>;
  onClose: () => void;
}) {
  const dropoffPercent =
    ((data as { firstStageDropoff?: number })?.firstStageDropoff ?? 0);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div>
        <p className="text-white/60 text-xs leading-relaxed">
          The first stage of your conversion funnel is showing{' '}
          <span className="text-white font-bold">
            {dropoffPercent.toFixed(0)}% drop-off
          </span>
          , which is above the healthy threshold of 30%.
        </p>
      </div>

      {/* Visual Representation */}
      <div className="bg-white/5 rounded-lg p-4 border border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] text-white/40 font-bold uppercase tracking-wider">
            First Stage Drop-off
          </span>
          <span className="text-lg font-black text-amber-400">
            {dropoffPercent.toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full"
            style={{ width: `${Math.min(dropoffPercent, 100)}%` }}
          />
        </div>
        <p className="text-[10px] text-white/40 mt-2">
          Healthy threshold: &lt;30% • Current: {dropoffPercent.toFixed(1)}%
        </p>
      </div>

      {/* Possible Causes */}
      <div className="space-y-3">
        <p className="text-[10px] text-white/40 font-black uppercase tracking-widest">
          Potential Causes
        </p>
        <div className="space-y-2">
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
            <span>Widget not loading or visible to users</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
            <span>Slow initial response times</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
            <span>Unclear call-to-action or widget placement</span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-3">
        <p className="text-[10px] text-white/40 font-black uppercase tracking-widest">
          Recommendations
        </p>
        <div className="space-y-2">
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Review widget placement on high-traffic pages</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>Check widget loading times and errors in analytics</span>
          </div>
          <div className="flex items-start gap-3 text-white/60 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] mt-1.5 flex-shrink-0" />
            <span>A/B test different widget triggers and messages</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status: 'critical' | 'warning' | 'healthy';
}) {
  const statusColors = {
    critical: 'text-rose-400',
    warning: 'text-amber-400',
    healthy: 'text-[#00f5d4]',
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-white/60">{label}</span>
      <span className={`text-sm font-black ${statusColors[status]}`}>{value}</span>
    </div>
  );
}
