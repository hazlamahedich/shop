import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, ArrowRight, Users, TrendingDown, Cpu } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { handoffAlertsService } from '../../services/handoffAlerts';
import { StatCard } from './StatCard';
import { Link } from 'react-router-dom';

type AlertSeverity = 'critical' | 'warning' | 'info';

interface AlertItem {
  id: string;
  severity: AlertSeverity;
  message: string;
  action?: {
    label: string;
    href: string;
  };
  icon: React.ReactNode;
}

function AlertRow({ alert }: { alert: AlertItem }) {
  const severityStyles = {
    critical: 'bg-rose-500/10 border-rose-500/20 text-rose-200 shadow-[0_0_20px_rgba(244,63,94,0.1)]',
    warning: 'bg-yellow-400/10 border-yellow-400/20 text-yellow-200 shadow-[0_0_20px_rgba(250,204,21,0.1)]',
    info: 'bg-[#00f5d4]/10 border-[#00f5d4]/20 text-[#00f5d4] shadow-[0_0_20px_rgba(0,245,212,0.1)]',
  };

  const iconColors = {
    critical: 'text-rose-400',
    warning: 'text-yellow-400',
    info: 'text-[#00f5d4]',
  };

  return (
    <div className={`flex items-center justify-between gap-4 p-4 rounded-xl border backdrop-blur-xl transition-all duration-400 group/alert hover:translate-x-1 ${severityStyles[alert.severity]}`}>
      <div className="flex items-center gap-3">
        <span className={`${iconColors[alert.severity]} drop-shadow-[0_0_5px_currentColor] group-hover/alert:scale-110 transition-transform`}>
          {React.cloneElement(alert.icon as React.ReactElement, { size: 14, strokeWidth: 3 })}
        </span>
        <span className="text-[10px] font-black tracking-[0.1em] uppercase group-hover/alert:text-white transition-colors">
          {alert.message}
        </span>
      </div>
      {alert.action && (
        <Link
          to={alert.action.href}
          className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-white/40 hover:text-white transition-all bg-white/5 hover:bg-white/10 px-2.5 py-1.5 rounded border border-white/5 hover:border-white/20 shadow-inner"
        >
          {alert.action.label}
          <ArrowRight size={10} strokeWidth={3} />
        </Link>
      )}
    </div>
  );
}

export function AlertsWidget() {
  const { data: handoffData } = useQuery({
    queryKey: ['handoffAlerts', 'unreadCount'],
    queryFn: () => handoffAlertsService.getUnreadCount(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });

  const { data: botQuality } = useQuery({
    queryKey: ['analytics', 'botQuality'],
    queryFn: () => analyticsService.getBotQuality(30),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const { data: conversionFunnel } = useQuery({
    queryKey: ['analytics', 'conversionFunnel'],
    queryFn: () => analyticsService.getConversionFunnel(30),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const alerts: AlertItem[] = [];

  const unreadHandoffs = handoffData?.unreadCount ?? 0;
  if (unreadHandoffs > 0) {
    alerts.push({
      id: 'unread-handoffs',
      severity: unreadHandoffs > 5 ? 'critical' : 'warning',
      message: `${unreadHandoffs} INTERCEPT_WAITS_ACTIVE`,
      action: { label: 'ACCESS_HUB', href: '/conversations?view=handoff' },
      icon: <Users size={14} />,
    });
  }

  if (botQuality?.healthStatus === 'critical') {
    alerts.push({
      id: 'bot-critical',
      severity: 'critical',
      message: 'NEURAL_LINK_DEGRADED_CRITICAL',
      action: { label: 'DIAGNOSTIC', href: '/analytics' },
      icon: <Cpu size={14} />,
    });
  } else if (botQuality?.healthStatus === 'warning') {
    alerts.push({
      id: 'bot-warning',
      severity: 'warning',
      message: 'BOT_ANOMALY_DETECTED',
      action: { label: 'DIAGNOSTIC', href: '/analytics' },
      icon: <AlertTriangle size={14} />,
    });
  }

  const funnelData = conversionFunnel as { stages?: { dropoffPercent?: number }[] } | null;
  const firstStageDropoff = funnelData?.stages?.[0]?.dropoffPercent;
  if (firstStageDropoff != null && firstStageDropoff > 30) {
    alerts.push({
      id: 'conversion-drop',
      severity: 'warning',
      message: `LEAKAGE_DETECTED: ${firstStageDropoff.toFixed(0)}%_DROPOFF`,
      action: { label: 'ANALYSIS', href: '/analytics' },
      icon: <TrendingDown size={14} />,
    });
  }

  const hasAlerts = alerts.length > 0;
  const criticalCount = alerts.filter((a) => a.severity === 'critical').length;
  const warningCount = alerts.filter((a) => a.severity === 'warning').length;

  return (
    <StatCard
      title="Critical Signal Hub"
      value={hasAlerts ? `${criticalCount + warningCount}` : '0'}
      subValue={hasAlerts ? `${criticalCount}_CRIT / ${warningCount}_WARN` : 'TELEMETRY_NOMINAL'}
      icon={hasAlerts ? <AlertTriangle size={18} strokeWidth={2.5} /> : <CheckCircle size={18} strokeWidth={2.5} />}
      accentColor={criticalCount > 0 ? 'red' : warningCount > 0 ? 'orange' : 'mantis'}
      data-testid="alerts-widget"
    >
      {hasAlerts ? (
        <div className="space-y-2 mt-4">
          {alerts.map((alert) => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-3 py-10 opacity-40 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700">
          <div className="relative">
             <CheckCircle size={32} className="text-[#00f5d4] animate-pulse" />
             <div className="absolute inset-0 bg-[#00f5d4]/20 blur-xl animate-pulse" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#00f5d4] drop-shadow-[0_0_10px_rgba(0,245,212,0.5)]">GRID_NOMINAL</span>
        </div>
      )}
    </StatCard>
  );
}

export default AlertsWidget;
