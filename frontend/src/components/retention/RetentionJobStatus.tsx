import React, { useState, useEffect } from 'react';
import { Activity, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { Card } from '../ui/Card';

interface RetentionJobStatusProps {
  className?: string;
}

interface SchedulerStatus {
  status: 'healthy' | 'running' | 'idle' | 'error';
  lastRun: string | null;
  nextRun: string | null;
  jobsProcessed: number;
  errors: number;
}

export const RetentionJobStatus: React.FC<RetentionJobStatusProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<SchedulerStatus>({
    status: 'idle',
    lastRun: null,
    nextRun: null,
    jobsProcessed: 0,
    errors: 0,
  });

  useEffect(() => {
    fetchSchedulerStatus();
  }, []);

  const fetchSchedulerStatus = async () => {
    try {
      const response = await fetch('/api/v1/health/scheduler', {
        headers: {
          'X-Internal-Request': 'true',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStatus({
          status: data.status || 'idle',
          lastRun: data.last_run || null,
          nextRun: data.next_run || null,
          jobsProcessed: data.jobs_processed || 0,
          errors: data.errors || 0,
        });
      } else {
        setStatus(prev => ({ ...prev, status: 'error' }));
      }
    } catch (error) {
      setStatus(prev => ({ ...prev, status: 'error' }));
    }
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case 'healthy':
        return <CheckCircle className="text-green-500" size={20} />;
      case 'running':
        return <Activity className="text-blue-500 animate-spin" size={20} />;
      case 'error':
        return <AlertCircle className="text-red-500" size={20} />;
      default:
        return <Clock className="text-gray-500" size={20} />;
    }
  };

  const getStatusColor = () => {
    switch (status.status) {
      case 'healthy':
        return 'bg-green-50 text-green-700';
      case 'running':
        return 'bg-blue-50 text-blue-700';
      case 'error':
        return 'bg-red-50 text-red-700';
      default:
        return 'bg-gray-50 text-gray-700';
    }
  };

  const formatTime = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card className={className}>
      <div style={{ padding: 'var(--card-padding)' }}>
        <div data-testid="retention-job-status">
          <div className="flex justify-between items-start mb-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Data Retention</p>
              <h3 className="text-lg font-semibold text-gray-900 mt-1">
                Retention Job Status
              </h3>
            </div>
            <div className={`p-2 rounded-lg ${getStatusColor()}`}>
              {getStatusIcon()}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Status</span>
              <span data-testid="status-text" className="text-sm font-medium capitalize">
                {status.status}
              </span>
            </div>

            {status.lastRun && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Last run:</span>
                <span data-testid="last-run-time" data-testid-also="last-successful-run" className="text-sm font-medium">
                  Last run: {formatTime(status.lastRun)}
                </span>
              </div>
            )}

            {status.nextRun && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Next run:</span>
                <span data-testid="next-run-time" className="text-sm font-medium text-primary">
                  {formatTime(status.nextRun)}
                </span>
              </div>
            )}

            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
              <span className="text-sm text-gray-600">Jobs processed today</span>
              <span className="text-sm font-medium">{status.jobsProcessed}</span>
            </div>

            {status.errors > 0 && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                <div className="flex items-center gap-2">
                  <AlertCircle size={16} className="text-red-600" />
                  <span className="text-sm text-red-700">
                    {status.errors} error{status.errors !== 1 ? 's' : ''} in last 24h
                  </span>
                </div>
              </div>
            )}
          </div>

          <a
            href="/dashboard/audit-logs"
            className="mt-4 text-sm text-primary font-medium hover:underline flex items-center gap-1"
          >
            View Audit Logs
            <Activity size={14} className="ml-1" />
          </a>
        </div>
      </div>
    </Card>
  );
};
