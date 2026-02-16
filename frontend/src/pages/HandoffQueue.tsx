/**
 * HandoffQueue Page - Story 4-7: Handoff Queue with Urgency
 *
 * Displays active handoff conversations sorted by urgency and wait time.
 * Allows merchants to filter by urgency level and paginate through results.
 * Story 4-9: Added Open in Messenger quick action button.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Users, ChevronLeft, ChevronRight } from 'lucide-react';
import { useHandoffAlertsStore, type QueueUrgencyFilter } from '../stores/handoffAlertStore';
import type { HandoffAlert } from '../services/handoffAlerts';
import { conversationsService } from '../services/conversations';
import type { FacebookPageInfo, HybridModeState } from '../types/conversation';

const URGENCY_CONFIG = {
  high: { emoji: '🔴', label: 'High', color: 'text-red-600', bg: 'bg-red-50' },
  medium: { emoji: '🟡', label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-50' },
  low: { emoji: '🟢', label: 'Low', color: 'text-green-600', bg: 'bg-green-50' },
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
  facebookPage: FacebookPageInfo | null;
  onOpenMessenger: (conversationId: number, platformSenderId: string) => Promise<void>;
  hybridModes: Record<number, HybridModeState>;
}

function HandoffQueueItem({ 
  alert, 
  onMarkAsRead, 
  onViewHistory, 
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
      className={`p-4 rounded-lg border cursor-pointer ${
        alert.isRead ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-300'
      } hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Header: Customer + Urgency Badge */}
          <div className="flex items-center gap-2 mb-2">
            <span 
              data-testid="item-urgency-badge"
              className={`inline-flex items-center px-2 py-0.5 rounded text-sm font-medium ${urgencyConfig.bg} ${urgencyConfig.color}`}
            >
              {urgencyConfig.emoji} {urgencyConfig.label}
            </span>
            <span className="text-gray-400">•</span>
            <span 
              data-testid="item-wait-time"
              className="text-sm text-gray-500 flex items-center gap-1"
            >
              <Clock size={14} />
              {formatWaitTime(alert.waitTimeSeconds)}
            </span>
          </div>

          {/* Customer Info */}
          <h3 
            data-testid="item-customer-name"
            className="font-medium text-gray-900 truncate"
          >
            {alert.customerName ?? `Customer ${alert.customerId ?? alert.conversationId}`}
          </h3>

          {/* Handoff Reason */}
          {alert.handoffReason && (
            <p 
              data-testid="item-handoff-reason"
              className="text-xs text-gray-500 mt-1"
            >
              Reason: {HANDOFF_REASON_LABELS[alert.handoffReason] || alert.handoffReason}
            </p>
          )}

          {/* Conversation Preview */}
          {alert.conversationPreview && (
            <p 
              data-testid="item-preview"
              className="text-sm text-gray-600 mt-2 line-clamp-2"
            >
              {alert.conversationPreview}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="ml-4 flex flex-col items-end gap-2">
          {hasFacebookConnection && (
            <button
              data-testid="item-open-messenger"
              onClick={async (e) => {
                e.stopPropagation();
                await onOpenMessenger(alert.conversationId, alert.platformSenderId!);
              }}
              className={`text-xs px-3 py-1.5 rounded-md flex items-center gap-1 ${
                isHybridModeActive 
                  ? 'bg-green-600 text-white hover:bg-green-700' 
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <span>{isHybridModeActive ? 'Bot Paused' : 'Open in Messenger'}</span>
            </button>
          )}
          {!alert.isRead && (
            <button
              data-testid="item-mark-read"
              onClick={(e) => {
                e.stopPropagation();
                onMarkAsRead(alert.id);
              }}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Mark as read
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
    <div className="flex border-b border-gray-200" data-testid="urgency-filter-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          data-testid={`filter-${tab.value}`}
          onClick={() => onFilterChange(tab.value)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeFilter === tab.value
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {tab.emoji && <span className="mr-1">{tab.emoji}</span>}
          {tab.label}
        </button>
      ))}
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
    <div className="flex items-center justify-between mt-6" data-testid="pagination">
      <p data-testid="pagination-info" className="text-sm text-gray-500">
        Page {currentPage} of {totalPages}
      </p>
      <div className="flex gap-2">
        <button
          data-testid="pagination-prev"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="p-2 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          <ChevronLeft size={16} />
        </button>
        <button
          data-testid="pagination-next"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-2 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          <ChevronRight size={16} />
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

  return (
    <div className="p-6" data-testid="handoff-queue-page">
      {/* Error Banner */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <span className="text-red-700 text-sm">{error}</span>
          <button
            onClick={clearError}
            className="text-red-500 hover:text-red-700 text-sm font-medium"
          >
            Dismiss
          </button>
        </div>
      )}
      
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Handoff Queue</h1>
        <p className="text-gray-500 mt-1">
          Active handoff conversations sorted by urgency
        </p>
      </div>

      {/* Total Waiting Count */}
      {queue.meta.totalWaiting !== null && (
        <div 
          className="flex items-center gap-2 mb-4 p-3 bg-blue-50 rounded-lg"
          data-testid="total-waiting-count"
        >
          <Users className="text-blue-600" size={20} />
          <span className="font-medium text-blue-900">
            {queue.meta.totalWaiting} customer{queue.meta.totalWaiting !== 1 ? 's' : ''} waiting
          </span>
        </div>
      )}

      {/* Filter Tabs */}
      <UrgencyFilterTabs
        activeFilter={queue.filter}
        onFilterChange={setQueueFilter}
      />

      {/* Queue List */}
      <div className="mt-4 space-y-3" data-testid="handoff-queue-list">
        {queue.isLoading ? (
          <div className="p-8 text-center text-gray-500">
            Loading queue...
          </div>
        ) : queue.items.length === 0 ? (
          <div className="p-8 text-center text-gray-500" data-testid="queue-empty-state">
            <Users className="mx-auto mb-2 text-gray-300" size={48} />
            <p>No active handoffs in the queue</p>
            <p className="text-sm mt-1">Customers needing assistance will appear here</p>
          </div>
        ) : (
          <>
            {queue.items.map((alert) => (
              <HandoffQueueItem
                key={alert.id}
                alert={alert}
                onMarkAsRead={handleMarkAsRead}
                onViewHistory={handleViewHistory}
                facebookPage={facebookPage}
                onOpenMessenger={handleOpenMessenger}
                hybridModes={hybridModes}
              />
            ))}

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
  );
}
