/**
 * HandoffQueue Page - Story 4-7: Handoff Queue with Urgency
 *
 * Displays active handoff conversations sorted by urgency and wait time.
 * Allows merchants to filter by urgency level and paginate through results.
 * Story 4-9: Added Open in Messenger quick action button.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Users, ChevronLeft, ChevronRight, CheckCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useHandoffAlertsStore, type QueueUrgencyFilter } from '../stores/handoffAlertStore';
import type { HandoffAlert } from '../services/handoffAlerts';
import { conversationsService } from '../services/conversations';
import type { FacebookPageInfo, HybridModeState } from '../types/conversation';

const URGENCY_CONFIG = {
  high: { emoji: '🔴', label: 'High', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)]' },
  medium: { emoji: '🟡', label: 'Medium', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', glow: 'shadow-[0_0_15px_rgba(234,179,8,0.2)]' },
  low: { emoji: '🟢', label: 'Low', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]' },
};

const OFFLINE_CONFIG = {
  emoji: '🌙',
  label: 'After Hours',
  color: 'text-purple-400',
  bg: 'bg-purple-500/10',
  border: 'border-purple-500/20',
};

const HANDOFF_REASON_LABELS: Record<string, string> = {
  keyword: 'Keyword Trigger',
  low_confidence: 'Low Confidence',
  clarification_loop: 'Clarification Loop',
};

function formatWaitTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) {
    return `${hours}h`;
  }
  return `${hours}h ${remainingMinutes}m`;
}

interface HandoffQueueItemProps {
  alert: HandoffAlert;
  onMarkAsRead: (id: number) => void;
  onViewHistory: (conversationId: number) => void;
  onResolve: (conversationId: number) => void;
  facebookPage: FacebookPageInfo | null;
  onOpenMessenger: (conversationId: number, platformSenderId: string) => Promise<void>;
  hybridModes: Record<number, HybridModeState>;
}

function HandoffQueueItem({ 
  alert, 
  onMarkAsRead, 
  onViewHistory, 
  onResolve,
  facebookPage, 
  onOpenMessenger,
  hybridModes,
}: HandoffQueueItemProps) {
  const urgencyConfig = URGENCY_CONFIG[alert.urgencyLevel];
  const hybridMode = hybridModes[alert.conversationId] || null;
  const hasFacebookConnection = facebookPage?.isConnected && facebookPage.pageId && alert.platformSenderId;
  const isHybridModeActive = hybridMode?.enabled === true;

  return (
    <div
      data-testid="queue-item"
      data-alert-id={alert.id}
      data-urgency={alert.urgencyLevel}
      onClick={() => onViewHistory(alert.conversationId)}
      className={`p-6 rounded-[24px] border transition-all duration-300 cursor-pointer group relative overflow-hidden ${
        alert.isRead 
          ? 'bg-white/[0.02] border-white/5 opacity-60' 
          : 'bg-white/[0.04] border-white/10 shadow-xl'
      } hover:border-emerald-500/30 hover:bg-white/[0.06]`}
    >
      <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full -mr-16 -mt-16 blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="flex items-start justify-between relative z-10">
        <div className="flex-1 min-w-0">
          {/* Header: Customer + Urgency Badge + Wait Time */}
          <div className="flex items-center gap-3 mb-4 flex-wrap">
            <span 
              data-testid="item-urgency-badge"
              className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${urgencyConfig.bg} ${urgencyConfig.color} ${urgencyConfig.border} ${urgencyConfig.glow}`}
            >
              {urgencyConfig.label}
            </span>
            {alert.isOffline && (
              <span 
                data-testid="item-offline-badge"
                className={`inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${OFFLINE_CONFIG.bg} ${OFFLINE_CONFIG.color} ${OFFLINE_CONFIG.border}`}
              >
                {OFFLINE_CONFIG.label}
              </span>
            )}
            <span 
              data-testid="item-wait-time"
              className="text-xs text-white/40 font-bold uppercase tracking-widest flex items-center gap-1.5 ml-auto sm:ml-0"
            >
              <Clock size={12} className="text-emerald-500/50" />
              {formatWaitTime(alert.waitTimeSeconds)} waiting
            </span>
          </div>

          {/* Customer Info */}
          <h3 
            data-testid="item-customer-name"
            className="text-xl font-bold text-white tracking-tight group-hover:text-emerald-400 transition-colors"
          >
            {alert.customerName ?? `Customer ${alert.customerId ?? alert.conversationId}`}
          </h3>

          {/* Handoff Reason */}
          {alert.handoffReason && (
            <p 
              data-testid="item-handoff-reason"
              className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em] mt-2 italic"
            >
              Reason: {HANDOFF_REASON_LABELS[alert.handoffReason] || alert.handoffReason}
            </p>
          )}

          {/* Conversation Preview */}
          {alert.conversationPreview && (
            <div className="mt-4 p-4 bg-black/20 rounded-xl border border-white/5 group-hover:border-white/10 transition-colors">
              <p 
                data-testid="item-preview"
                className="text-sm text-white/60 leading-relaxed line-clamp-2 italic"
              >
                &quot;{alert.conversationPreview}&quot;
              </p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="ml-6 flex flex-col items-end gap-3 shrink-0">
          <button
            data-testid="item-resolve"
            onClick={async (e) => {
              e.stopPropagation();
              onResolve(alert.conversationId);
            }}
            className="w-full text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl flex items-center justify-center gap-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 hover:border-emerald-500/30 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]"
          >
            <CheckCircle size={14} />
            <span>Resolve</span>
          </button>
          
          {hasFacebookConnection && (
            <button
              data-testid="item-open-messenger"
              onClick={async (e) => {
                e.stopPropagation();
                await onOpenMessenger(alert.conversationId, alert.platformSenderId!);
              }}
              className={`w-full text-[10px] font-black uppercase tracking-widest px-4 py-2 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg ${
                isHybridModeActive 
                  ? 'bg-emerald-600 text-white hover:bg-emerald-500 shadow-emerald-600/20' 
                  : 'bg-blue-600 text-white hover:bg-blue-500 shadow-blue-600/20'
              }`}
            >
              <span>{isHybridModeActive ? 'Bot Paused' : 'Messenger'}</span>
            </button>
          )}
          
          {!alert.isRead && (
            <button
              data-testid="item-mark-read"
              onClick={(e) => {
                e.stopPropagation();
                onMarkAsRead(alert.id);
              }}
              className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500/40 hover:text-emerald-400 transition-colors px-2 py-1"
            >
              Mark read
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface UrgencyFilterTabsProps {
  activeFilter: QueueUrgencyFilter;
  onFilterChange: (filter: QueueUrgencyFilter) => void;
}

function UrgencyFilterTabs({ activeFilter, onFilterChange }: UrgencyFilterTabsProps) {
  const tabs: { value: QueueUrgencyFilter; label: string; emoji?: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'high', label: 'High', emoji: '🔴' },
    { value: 'medium', label: 'Medium', emoji: '🟡' },
    { value: 'low', label: 'Low', emoji: '🟢' },
  ];

  return (
    <div className="flex gap-2 p-1.5 bg-white/5 border border-white/10 rounded-2xl w-fit" data-testid="urgency-filter-tabs">
      {tabs.map((tab) => {
        const isActive = activeFilter === tab.value;
        return (
          <button
            key={tab.value}
            data-testid={`filter-${tab.value}`}
            onClick={() => onFilterChange(tab.value)}
            className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all duration-300 relative overflow-hidden ${
              isActive
                ? 'bg-[var(--mantis-glow)]/10 text-[var(--mantis-glow)] border border-[var(--mantis-glow)]/20 shadow-[0_0_15px_rgba(34,197,94,0.1)]'
                : 'text-white/40 hover:text-white/60 hover:bg-white/5'
            }`}
          >
            <span className="relative z-10">
              {tab.emoji && <span className="mr-2 grayscale-0 group-hover:grayscale-0">{tab.emoji}</span>}
              {tab.label}
            </span>
            {isActive && (
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 to-transparent opacity-50" />
            )}
          </button>
        );
      })}
    </div>
  );
}

