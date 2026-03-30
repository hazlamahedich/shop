import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Activity, Zap, Clock, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface PerformanceAlert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  metric: string;
  value: number;
  threshold: number;
  timestamp: string;
  suggestedAction?: string;
}

export function PerformanceAlertsWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'performance-alerts'],
    queryFn: () => analyticsService.getPerformanceAlerts(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const alerts = data as PerformanceAlert[] | undefined;
  const criticalCount = alerts?.filter((a) => a.type === 'critical').length || 0;
  const warningCount = alerts?.filter((a) => a.type === 'warning').length || 0;

  return (
    <StatCard
      title="Performance Alerts"
      value={isLoading ? '...' : `${alerts?.length || 0}`}
      subValue="ACTIVE_ALERTS"
      icon={<Activity size={18} />}
      accentColor={criticalCount > 0 ? 'red' : warningCount > 0 ? 'orange' : 'mantis'}
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Alerts Unavailable</p>
          </div>
        ) : !alerts || alerts.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-[#00f5d4]/60 uppercase tracking-widest flex items-center gap-2">
              <Activity size={14} />
              All systems optimal!
            </p>
          </div>
        ) : (
          <>
            {/* Alert Summary */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-rose-400/5 border border-rose-400/20 p-3 rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle size={12} className="text-rose-400" />
                  <p className="text-[9px] font-bold text-rose-400 uppercase tracking-wider">Critical</p>
                </div>
                <p className="text-2xl font-black text-rose-400">{criticalCount}</p>
              </div>
              <div className="bg-orange-400/5 border border-orange-400/20 p-3 rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 mb-1">
                  <Zap size={12} className="text-orange-400" />
                  <p className="text-[9px] font-bold text-orange-400 uppercase tracking-wider">Warning</p>
                </div>
                <p className="text-2xl font-black text-orange-400">{warningCount}</p>
              </div>
            </div>

            {/* Alerts List */}
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Active Alerts</p>
                <p className="text-[8px] text-white/30">Sorted by severity</p>
              </div>
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`${
                      alert.type === 'critical'
                        ? 'bg-rose-400/5 border-rose-400/20'
                        : alert.type === 'warning'
                        ? 'bg-orange-400/5 border-orange-400/20'
                        : 'bg-white/5 border-white/10'
                    } border p-3 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-all`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                        alert.type === 'critical'
                          ? 'bg-rose-400/10'
                          : alert.type === 'warning'
                          ? 'bg-orange-400/10'
                          : 'bg-white/10'
                      }`}>
                        {alert.type === 'critical' ? (
                          <AlertTriangle size={16} className="text-rose-400" />
                        ) : alert.type === 'warning' ? (
                          <Zap size={16} className="text-orange-400" />
                        ) : (
                          <Activity size={16} className="text-white/60" />
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <p className="text-[10px] font-semibold text-white/90">{alert.title}</p>
                          <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${
                            alert.type === 'critical'
                              ? 'bg-rose-400/20 text-rose-400'
                              : alert.type === 'warning'
                              ? 'bg-orange-400/20 text-orange-400'
                              : 'bg-white/10 text-white/60'
                          }`}>
                            {alert.type}
                          </span>
                        </div>
                        <p className="text-[9px] text-white/60 mb-2">{alert.description}</p>

                        {/* Metric */}
                        <div className="flex items-center gap-2 text-[9px]">
                          <span className="text-white/30">{alert.metric}:</span>
                          <span
                            className={`font-black ${
                              alert.type === 'critical' ? 'text-rose-400' : alert.type === 'warning' ? 'text-orange-400' : 'text-white/80'
                            }`}
                          >
                            {alert.value}
                          </span>
                          <span className="text-white/30">/ {alert.threshold} threshold</span>
                        </div>

                        {/* Suggested Action */}
                        {alert.suggestedAction && (
                          <div className="mt-2 pt-2 border-t border-white/5">
                            <p className="text-[8px] text-white/40 uppercase tracking-wider mb-1">Suggested Action</p>
                            <p className="text-[9px] text-[#00f5d4]">{alert.suggestedAction}</p>
                          </div>
                        )}

                        {/* Timestamp */}
                        <div className="mt-2 pt-2 border-t border-white/5">
                          <p className="text-[8px] text-white/30 uppercase tracking-wider flex items-center gap-1">
                            <Clock size={10} />
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Summary */}
            <div className="pt-2 border-t border-white/5">
              <div className="flex items-center justify-between text-[9px]">
                <span className="text-white/30 uppercase tracking-wider">System Health</span>
                <span
                  className={`font-black ${
                    criticalCount === 0 && warningCount === 0
                      ? 'text-[#00f5d4]'
                      : criticalCount === 0
                      ? 'text-orange-400'
                      : 'text-rose-400'
                  }`}
                >
                  {criticalCount === 0 && warningCount === 0
                    ? 'Optimal'
                    : criticalCount === 0
                    ? 'Degraded'
                    : 'Critical'}
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default PerformanceAlertsWidget;
