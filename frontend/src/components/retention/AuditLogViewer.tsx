import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Filter, RefreshCw, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { Badge } from '../ui/Badge';

interface AuditLog {
  id: number;
  sessionId: string;
  merchantId: number;
  retentionPeriodDays: number | null;
  deletionTrigger: string;
  requestedAt: string;
  completedAt: string | null;
  conversationsDeleted: number;
  messagesDeleted: number;
  redisKeysCleared: number;
  errorMessage: string | null;
}

interface AuditLogViewerProps {
  className?: string;
}

export const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ className = '' }) => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    merchantId: '',
    startDate: '',
    endDate: '',
    trigger: '',
  });

  const [showFilters, setShowFilters] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('pageSize', pageSize.toString());

      if (filters.merchantId) params.append('merchantId', filters.merchantId);
      if (filters.startDate) params.append('startDate', filters.startDate);
      if (filters.endDate) params.append('endDate', filters.endDate);
      if (filters.trigger) params.append('trigger', filters.trigger);

      const response = await fetch(`/api/v1/audit/retention-logs?${params.toString()}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || errorData?.message || 'Failed to fetch audit logs';
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const handleRefresh = () => {
    fetchLogs();
  };

  const handleExport = () => {
    const csvContent = [
      ['Session ID', 'Merchant ID', 'Trigger', 'Requested At', 'Conversations', 'Messages', 'Status'].join(','),
      ...logs.map(log => [
        log.sessionId,
        log.merchantId,
        log.deletionTrigger,
        new Date(log.requestedAt).toISOString(),
        log.conversationsDeleted,
        log.messagesDeleted,
        log.completedAt ? 'Completed' : 'Failed',
      ].join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `retention-audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const totalPages = Math.ceil(total / pageSize);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={className}>
      <div data-testid="audit-logs-tab">
        <div className="mb-0">
          <div className="flex justify-between items-center mb-10">
            <div className="flex gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`h-12 px-6 rounded-2xl flex items-center gap-3 transition-all duration-500 text-[10px] font-black uppercase tracking-[0.2em] border backdrop-blur-md ${
                  showFilters
                    ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)]'
                    : 'bg-white/5 border-white/10 text-emerald-900/60 hover:bg-white/10 hover:border-white/20'
                }`}
              >
                <Filter size={14} className={showFilters ? 'text-emerald-400 shadow-glow' : ''} />
                Filters Schema
              </button>
              <button
                onClick={handleRefresh}
                data-testid="refresh-audit-logs"
                className="h-12 px-6 bg-white/5 border border-white/10 text-emerald-900/60 rounded-2xl flex items-center gap-3 transition-all duration-500 hover:bg-white/10 hover:border-white/20 text-[10px] font-black uppercase tracking-[0.2em] backdrop-blur-md"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin text-emerald-400' : ''} />
                Refresh Engine
              </button>
            </div>
            <button
              onClick={handleExport}
              className="h-12 px-8 bg-emerald-500 text-black rounded-2xl flex items-center gap-3 transition-all duration-500 hover:bg-emerald-400 hover:scale-[1.02] active:scale-[0.98] font-black text-[10px] uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(16,185,129,0.3)]"
            >
              <Download size={14} />
              Export Records
            </button>
          </div>

          {showFilters && (
            <GlassCard accent="mantis" className="mb-8 p-8 border-emerald-500/10 bg-emerald-500/[0.02]">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div className="space-y-3">
                  <label className="block text-[10px] font-black text-emerald-900/40 uppercase tracking-widest pl-1">
                    Merchant Identity
                  </label>
                  <input
                    type="number"
                    value={filters.merchantId}
                    onChange={(e) => handleFilterChange('merchantId', e.target.value)}
                    placeholder="All Merchants"
                    className="w-full h-12 px-4 bg-black/40 border border-emerald-500/10 rounded-xl text-emerald-50 placeholder:text-emerald-900/20 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 outline-none transition-all duration-300 text-sm"
                  />
                </div>

                <div className="space-y-3">
                  <label className="block text-[10px] font-black text-emerald-900/40 uppercase tracking-widest pl-1">
                    Temporal Start
                  </label>
                  <input
                    type="date"
                    data-testid="start-date"
                    value={filters.startDate}
                    onChange={(e) => handleFilterChange('startDate', e.target.value)}
                    className="w-full h-12 px-4 bg-black/40 border border-emerald-500/10 rounded-xl text-emerald-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 outline-none transition-all duration-300 text-sm [color-scheme:dark]"
                  />
                </div>

                <div className="space-y-3">
                  <label className="block text-[10px] font-black text-emerald-900/40 uppercase tracking-widest pl-1">
                    Temporal End
                  </label>
                  <input
                    type="date"
                    data-testid="end-date"
                    value={filters.endDate}
                    onChange={(e) => handleFilterChange('endDate', e.target.value)}
                    className="w-full h-12 px-4 bg-black/40 border border-emerald-500/10 rounded-xl text-emerald-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 outline-none transition-all duration-300 text-sm [color-scheme:dark]"
                  />
                </div>

                <div className="space-y-3">
                  <label className="block text-[10px] font-black text-emerald-900/40 uppercase tracking-widest pl-1">
                    Trigger Source
                  </label>
                  <select
                    data-testid="deletion-trigger-filter"
                    value={filters.trigger}
                    onChange={(e) => handleFilterChange('trigger', e.target.value)}
                    className="w-full h-12 px-4 bg-black/40 border border-emerald-500/10 rounded-xl text-emerald-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 outline-none transition-all duration-300 text-sm appearance-none cursor-pointer"
                  >
                    <option value="" className="bg-[#0a0a0a]">Global Scopes</option>
                    <option value="manual" className="bg-[#0a0a0a]">Manual Intervention</option>
                    <option value="auto" className="bg-[#0a0a0a]">Automated Protocol</option>
                  </select>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-emerald-500/5 flex justify-end">
                <button
                  data-testid="apply-filter"
                  onClick={() => {
                    setFilters({ merchantId: '', startDate: '', endDate: '', trigger: '' });
                    setPage(1);
                  }}
                  className="px-6 py-2 text-[10px] font-black text-emerald-900/40 hover:text-emerald-400 uppercase tracking-widest transition-colors"
                >
                  Clear Schemas
                </button>
              </div>
            </GlassCard>
          )}

          {error && (
            <div data-testid="error-banner" className="mb-8 p-6 bg-red-500/5 border border-red-500/20 rounded-2xl backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-500">
              <div className="flex items-center gap-4">
                <div className="p-2 bg-red-500/10 rounded-lg">
                  <FileText size={20} className="text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]" />
                </div>
                <div>
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-red-500/60 mb-1">Critical Error</h4>
                  <p className="text-sm text-red-200/80 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}

          {loading ? (
            <GlassCard accent="mantis" className="border-emerald-500/10 bg-emerald-500/[0.02]">
              <div className="text-center py-24">
                <RefreshCw size={48} className="mx-auto text-emerald-500/20 animate-spin" />
                <p className="text-emerald-900/40 mt-6 text-[11px] font-black uppercase tracking-[0.3em]">Synching Audit Records...</p>
              </div>
            </GlassCard>
          ) : (
            <>
              <GlassCard className="p-0 overflow-hidden border-emerald-500/10 bg-emerald-500/[0.01]">
                <div data-testid="audit-log-table" className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-emerald-500/10 bg-emerald-500/[0.03]">
                        {['Session Identity', 'Merchant', 'Trigger', 'Requested At', 'Data Deleted', 'Status'].map((header) => (
                          <th key={header} className="px-8 py-6 text-left text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em]">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-emerald-500/5">
                      {logs.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-8 py-24 text-center">
                            <div className="flex flex-col items-center gap-4">
                              <FileText size={32} className="text-emerald-900/20" />
                              <p className="text-emerald-900/40 text-[11px] font-black uppercase tracking-[0.2em]">No Audit Fragments Found</p>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        logs.map((log) => (
                          <tr key={log.id} className="group hover:bg-emerald-500/[0.04] transition-all duration-300">
                            <td className="px-8 py-6 whitespace-nowrap">
                              <span className="text-sm font-mono text-emerald-100/90 group-hover:text-emerald-400 transition-colors">
                                {log.sessionId.substring(0, 8)}<span className="text-emerald-900/40">...</span>
                              </span>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              <span className="text-sm font-bold text-white/80">{log.merchantId}</span>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              <Badge
                                variant="outline"
                                className={`text-[9px] font-black uppercase tracking-[0.2em] px-3 py-1 rounded-lg border-2 ${
                                  log.deletionTrigger === 'auto'
                                    ? 'border-emerald-500/20 text-emerald-400 bg-emerald-500/5'
                                    : 'border-blue-500/20 text-blue-400 bg-blue-500/5'
                                }`}
                              >
                                {log.deletionTrigger}
                              </Badge>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap text-sm text-emerald-900/60 font-medium">
                              {formatDate(log.requestedAt)}
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              <div className="flex flex-col gap-1">
                                <span className="text-sm font-bold text-emerald-100/80">{log.conversationsDeleted} <span className="text-[10px] font-black uppercase tracking-widest text-emerald-900/40 ml-1">Conversations</span></span>
                                <span className="text-[10px] text-emerald-900/40 font-black uppercase tracking-widest">
                                  {log.messagesDeleted} Messages
                                </span>
                              </div>
                            </td>
                            <td className="px-8 py-6 whitespace-nowrap">
                              {log.completedAt ? (
                                <div className="flex items-center gap-2 text-emerald-400">
                                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)] animate-pulse" />
                                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">Verified</span>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2 text-red-500">
                                  <div className="w-1.5 h-1.5 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">Aborted</span>
                                </div>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </GlassCard>

              {total > pageSize && (
                <div className="mt-10 flex justify-between items-center px-4">
                  <div className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.2em]">
                    Showing <span className="text-emerald-400">{((page - 1) * pageSize) + 1}</span> — <span className="text-emerald-400">{Math.min(page * pageSize, total)}</span> of <span className="text-emerald-400">{total}</span> fragments
                  </div>
                  <div className="flex items-center gap-6">
                    <button
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                      className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-emerald-400 disabled:opacity-20 disabled:cursor-not-allowed hover:bg-white/10 hover:scale-110 active:scale-95 transition-all duration-300"
                    >
                      <ChevronLeft size={18} />
                    </button>
                    <span className="text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em]">
                      Page {page} / {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(page + 1)}
                      disabled={page === totalPages}
                      className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-emerald-400 disabled:opacity-20 disabled:cursor-not-allowed hover:bg-white/10 hover:scale-110 active:scale-95 transition-all duration-300"
                    >
                      <ChevronRight size={18} />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

