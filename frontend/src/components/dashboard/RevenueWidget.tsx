import { useQuery } from '@tanstack/react-query';
import { TrendingUp, ShoppingBag, Package } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-blue-100 text-blue-700',
  processing: 'bg-indigo-100 text-indigo-700',
  shipped: 'bg-cyan-100 text-cyan-700',
  delivered: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
  refunded: 'bg-orange-100 text-orange-700',
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
  const avgOrder =
    totalOrders > 0 ? totalRevenue / totalOrders : 0;
  const byStatus: Record<string, number> =
    orderStats?.byStatus && typeof orderStats.byStatus === 'object'
      ? (orderStats.byStatus as Record<string, number>)
      : {};

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
      accentColor="purple"
      isLoading={isLoading}
      data-testid="revenue-widget"
    >
      {topStatuses.length > 0 ? (
        <div className="flex flex-wrap gap-1.5 mt-1">
          {topStatuses.map(([status, count]) => (
            <span
              key={status}
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STATUS_COLORS[status] ?? 'bg-gray-100 text-gray-600'}`}
            >
              <ShoppingBag size={10} />
              {status} &nbsp;{count}
            </span>
          ))}
        </div>
      ) : !isLoading && totalOrders === 0 ? (
        <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
          <Package size={12} /> Shopify orders will appear here once webhooks are active.
        </p>
      ) : null}
    </StatCard>
  );
}

export default RevenueWidget;
