import React, { useState, useEffect } from 'react';
import { FileText, Filter, RefreshCw, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '../ui/Card';

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

  useEffect(() => {
    fetchLogs();
  }, [page, filters]);

  const fetchLogs = async () => {
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
  };

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
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 data-testid="audit-logs-heading" className="text-2xl font-bold text-gray-900">
                Retention Audit Logs
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Track data deletion activities for GDPR/CCPA compliance
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                  showFilters ? 'bg-primary text-white' : 'bg-gray-100 text-gray-700'
                }`}
              >
                <Filter size={16} />
                Filters
              </button>
              <button
                onClick={handleRefresh}
                data-testid="refresh-audit-logs"
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg flex items-center gap-2 hover:bg-gray-200"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-primary text-white rounded-lg flex items-center gap-2 hover:bg-primary/90"
              >
                <Download size={16} />
                Export CSV
              </button>
            </div>
          </div>

          {showFilters && (
            <Card className="mb-4">
              <div style={{ padding: 'var(--card-padding)' }}>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Merchant ID
                    </label>
                    <input
                      type="number"
                      value={filters.merchantId}
                      onChange={(e) => handleFilterChange('merchantId', e.target.value)}
                      placeholder="All merchants"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      data-testid="start-date"
                      value={filters.startDate}
                      onChange={(e) => handleFilterChange('startDate', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      data-testid="end-date"
                      value={filters.endDate}
                      onChange={(e) => handleFilterChange('endDate', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Trigger Type
                    </label>
                    <select
                      data-testid="deletion-trigger-filter"
                      value={filters.trigger}
                      onChange={(e) => handleFilterChange('trigger', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      <option value="">All triggers</option>
                      <option value="manual">Manual</option>
                      <option value="auto">Auto</option>
                    </select>
                  </div>
                </div>

                <div className="mt-4 flex justify-end">
                  <button
                    data-testid="apply-filter"
                    onClick={() => {
                      setFilters({ merchantId: '', startDate: '', endDate: '', trigger: '' });
                      setPage(1);
                    }}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            </Card>
          )}

          {error && (
            <div data-testid="error-banner" className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-red-600" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            </div>
          )}

          {loading ? (
            <Card>
              <div style={{ padding: 'var(--card-padding)' }} className="text-center py-12">
                <RefreshCw size={32} className="mx-auto text-gray-400 animate-spin" />
                <p className="text-gray-500 mt-4">Loading audit logs...</p>
              </div>
            </Card>
          ) : (
            <>
              <Card>
                <div style={{ padding: '0' }}>
                  <div data-testid="audit-log-table" className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Session ID
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Merchant
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Trigger
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Requested At
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Data Deleted
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {logs.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                              No audit logs found
                            </td>
                          </tr>
                        ) : (
                          logs.map((log) => (
                            <tr key={log.id} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                {log.sessionId.substring(0, 8)}...
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {log.merchantId}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span
                                  data-testid="deletion-trigger"
                                  className={`px-2 py-1 inline-flex text-xs font-semibold rounded-full ${
                                    log.deletionTrigger === 'auto'
                                      ? 'bg-blue-100 text-blue-700'
                                      : 'bg-purple-100 text-purple-700'
                                  }`}
                                >
                                  {log.deletionTrigger}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatDate(log.requestedAt)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <div className="flex flex-col">
                                  <span>{log.conversationsDeleted} conversations</span>
                                  <span className="text-xs text-gray-400">
                                    {log.messagesDeleted} messages
                                  </span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                {log.completedAt ? (
                                  <span className="px-2 py-1 inline-flex text-xs font-semibold rounded-full bg-green-100 text-green-700">
                                    Completed
                                  </span>
                                ) : (
                                  <span className="px-2 py-1 inline-flex text-xs font-semibold rounded-full bg-red-100 text-red-700">
                                    Failed
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </Card>

              {total > pageSize && (
                <div className="mt-4 flex justify-between items-center">
                  <div className="text-sm text-gray-500">
                    Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} results
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(page - 1)}
                      disabled={page === 1}
                      className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <span className="px-3 py-1 text-sm text-gray-700">
                      Page {page} of {totalPages}
                    </span>
                    <button
                      onClick={() => setPage(page + 1)}
                      disabled={page === totalPages}
                      className="px-3 py-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                    >
                      <ChevronRight size={16} />
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
