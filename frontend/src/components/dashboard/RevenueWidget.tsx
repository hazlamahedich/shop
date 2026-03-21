import { useQuery } from '@tanstack/react-query';
import { ShoppingBag, Package, DollarSign } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-amber-400 border-amber-400/20 bg-amber-400/5',
  confirmed: 'text-blue-400 border-blue-400/20 bg-blue-400/5',
  processing: 'text-indigo-400 border-indigo-400/20 bg-indigo-400/5',
  shipped: 'text-cyan-400 border-cyan-400/20 bg-cyan-400/5',
  delivered: 'text-[#00f5d4] border-[#00f5d4]/20 bg-[#00f5d4]/5',
  cancelled: 'text-rose-400 border-rose-400/20 bg-rose-400/5',
  refunded: 'text-orange-400 border-orange-400/20 bg-orange-400/5',
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
      title="Revenue Stream"
      value={isError ? 'ERR' : formatCurrency(totalRevenue)}
      subValue="GROSS_CAPITAL_30D"
      icon={<DollarSign size={18} />}
      trend={revenueTrend}
      accentColor="purple"
      isLoading={isLoading}
      data-testid="revenue-widget"
    >
      <div className="space-y-4 mt-4">
        <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/hex">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">TOTAL_ORDERS</p>
                <p className="text-xl font-black text-white group-hover/hex:text-purple-400 transition-colors">{totalOrders}</p>
            </div>
            <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/hex">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">AVG_TICKET</p>
                <p className="text-xl font-black text-white group-hover/hex:text-purple-400 transition-colors">{formatCurrency(avgOrder)}</p>
            </div>
        </div>

        {topStatuses.length > 0 ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
                <span className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em]">FULFILLMENT_PIPELINE</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {topStatuses.map(([status, count]) => (
                <div
                  key={status}
                  className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-[10px] font-black uppercase tracking-tighter transition-all hover:bg-white/10 ${STATUS_COLORS[status] ?? 'text-white/40 border-white/10 bg-white/5'}`}
                >
                  <ShoppingBag size={10} strokeWidth={3} />
                  <span>{status}</span>
                  <span className="opacity-40">{count}</span>
                </div>
              ))}
            </div>
          </div>
        ) : !isLoading && totalOrders === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 opacity-30 grayscale">
            <Package size={24} className="text-white/20" />
            <p className="text-[9px] font-black uppercase tracking-[0.3em] mt-2">LINK_OFFLINE</p>
          </div>
        ) : null}

        <div className="flex items-center justify-between pt-2 border-t border-white/5">
           <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.4em]">MARKET_TELEMETRY_PASS</span>
           <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)] animate-pulse" />
        </div>
      </div>
    </StatCard>
  );
}

export default RevenueWidget;
