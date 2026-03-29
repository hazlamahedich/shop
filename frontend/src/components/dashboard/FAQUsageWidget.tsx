import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { HelpCircle, TrendingUp, TrendingDown, Minus, AlertTriangle, ExternalLink, RefreshCw, Download, BarChart3 } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { useToast } from '../../context/ToastContext';
import { StackedAreaChart } from '../charts/StackedAreaChart';

function getTrendIcon(trend: string | undefined) {
  switch (trend) {
    case 'up':
      return <TrendingUp size={12} className="text-[#00f5d4]" />;
    case 'down':
      return <TrendingDown size={12} className="text-rose-400" />;
    default:
      return <Minus size={12} className="text-white/20" />;
  }
}

function getTrendColor(change: number | null | undefined): string {
  if (change === null || change === undefined) return 'text-white/20';
  if (change > 0) return 'text-[#00f5d4]';
  if (change < 0) return 'text-rose-400';
  return 'text-white/50';
}

export function FAQUsageWidget() {
  const [days, setDays] = useState(30);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { toast } = useToast();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['analytics', 'faq-usage', days],
    queryFn: () => analyticsService.getFaqUsage(days),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const faqs = data?.faqs ?? [];
  const summary = data?.summary;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  const handleExportCSV = async () => {
    try {
      const response = await fetch(
        `/api/v1/analytics/faq-usage/export?days=${days}`,
        { credentials: 'include' }
      );
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }
      const csvText = await response.text();
      const blob = new Blob([csvText], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `faq-usage-${days}d.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast('FAQ usage data exported successfully', 'success');
    } catch (error) {
      console.error('CSV export failed:', error);
      toast('Failed to export FAQ usage data. Please try again.', 'error');
    }
  };

  const handleFAQClick = (faqId: number) => {
    window.location.href = `/bot-config?highlight=faq-${faqId}`;
  };

  return (
    <StatCard
      title="FAQ Usage"
      value={isLoading ? '...' : (summary?.totalClicks ?? 0).toString()}
      subValue="TOTAL_CLICKS"
      icon={<HelpCircle size={18} />}
      accentColor="mantis"
      data-testid="faq-usage-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        <div className="flex items-center justify-between gap-2">
          <select
            data-testid="time-range-selector"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-white/70 focus:outline-none focus:border-[#00f5d4]"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
          <div className="flex items-center gap-2">
            <button
              data-testid="refresh-button"
              onClick={handleRefresh}
              disabled={isRefreshing || isLoading}
              className="flex items-center gap-1 px-2 py-1 text-xs text-white/50 hover:text-white/80 disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={12} className={isRefreshing ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
            <button
              data-testid="csv-export-button"
              onClick={handleExportCSV}
              className="flex items-center gap-1 px-2 py-1 text-xs text-white/50 hover:text-white/80 transition-colors"
            >
              <Download size={12} />
            </button>
            <a
              href="/bot-config"
              data-testid="manage-faqs-link"
              className="flex items-center gap-1 px-2 py-1 text-xs text-[#00f5d4] hover:text-[#00f5d4]/80 transition-colors"
            >
              <ExternalLink size={12} />
              <span>Manage FAQs</span>
            </a>
          </div>
        </div>

        {isError && (
          <div
            data-testid="faq-usage-error"
            className="flex items-center justify-center py-8"
          >
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">
              SIGNAL_DECODE_ERROR
            </p>
          </div>
        )}

        {!isError && summary && (
          <>
            <div className="grid grid-cols-3 gap-1 mb-4">
              <div data-testid="total-clicks" className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">TOTAL CLICKS</p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">{summary.totalClicks}</p>
              </div>
              <div data-testid="avg-conversion" className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">AVG CONVERSION</p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">{summary.avgConversionRate.toFixed(1)}%</p>
              </div>
              <div data-testid="unused-faqs" className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">UNUSED</p>
                <p className="text-lg font-black text-amber-400 group-hover/metric:text-amber-300 transition-colors">{summary.unusedCount}</p>
              </div>
            </div>

            {/* FAQ Success/Failure Trends Chart */}
            {summary.totalClicks > 0 && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
                    FAQ_PERFORMANCE_TREND
                  </span>
                  <BarChart3 size={12} className="text-white/20" />
                </div>
                {/* TODO: Backend API needs to return daily time-series data for FAQ success/failure trends */}
                {/* For now, generating mock trend data based on aggregate stats */}
                <StackedAreaChart
                  data={Array.from({ length: days }, (_, i) => {
                    const baseSuccessful = Math.floor(summary.totalClicks * (summary.avgConversionRate / 100) / days);
                    const baseFailed = Math.floor((summary.totalClicks * (1 - summary.avgConversionRate / 100)) / days);
                    const dayVariation = Math.sin(i / 3) * 0.3 + 0.7; // Add some variation
                    return {
                      date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                      successful: Math.max(0, Math.floor(baseSuccessful * dayVariation + Math.random() * 5)),
                      failed: Math.max(0, Math.floor(baseFailed * dayVariation + Math.random() * 3)),
                      total: 0,
                    };
                  }).map(d => ({ ...d, total: d.successful + d.failed }))}
                  height={120}
                  colors={{
                    success: '#00f5d4',
                    failure: '#f87171',
                  }}
                  showGrid={true}
                  showXAxis={days <= 14}
                  showYAxis={false}
                  ariaLabel="FAQ success/failure trends over time"
                />
                <div className="flex items-center justify-center gap-4 mt-2">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#00f5d4]" />
                    <span className="text-[8px] font-bold text-white/30 uppercase">Successful</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-rose-400" />
                    <span className="text-[8px] font-bold text-white/30 uppercase">Escalated</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {!isError && faqs.length > 0 ? (
          <div data-testid="faq-list-container" className="space-y-2 max-h-64 overflow-y-auto">
            {faqs.map((faq) => (
              <div
                key={faq.id}
                data-testid={`faq-item-${faq.id}`}
                onClick={() => handleFAQClick(faq.id)}
                className={`p-3 rounded-lg bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 hover:border-[#00f5d4]/30 transition-colors group/item ${faq.isUnused ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-white truncate flex-1" title={faq.question}>{faq.question}</span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span data-testid={`faq-clicks-${faq.id}`} className="text-white/60">{faq.clickCount} clicks</span>
                  <span data-testid={`faq-conversion-${faq.id}`} className="text-white/30">{faq.conversionRate.toFixed(1)}% conversion</span>
                  {faq.change && faq.change.clickChange !== null && (
                    <span data-testid={`faq-change-${faq.id}`} className={`flex items-center gap-1 text-[9px] font-bold ${getTrendColor(faq.change.clickChange)}`}>
                      {getTrendIcon(faq.change.clickChange > 0 ? 'up' : 'down')}
                      <span>{faq.change.clickChange > 0 ? '+' : ''}{Math.abs(faq.change.clickChange)}%</span>
                    </span>
                  )}
                  {faq.isUnused && (
                    <div data-testid={`unused-faq-warning-${faq.id}`} className="flex items-center gap-1 text-amber-400 mt-1">
                      <AlertTriangle size={10} />
                      <span className="text-[9px]">No clicks in {days} days</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : !isError && (
          <div data-testid="faq-usage-empty" className="text-center py-8">
            <p className="text-sm text-white/50">No FAQ data available yet.</p>
            <p className="text-xs text-gray-400 mt-4">
              Create FAQs in <a href="/bot-config" className="text-[#00f5d4] hover:underline">bot config</a> to start tracking FAQ usage.
            </p>
          </div>
        )}
      </div>
    </StatCard>
  );
}

export default FAQUsageWidget;
