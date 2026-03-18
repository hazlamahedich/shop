import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Activity, BarChart3, Download, RefreshCw, Loader2, Mic } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '../../services/analyticsService';
import type { WidgetAnalyticsMetrics } from '../../services/analyticsService';

type PeriodOption = '7' | '30' | '90';

const PERIOD_LABELS: Record<PeriodOption, string> = {
  '7': '7 days',
  '30': '30 days',
  '90': '90 days',
};

function TrendIndicator({ trend }: { trend: number | undefined }) {
  if (trend === undefined || trend === 0) return null;
  const isUp = trend > 0;
  const Icon = isUp ? TrendingUp : TrendingDown;
  const colorClass = isUp ? 'text-green-600' : 'text-red-600';
  const bgClass = isUp ? 'bg-green-50' : 'bg-red-50';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${bgClass} ${colorClass}`}>
      <Icon size={12} />
      {isUp ? '+' : ''}{Math.abs(trend).toFixed(1)}%
    </span>
  );
}

function MetricCard({
  label,
  value,
  unit = '%',
  trend,
  icon: Icon,
}: {
  label: string;
  value: number;
  unit?: string;
  trend?: number;
  icon: React.ElementType;
}) {
  return (
    <div className="flex flex-col p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <Icon size={14} className="text-gray-400" />
          <span className="text-xs text-gray-500">{label}</span>
        </div>
        <TrendIndicator trend={trend} />
      </div>
      <span className="text-xl font-semibold text-gray-900">
        {value.toFixed(1)}{unit}
      </span>
    </div>
  );
}

export function WidgetAnalyticsWidget() {
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodOption>('30');
  const [isExporting, setIsExporting] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery<WidgetAnalyticsMetrics>({
    queryKey: ['widget-analytics', selectedPeriod],
    queryFn: () => analyticsService.getWidgetMetrics(parseInt(selectedPeriod)),
    refetchInterval: 60000,
  });

  const metrics = data?.metrics;
  const trends = data?.trends;
  const performance = data?.performance;

  const handleExport = async () => {
    if (!data?.merchantId) return;
    setIsExporting(true);
    try {
      const endDate = new Date().toISOString().split('T')[0];
      const startDate = new Date(Date.now() - parseInt(selectedPeriod) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      const blob = await analyticsService.exportWidgetAnalytics(startDate, endDate, data.merchantId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `widget-analytics-${startDate}-${endDate}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  if (isError) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4" data-testid="widget-analytics-widget">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Widget Analytics</h3>
        </div>
        <div className="flex items-center justify-center h-32 text-gray-500">
          <Activity size={16} className="mr-2" />
          <span>Failed to load analytics data</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4" data-testid="widget-analytics-widget">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Widget Analytics</h3>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {(Object.keys(PERIOD_LABELS) as PeriodOption[]).map((period) => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                  selectedPeriod === period
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {PERIOD_LABELS[period]}
              </button>
            ))}
          </div>
          <button
            onClick={() => refetch()}
            className="p-1.5 text-gray-400 hover:text-gray-600"
            title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="animate-spin h-6 w-6 text-indigo-600" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            <MetricCard
              label="Open Rate"
              value={metrics?.openRate ?? 0}
              trend={trends?.openRateChange}
              icon={TrendingUp}
            />
            <MetricCard
              label="Message Rate"
              value={metrics?.messageRate ?? 0}
              trend={trends?.messageRateChange}
              icon={BarChart3}
            />
            <MetricCard
              label="Quick Reply"
              value={metrics?.quickReplyRate ?? 0}
              icon={Activity}
            />
            <MetricCard
              label="Voice Input"
              value={metrics?.voiceInputRate ?? 0}
              icon={Mic}
            />
            <MetricCard
              label="Proactive"
              value={metrics?.proactiveConversionRate ?? 0}
              icon={TrendingUp}
            />
            <MetricCard
              label="Carousel"
              value={metrics?.carouselEngagementRate ?? 0}
              icon={BarChart3}
            />
          </div>

          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-700">Performance</h4>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-xs text-gray-500">Avg Load</div>
                <div className="text-sm font-semibold text-gray-900">
                  {performance?.avgLoadTimeMs?.toFixed(0) ?? 0}ms
                </div>
              </div>
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-xs text-gray-500">P95 Load</div>
                <div className="text-sm font-semibold text-gray-900">
                  {performance?.p95LoadTimeMs?.toFixed(0) ?? 0}ms
                </div>
              </div>
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-xs text-gray-500">Bundle</div>
                <div className="text-sm font-semibold text-gray-900">
                  {performance?.bundleSizeKb?.toFixed(0) ?? 0}KB
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end mt-4">
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting ? (
                <Loader2 className="animate-spin h-4 w-4" />
              ) : (
                <Download size={14} />
              )}
              {isExporting ? 'Exporting...' : 'Export CSV'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default WidgetAnalyticsWidget;
