import { useQuery } from '@tanstack/react-query';
import { TrendingUp, ShoppingBag, Package } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.1)]',
  confirmed: 'bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]',
  processing: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 shadow-[0_0_10px_rgba(99,102,241,0.1)]',
  shipped: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20 shadow-[0_0_10px_rgba(6,182,212,0.1)]',
  delivered: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]',
  cancelled: 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_10px_rgba(244,63,94,0.1)]',
  refunded: 'bg-orange-500/10 text-orange-400 border-orange-500/20 shadow-[0_0_10px_rgba(249,115,22,0.1)]',
};

function formatCurrency(value: number, currency = 'USD'): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

export function RevenueWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsService.getSummary(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const orderStats = data?.orderStats;
  const totalRevenue = typeof orderStats?.totalRevenue === 'number' ? orderStats.totalRevenue : 0;
  const totalOrders = typeof orderStats?.total === 'number' ? orderStats.total : 0;
  const avgOrder = totalOrders > 0 ? totalRevenue / totalOrders : 0;
  const byStatus: Record<string, number> =
    orderStats?.byStatus && typeof orderStats.byStatus === 'object'
      ? (orderStats.byStatus as Record<string, number>)
      : {};

  const momComparison = orderStats?.momComparison;
  const revenueTrend =
    momComparison?.revenueChangePercent !== null && momComparison?.revenueChangePercent !== undefined
      ? momComparison.revenueChangePercent
      : undefined;

  const topStatuses = Object.entries(byStatus)
    .filter(([, count]) => (count as number) > 0)
    .sort((a, b) => (b[1] as number) - (a[1] as number))
    .slice(0, 4);

  return (
    <StatCard
      title="Revenue (30 days)"
      value={isError ? 'N/A' : formatCurrency(totalRevenue)}
      subValue={
        isError
          ? 'Could not load data'
          : totalOrders > 0
          ? `${totalOrders} orders · Avg ${formatCurrency(avgOrder)}`
          : 'No orders yet'
      }
      icon={<TrendingUp size={18} />}
      trend={revenueTrend}
      accentColor="purple"
      isLoading={isLoading}
      data-testid="revenue-widget"
    >
      {topStatuses.length > 0 ? (
        <div className="flex flex-wrap gap-2 mt-2">
          {topStatuses.map(([status, count]) => (
            <span
              key={status}
              className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[10px] font-bold uppercase tracking-tight border backdrop-blur-sm transition-all duration-300 hover:scale-[1.05] ${STATUS_COLORS[status] ?? 'bg-white/5 text-white/40 border-white/5'}`}
            >
              <ShoppingBag size={10} className="opacity-70" />
              {status} <span className="opacity-50 font-black ml-0.5">{count}</span>
            </span>
          ))}
        </div>
      ) : !isLoading && totalOrders === 0 ? (
        <p className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] flex items-center gap-2 mt-2">
          <Package size={12} className="opacity-30" /> SHOPIFY WEBHOOKS INITIALIZING...
        </p>
      ) : null}
    </StatCard>
  );
}

export default RevenueWidget;
