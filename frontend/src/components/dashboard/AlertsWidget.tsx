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
    critical: 'bg-rose-500/10 border-rose-500/20 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.1)]',
    warning: 'bg-amber-500/10 border-amber-500/20 text-amber-200 shadow-[0_0_15px_rgba(245,158,11,0.1)]',
    info: 'bg-blue-500/10 border-blue-500/20 text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.1)]',
  };

  const iconColors = {
    critical: 'text-rose-400',
    warning: 'text-amber-400',
    info: 'text-blue-400',
  };

  return (
    <div className={`flex items-center justify-between gap-3 p-3 rounded-xl border backdrop-blur-md transition-all duration-300 hover:scale-[1.01] ${severityStyles[alert.severity]}`}>
      <div className="flex items-center gap-2.5">
        <span className={`${iconColors[alert.severity]} drop-shadow-sm`}>{alert.icon}</span>
        <span className="text-xs font-bold tracking-wide uppercase">{alert.message}</span>
      </div>
      {alert.action && (
        <Link
          to={alert.action.href}
          className="flex items-center gap-1 text-[10px] font-black uppercase tracking-tighter hover:text-white transition-colors bg-white/10 px-2 py-1 rounded-md border border-white/10"
        >
          {alert.action.label}
          <ArrowRight size={10} />
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
      message: `${unreadHandoffs} unread handoff${unreadHandoffs > 1 ? 's' : ''} waiting`,
      action: { label: 'View Queue', href: '/conversations?view=handoff' },
      icon: <Users size={14} />,
    });
  }

  if (botQuality?.healthStatus === 'critical') {
    alerts.push({
      id: 'bot-critical',
      severity: 'critical',
      message: 'Bot health critical - high fallback rate',
      action: { label: 'View Details', href: '/analytics' },
      icon: <Cpu size={14} />,
    });
  } else if (botQuality?.healthStatus === 'warning') {
    alerts.push({
      id: 'bot-warning',
      severity: 'warning',
      message: 'Bot needs attention',
      action: { label: 'View Details', href: '/analytics' },
      icon: <AlertTriangle size={14} />,
    });
  }

  const funnelData = conversionFunnel as { stages?: { dropoffPercent?: number }[] } | null;
  const firstStageDropoff = funnelData?.stages?.[0]?.dropoffPercent;
  if (firstStageDropoff != null && firstStageDropoff > 30) {
    alerts.push({
      id: 'conversion-drop',
      severity: 'warning',
      message: `High drop-off at first funnel stage (${firstStageDropoff.toFixed(0)}%)`,
      action: { label: 'View Funnel', href: '/analytics' },
      icon: <TrendingDown size={14} />,
    });
  }

  const hasAlerts = alerts.length > 0;
  const criticalCount = alerts.filter((a) => a.severity === 'critical').length;
  const warningCount = alerts.filter((a) => a.severity === 'warning').length;

  return (
    <StatCard
      title="Alerts"
      value={hasAlerts ? `${criticalCount + warningCount}` : '0'}
      subValue={hasAlerts ? `${criticalCount} critical, ${warningCount} warning` : 'All clear'}
      icon={hasAlerts ? <AlertTriangle size={18} /> : <CheckCircle size={18} />}
      accentColor={criticalCount > 0 ? 'red' : warningCount > 0 ? 'orange' : 'green'}
      data-testid="alerts-widget"
    >
      {hasAlerts ? (
        <div className="space-y-2 mt-2">
          {alerts.map((alert) => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </div>
      ) : (
        <div className="flex items-center justify-center gap-2 py-6 text-emerald-400/60 transition-opacity duration-500">
          <CheckCircle size={16} className="animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-widest">SYSTEMS OPTIMAL</span>
        </div>
      )}
    </StatCard>
  );
}

export default AlertsWidget;