interface PaginationProps {
  currentPage: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
}

function Pagination({ currentPage, total, limit, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(total / limit);

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between mt-10 pt-8 border-t border-white/5" data-testid="pagination">
      <p data-testid="pagination-info" className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">
        Page <span className="text-emerald-400">{currentPage}</span> of <span className="text-white/60">{totalPages}</span>
      </p>
      <div className="flex gap-3">
        <button
          data-testid="pagination-prev"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="p-3 rounded-xl bg-white/5 border border-white/10 text-white/60 disabled:opacity-20 disabled:cursor-not-allowed hover:bg-white/10 hover:border-white/20 transition-all"
        >
          <ChevronLeft size={18} />
        </button>
        <button
          data-testid="pagination-next"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-3 rounded-xl bg-white/5 border border-white/10 text-white/60 disabled:opacity-20 disabled:cursor-not-allowed hover:bg-white/10 hover:border-white/20 transition-all"
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  );
}

export default function HandoffQueue() {
  const navigate = useNavigate();
  const {
    queue,
    fetchQueue,
    setQueueFilter,
    setQueuePage,
    markAsRead,
    startQueuePolling,
    stopQueuePolling,
    error,
    clearError,
  } = useHandoffAlertsStore();
  
  const [facebookPage, setFacebookPage] = useState<FacebookPageInfo | null>(null);
  const [hybridModes, setHybridModes] = useState<Record<number, HybridModeState>>({});

  // Fetch queue and Facebook page on mount and start polling
  useEffect(() => {
    fetchQueue();
    startQueuePolling(30000);
    
    conversationsService.getFacebookPageInfo()
      .then((res) => setFacebookPage(res.data))
      .catch(() => setFacebookPage({ pageId: null, pageName: null, isConnected: false }));
    
    return () => stopQueuePolling();
  }, [fetchQueue, startQueuePolling, stopQueuePolling]);

  const handleMarkAsRead = async (alertId: number) => {
    await markAsRead(alertId);
  };

  const handleViewHistory = (conversationId: number) => {
    navigate(`/conversations/${conversationId}/history`, { state: { from: '/handoff-queue' } });
  };
  
  const handleOpenMessenger = async (conversationId: number, platformSenderId: string) => {
    if (!facebookPage?.pageId) return;
    
    const messengerUrl = `https://m.me/${facebookPage.pageId}?thread_id=${platformSenderId}`;
    window.open(messengerUrl, '_blank');
    
    try {
      const response = await conversationsService.setHybridMode(conversationId, {
        enabled: true,
        reason: 'merchant_responding',
      });
      
      setHybridModes((prev) => ({
        ...prev,
        [conversationId]: {
          enabled: response.hybridMode.enabled,
          activatedAt: response.hybridMode.activatedAt,
          activatedBy: response.hybridMode.activatedBy,
          expiresAt: response.hybridMode.expiresAt,
          remainingSeconds: response.hybridMode.remainingSeconds,
        },
      }));
    } catch (err) {
      console.error('Failed to enable hybrid mode:', err);
    }
  };

  const handleResolve = async (conversationId: number) => {
    try {
      await conversationsService.resolveHandoff(conversationId);
      await fetchQueue();
    } catch (err) {
      console.error('Failed to resolve handoff:', err);
    }
  };

  return (
    <div className="space-y-10" data-testid="handoff-queue-page">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 pb-8 border-b border-white/5">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tight mantis-glow-text">Handoff Queue</h1>
          <p className="text-base text-white/60 mt-1 font-medium">
            Active handoff conversations requiring agent assistance.
          </p>
        </div>
        
        {/* Total Waiting Count */}
        {queue.meta.totalWaiting !== null && (
          <div 
            className="flex items-center gap-3 px-6 py-3 bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 rounded-2xl shadow-[0_0_20px_rgba(34,197,94,0.1)] backdrop-blur-md"
            data-testid="total-waiting-count"
          >
            <Users className="text-[var(--mantis-glow)]" size={20} />
            <span className="text-sm font-black uppercase tracking-widest text-[var(--mantis-glow)]">
              {queue.meta.totalWaiting} customer{queue.meta.totalWaiting !== 1 ? 's' : ''} waiting
            </span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-5 bg-red-500/5 border border-red-500/10 rounded-2xl flex items-center justify-between backdrop-blur-xl animate-in shake duration-500">
          <div className="flex items-center gap-3">
            <AlertCircle size={20} className="text-red-400" />
            <span className="text-red-400 text-sm font-medium">{error}</span>
          </div>
          <button
            onClick={clearError}
            className="text-red-400/60 hover:text-red-400 text-[10px] font-black uppercase tracking-widest"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="glass-card p-1 pb-10 border-none shadow-2xl relative overflow-hidden flex flex-col">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full -mr-32 -mt-32 blur-[100px]" />
        
        {/* Filter Toolbar */}
        <div className="p-8 pb-4 flex items-center justify-between relative z-10 flex-wrap gap-4">
          <UrgencyFilterTabs
            activeFilter={queue.filter}
            onFilterChange={setQueueFilter}
          />
          
          <div className="flex items-center gap-2 text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">
            <RefreshCw size={12} className={queue.isLoading ? "animate-spin" : ""} />
            Auto-polling active
          </div>
        </div>

        {/* Queue List wrapper */}
        <div className="px-8 mt-4 relative z-10" data-testid="handoff-queue-list">
          <div className="space-y-4">
            {queue.isLoading && queue.items.length === 0 ? (
              <div className="py-20 flex flex-col items-center justify-center text-center space-y-4">
                <Loader2 size={48} className="text-emerald-500 animate-spin opacity-40" />
                <p className="text-[10px] font-bold text-white/30 uppercase tracking-[0.2em]">Retrieving active handoffs...</p>
              </div>
            ) : queue.items.length === 0 ? (
              <div className="py-24 text-center border-2 border-dashed border-white/5 rounded-[32px] bg-white/[0.01]" data-testid="queue-empty-state">
                <div className="p-6 bg-white/5 rounded-full w-fit mx-auto mb-6 shadow-inner">
                  <Users className="text-white/20" size={48} />
                </div>
                <h3 className="text-2xl font-bold text-white tracking-tight">Zero Handoffs</h3>
                <p className="max-w-[280px] mx-auto text-sm text-white/40 mt-2 font-medium">
                  Excellent work! All customer queries are currently being handled by the AI or cleared.
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 gap-4">
                  {queue.items.map((alert) => (
                    <HandoffQueueItem
                      key={alert.id}
                      alert={alert}
                      onMarkAsRead={handleMarkAsRead}
                      onViewHistory={handleViewHistory}
                      onResolve={handleResolve}
                      facebookPage={facebookPage}
                      onOpenMessenger={handleOpenMessenger}
                      hybridModes={hybridModes}
                    />
                  ))}
                </div>

                {/* Pagination */}
                <Pagination
                  currentPage={queue.currentPage}
                  total={queue.meta.total}
                  limit={20}
                  onPageChange={setQueuePage}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
