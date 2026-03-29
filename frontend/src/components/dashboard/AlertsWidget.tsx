import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, ArrowRight, Users, TrendingDown, Cpu, RotateCcw, Clock } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { handoffAlertsService } from '../../services/handoffAlerts';
import { StatCard } from './StatCard';
import { AlertDetailPanel } from './AlertDetailPanel';

const DISMISSED_ALERTS_KEY = 'dismissed_alerts';
const ALERT_TIMESTAMPS_KEY = 'alert_timestamps';

interface DismissedAlert {
  id: string;
  dismissedAt: string;
  alertType: 'handoff' | 'bot-quality' | 'conversion-drop';
  severity: 'critical' | 'warning' | 'info';
  message: string;
}

interface AlertTimestamps {
  [alertId: string]: string; // alertId -> ISO timestamp
}

type AlertSeverity = 'critical' | 'warning' | 'info';

interface AlertItem {
  id: string;
  severity: AlertSeverity;
  message: string;
  action?: {
    label: string;
  };
  alertType: 'handoff' | 'bot-quality' | 'conversion-drop';
  icon: React.ReactNode;
  timestamp?: string;
}

// Create icon components once to avoid JSX parsing issues
const createIcon = (IconComponent: any, size: number) => React.createElement(IconComponent, { size });

