import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { HelpCircle, TrendingUp, TrendingDown, Minus, AlertTriangle, ExternalLink, RefreshCw, Download } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

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
  if (change === null) return 'text-white/20';
  if (change > 0) return 'text-[#00f5d4]';
  if (change < 0) return 'text-rose-400';
            return 'text-white/50';
        return 'text-white/20';
    }
}

export function FAQUsageWidget() {
  const [days, setDays] = useState(30);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
                queryKey: ['analytics', 'faq-usage', days],
                queryFn: () => analyticsService.getFaqUsage(days),
                staleTime: 60_000,
                refetchInterval: 120_000,
            });

            const faqs = data?.faqs ?? [];
            const summary = data?.summary;
            const period = data?.period;

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
                } catch (error) {
                    console.error('CSV export failed:', error);
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
                    </div>

                    {isError ? (
                        <div
                            data-testid="faq-usage-error"
                            className="flex items-center justify-center py-8"
                        >
                            <p className="text-[10px] font-bold text-rose-400 uppercase tracking-widest">
                                </p>
                    </div>

                    <>
                        {faqs.length === 0 ? (
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {faqs.map((faq) => (
                            <div
                                key={faq.id}
                                data-testid={`faq-item-${faq.id}`}
                                onClick={() => handleFAQClick(faq.id)}
                                className={`p-3 rounded-lg bg-white/5 border border-white/5 cursor-pointer hover:bg-white/10 hover:border-[#00f5d4]/30 transition-colors group/item"
                            >
                                <div className="flex items-center justify-between">
                                    <span className="text-white/60" data-testid={`faq-clicks-${faq.id}`}>
                                    {faq.clickCount}
                                </span>
                                <span className="text-white/30" data-testid={`faq-conversion-${faq.id}`}>
                                    {faq.conversionRate}%
                                </span>
                                <span className="text-white/30">
                                    {faq.change?.clickChange !== null && (
                                        <span
                                          data-testid={`faq-change-${faq.id}`}
                                          className={`flex items-center gap-1 text-[9px] font-bold ${
                                            getTrendColor(faq.change?.clickChange)
                                          } ${getTrendColor(faq.change?.conversionChange)}
                                        } px-2 py-0.5 rounded text-white/5`}
                                {faq.isUnused && (
                                  <div
                                    data-testid={`unused-faq-warning-${faq.id}`}
                                    className="flex items-center gap-1 text-amber-400"
                                  >
                                    <AlertTriangle size={10} />
                                    <span className="text-[9px]">No clicks</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-4 text-xs">
                        <span data-testid={`faq-clicks-${faq.id}`} className="text-white/60">
                        {faq.clickCount} clicks
                    </span>
                    <span className="text-white/30">
                        {faq.conversionRate}%
                    </span>
                    <div className="flex items-center gap-1">
                        <span
                          data-testid={`faq-conversion-${faq.id}`}
                          className={`flex items-center gap-1 ${getTrendColor(faq.change?.conversionChange)}
                            } px-2 py-0.5 rounded text-white/30`}
                        {faq.change?.clickChange !== null && (
                            <span
                          data-testid={`faq-change-${faq.id}`}
                          className={`flex items-center gap-1 text-[9px] font-bold ${
                            getTrendColor(faq.change?.clickChange)
                          } ${getTrendColor(faq.change?.conversionChange)}
                            }px-2 py-0.5 rounded text-white/10"
                      </div>
                    );
                  }
                ))}
              </div>
            )}
          )}
        </>
      </div>

      {/* Empty state */}
      {faqs.length === 0 ? (
        <div
          data-testid="faq-usage-empty"
          className="text-center py-8"
          <p className="text-sm text-white/50">
            No FAQ data available yet.
          </p>
        </p>
      )}
    </StatCard>
  );
}