function AlertRow({
  alert,
  onClick,
}: {
  alert: AlertItem;
  onClick: () => void;
}) {
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

  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    return `${diffDays}d`;
  };

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between gap-3 p-3 rounded-xl border backdrop-blur-xl transition-all duration-400 group/alert hover:translate-x-1 cursor-pointer ${severityStyles[alert.severity]}`}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className={`${iconColors[alert.severity]} drop-shadow-[0_0_5px_currentColor] group-hover/alert:scale-110 transition-transform flex-shrink-0`}>
          {alert.icon}
        </span>
        <span className="text-[9px] font-black tracking-[0.05em] uppercase group-hover/alert:text-white transition-colors text-left flex-1 min-w-0 truncate">
          {alert.message}
        </span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        {alert.timestamp && (
          <span className="flex items-center gap-1 text-[8px] text-white/30 font-medium uppercase tracking-wider">
            <Clock size={8} strokeWidth={2} />
            {formatRelativeTime(alert.timestamp)}
          </span>
        )}
        {alert.action && (
          <span className="flex items-center gap-1 text-[8px] font-black uppercase tracking-widest text-white/40 group-hover/alert:text-white transition-all bg-white/5 group-hover/alert:bg-white/10 px-2 py-1 rounded border border-white/5 group-hover/alert:border-white/20 shadow-inner flex-shrink-0">
            {alert.action.label}
            <ArrowRight size={8} strokeWidth={3} />
          </span>
        )}
      </div>
    </button>
  );
}

export function AlertsWidget() {
  const [selectedAlert, setSelectedAlert] = useState<{
    id: string;
    alertType: 'handoff' | 'bot-quality' | 'conversion-drop';
    severity: AlertSeverity;
    data?: Record<string, unknown>;
  } | null>(null);

  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(() => {
    const stored = localStorage.getItem(DISMISSED_ALERTS_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });

  const [alertTimestamps, setAlertTimestamps] = useState<AlertTimestamps>(() => {
    const stored = localStorage.getItem(ALERT_TIMESTAMPS_KEY);
    return stored ? JSON.parse(stored) : {};
  });

  useEffect(() => {
    localStorage.setItem(DISMISSED_ALERTS_KEY, JSON.stringify([...dismissedAlerts]));
  }, [dismissedAlerts]);

  useEffect(() => {
    localStorage.setItem(ALERT_TIMESTAMPS_KEY, JSON.stringify(alertTimestamps));
  }, [alertTimestamps]);

  const handleDismissAlert = (alertId: string) => {
    setDismissedAlerts(prev => new Set([...prev, alertId]));
    localStorage.setItem(`${DISMISSED_ALERTS_KEY}_${alertId}`, new Date().toISOString());
  };

  const handleRestoreAlert = (alertId: string) => {
    setDismissedAlerts(prev => {
      const newSet = new Set(prev);
      newSet.delete(alertId);
      return newSet;
    });
  };

  const handleRestoreAll = () => {
    setDismissedAlerts(new Set());
    setShowRestoreDialog(false);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const updateAlertTimestamp = (alertId: string) => {
    setAlertTimestamps(prev => ({
      ...prev,
      [alertId]: new Date().toISOString(),
    }));
  };

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
  const handoffAlertId = 'unread-handoffs';
  const botCriticalAlertId = 'bot-critical';
  const botWarningAlertId = 'bot-warning';
  const conversionAlertId = 'conversion-drop';

  // Update timestamps for active alerts
  if (unreadHandoffs > 0 && !alertTimestamps[handoffAlertId]) {
    updateAlertTimestamp(handoffAlertId);
  }
  if (botQuality?.healthStatus === 'critical' && !alertTimestamps[botCriticalAlertId]) {
    updateAlertTimestamp(botCriticalAlertId);
  }
  if (botQuality?.healthStatus === 'warning' && !alertTimestamps[botWarningAlertId]) {
    updateAlertTimestamp(botWarningAlertId);
  }
  const funnelData = conversionFunnel as { stages?: { dropoffPercent?: number }[] } | null;
  const firstStageDropoff = funnelData?.stages?.[0]?.dropoffPercent;
  if (firstStageDropoff != null && firstStageDropoff > 30 && !alertTimestamps[conversionAlertId]) {
    updateAlertTimestamp(conversionAlertId);
  }

  if (unreadHandoffs > 0 && !dismissedAlerts.has(handoffAlertId)) {
    alerts.push({
      id: handoffAlertId,
      alertType: 'handoff',
      severity: unreadHandoffs > 5 ? 'critical' : 'warning',
      message: `${unreadHandoffs} INTERCEPT_WAITS_ACTIVE`,
      action: { label: 'VIEW DETAILS' },
      icon: createIcon(Users, 14),
      timestamp: alertTimestamps[handoffAlertId],
    });
  }

  if (botQuality?.healthStatus === 'critical' && !dismissedAlerts.has(botCriticalAlertId)) {
    alerts.push({
      id: botCriticalAlertId,
      alertType: 'bot-quality',
      severity: 'critical',
      message: 'NEURAL_LINK_DEGRADED_CRITICAL',
      action: { label: 'DIAGNOSTIC' },
      icon: createIcon(Cpu, 14),
      timestamp: alertTimestamps[botCriticalAlertId],
    });
  } else if (botQuality?.healthStatus === 'warning' && !dismissedAlerts.has(botWarningAlertId)) {
    alerts.push({
      id: botWarningAlertId,
      alertType: 'bot-quality',
      severity: 'warning',
      message: 'BOT_ANOMALY_DETECTED',
      action: { label: 'DIAGNOSTIC' },
      icon: createIcon(AlertTriangle, 14),
      timestamp: alertTimestamps[botWarningAlertId],
    });
  }

  if (firstStageDropoff != null && firstStageDropoff > 30 && !dismissedAlerts.has(conversionAlertId)) {
    alerts.push({
      id: conversionAlertId,
      alertType: 'conversion-drop',
      severity: 'warning',
      message: `LEAKAGE_DETECTED: ${firstStageDropoff.toFixed(0)}%_DROPOFF`,
      action: { label: 'ANALYSIS' },
      icon: createIcon(TrendingDown, 14),
      timestamp: alertTimestamps[conversionAlertId],
    });
  }

  const handleAlertClick = (alert: AlertItem) => {
    const alertData: Record<string, unknown> = {};

    if (alert.alertType === 'handoff') {
      alertData.unreadCount = unreadHandoffs;
    } else if (alert.alertType === 'bot-quality') {
      alertData.healthStatus = botQuality?.healthStatus;
      alertData.avgResponseTimeSeconds = botQuality?.avgResponseTimeSeconds;
      alertData.fallbackRate = botQuality?.fallbackRate;
      alertData.resolutionRate = botQuality?.resolutionRate;
      alertData.totalConversations = botQuality?.totalConversations;
    } else if (alert.alertType === 'conversion-drop') {
      alertData.firstStageDropoff = firstStageDropoff;
    }

    setSelectedAlert({
      id: alert.id,
      alertType: alert.alertType,
      severity: alert.severity,
      data: alertData,
    });
  };

  const hasAlerts = alerts.length > 0;
  const criticalCount = alerts.filter((a) => a.severity === 'critical').length;
  const warningCount = alerts.filter((a) => a.severity === 'warning').length;
  const hasDismissedAlerts = dismissedAlerts.size > 0;

  return (
    <>
      <StatCard
        title="Critical Signal Hub"
        value={hasAlerts ? `${criticalCount + warningCount}` : '0'}
        subValue={hasAlerts ? `${criticalCount}_CRIT / ${warningCount}_WARN` : 'TELEMETRY_NOMINAL'}
        icon={hasAlerts ? <AlertTriangle size={18} strokeWidth={2.5} /> : <CheckCircle size={18} strokeWidth={2.5} />}
        accentColor={criticalCount > 0 ? 'red' : warningCount > 0 ? 'orange' : 'mantis'}
        data-testid="alerts-widget"
      >
        {hasAlerts ? (
          <>
            {/* Horizontal scroll alert cards */}
            <div className="mt-4">
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/20">
                {alerts.map((alert, index) => (
                  <div
                    key={alert.id}
                    className="flex-shrink-0 w-48 p-3 rounded-xl border backdrop-blur-xl transition-all duration-300 group/alert hover:scale-105 cursor-pointer relative overflow-hidden"
                    style={{
                      backgroundColor: alert.severity === 'critical'
                        ? 'rgba(244, 63, 94, 0.1)'
                        : alert.severity === 'warning'
                          ? 'rgba(250, 204, 21, 0.1)'
                          : 'rgba(0, 245, 212, 0.1)',
                      borderColor: alert.severity === 'critical'
                        ? 'rgba(244, 63, 94, 0.2)'
                        : alert.severity === 'warning'
                          ? 'rgba(250, 204, 21, 0.2)'
                          : 'rgba(0, 245, 212, 0.2)',
                    }}
                    onClick={() => handleAlertClick(alert)}
                  >
                    {/* Severity badge */}
                    <div className="absolute top-2 right-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          alert.severity === 'critical'
                            ? 'bg-rose-500 animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.8)]'
                            : alert.severity === 'warning'
                              ? 'bg-yellow-400 shadow-[0_0_10px_rgba(250,204,21,0.8)]'
                              : 'bg-[#00f5d4] shadow-[0_0_10px_rgba(0,245,212,0.8)]'
                        }`}
                      />
                    </div>

                    {/* Alert content */}
                    <div className="flex items-start gap-2 mb-2">
                      <div
                        className={`flex-shrink-0 ${
                          alert.severity === 'critical'
                            ? 'text-rose-400'
                            : alert.severity === 'warning'
                              ? 'text-yellow-400'
                              : 'text-[#00f5d4]'
                        }`}
                      >
                        {alert.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[8px] font-black uppercase tracking-widest text-white/30 mb-1">
                          {alert.alertType.replace('-', ' ')}
                        </p>
                        <p className="text-[9px] font-bold text-white leading-tight">
                          {alert.message}
                        </p>
                      </div>
                    </div>

                    {/* Timestamp and action */}
                    <div className="flex items-center justify-between mt-2">
                      {alert.timestamp && (
                        <span className="flex items-center gap-1 text-[8px] text-white/30 font-medium uppercase tracking-wider">
                          <Clock size={8} strokeWidth={2} />
                          {formatTimestamp(alert.timestamp)}
                        </span>
                      )}
                      {alert.action && (
                        <span className="flex items-center gap-1 text-[8px] font-black uppercase tracking-widest text-white/40 group-hover/alert:text-white transition-all">
                          {alert.action.label}
                          <ArrowRight size={8} strokeWidth={3} />
                        </span>
                      )}
                    </div>

                    {/* Swipe dismiss hint */}
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-white/10 to-transparent transform scale-x-0 group-hover/alert:scale-x-100 transition-transform" />
                  </div>
                ))}
              </div>
            </div>

            {/* Scroll indicator */}
            <div className="flex items-center justify-center gap-2 mt-2">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-white/10" />
              <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest">
                ← Swipe to dismiss →
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-white/10" />
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center gap-3 py-10 opacity-40 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700">
            <div className="relative">
               <CheckCircle size={32} className="text-[#00f5d4] animate-pulse" />
               <div className="absolute inset-0 bg-[#00f5d4]/20 blur-xl animate-pulse" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#00f5d4] drop-shadow-[0_0_10px_rgba(0,245,212,0.5)]">GRID_NOMINAL</span>
            {hasDismissedAlerts && (
              <button
                onClick={() => setShowRestoreDialog(true)}
                className="text-[9px] font-black uppercase tracking-widest text-white/20 hover:text-white/40 transition-colors flex items-center gap-1.5 mt-2"
              >
                <RotateCcw size={10} strokeWidth={2.5} />
                Restore dismissed alerts
              </button>
            )}
          </div>
        )}

        {/* Dismissed alerts list */}
        {hasDismissedAlerts && hasAlerts && (
          <div className="mt-4 pt-4 border-t border-white/5">
            <button
              onClick={() => setShowRestoreDialog(true)}
              className="w-full text-[9px] font-black uppercase tracking-widest text-white/20 hover:text-white/40 transition-colors flex items-center justify-center gap-1.5 py-2 hover:bg-white/5 rounded"
            >
              <RotateCcw size={10} strokeWidth={2.5} />
              {dismissedAlerts.size} dismissed alert{dismissedAlerts.size > 1 ? 's' : ''}
            </button>
          </div>
        )}
      </StatCard>

      {selectedAlert && (
        <AlertDetailPanel
          isOpen={true}
          onClose={() => setSelectedAlert(null)}
          onDismiss={() => handleDismissAlert(selectedAlert.id)}
          alertId={selectedAlert.id}
          alertType={selectedAlert.alertType}
          severity={selectedAlert.severity}
          data={selectedAlert.data}
          timestamp={alertTimestamps[selectedAlert.id]}
        />
      )}

      {/* Restore Dialog */}
      {showRestoreDialog && (
        <>
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-in fade-in duration-200"
            onClick={() => setShowRestoreDialog(false)}
            aria-hidden="true"
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-[#0d0d12] border border-white/10 rounded-xl shadow-[0_0_40px_rgba(0,0,0,0.5)] max-w-md w-full animate-in zoom-in-95 duration-200">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-[#00f5d4]/10">
                    <RotateCcw size={18} className="text-[#00f5d4]" strokeWidth={2.5} />
                  </div>
                  <div>
                    <h3 className="text-sm font-black text-white uppercase tracking-widest">
                      Restore Dismissed Alerts
                    </h3>
                    <p className="text-[10px] text-white/40 font-bold uppercase tracking-wider mt-0.5">
                      {dismissedAlerts.size} alert{dismissedAlerts.size > 1 ? 's' : ''} available
                    </p>
                  </div>
                </div>

                <p className="text-xs text-white/60 leading-relaxed mb-6">
                  Restoring dismissed alerts will make them visible in the Critical Signal Hub again.
                  They will continue to trigger as long as the underlying conditions persist.
                </p>

                {/* Dismissed alerts list */}
                <div className="space-y-2 mb-6 max-h-48 overflow-y-auto">
                  {[...dismissedAlerts].map((alertId) => {
                    const timestamp = alertTimestamps[alertId];
                    const dismissedAt = localStorage.getItem(`${DISMISSED_ALERTS_KEY}_${alertId}`);
                    return (
                      <div
                        key={alertId}
                        className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-black uppercase tracking-wider text-white/40">
                            {alertId.replace(/-/g, ' ')}
                          </span>
                          {timestamp && (
                            <span className="text-[9px] text-white/30">
                              Triggered {formatTimestamp(timestamp)}
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => handleRestoreAlert(alertId)}
                          className="text-[9px] font-black uppercase tracking-widest text-[#00f5d4] hover:text-white transition-colors px-2 py-1 rounded hover:bg-[#00f5d4]/10"
                        >
                          Restore
                        </button>
                      </div>
                    );
                  })}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setShowRestoreDialog(false)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                      bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20
                      text-white/70 hover:text-white transition-all text-[10px] font-black uppercase tracking-widest"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRestoreAll}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                      bg-[#00f5d4] hover:bg-[#00f5d4]/90 text-black font-black text-[10px] uppercase tracking-widest
                      transition-all shadow-[0_0_20px_rgba(0,245,212,0.3)] hover:shadow-[0_0_30px_rgba(0,245,212,0.4)]"
                  >
                    <RotateCcw size={12} strokeWidth={2.5} />
                    Restore All
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

export default AlertsWidget;
