import { useQuery } from '@tanstack/react-query';
import { Clock, Calendar, CheckCircle } from 'lucide-react';
import { analyticsService, PendingOrder } from '../../services/analyticsService';

function formatCurrency(value: number, currencyCode: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode || 'USD',
  }).format(value);
}

function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch (e) {
    return isoString;
  }
}

export function PendingOrdersWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'pending-orders'],
    queryFn: () => analyticsService.getPendingOrders(5, 0),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const orders: PendingOrder[] = data?.items ?? [];

  return (
    <div
      className="relative overflow-hidden glass-card transition-all duration-300 w-full"
      data-testid="pending-orders-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-amber-400 to-orange-500 opacity-60" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.15)] ring-1 ring-white/5 transition-transform hover:rotate-12">
              <Clock size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/90 uppercase tracking-widest leading-none">
                Pending Orders
              </h3>
              <p className="text-[10px] font-medium text-white/40 uppercase tracking-tighter mt-1">
                Awaiting fulfillment
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-xl bg-white/5 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-white/5 animate-pulse" />
                  <div className="h-3 w-1/4 rounded bg-white/5 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-white/20 text-center py-6 font-medium italic">
            Connection lost. Could not sync orders.
          </p>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center bg-white/[0.02] rounded-2xl border border-white/5">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-3 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
              <CheckCircle size={20} className="text-emerald-400" />
            </div>
            <p className="text-sm font-bold text-white/80 uppercase tracking-widest">FLUX OPTIMIZED</p>
            <p className="text-[10px] font-medium text-white/20 uppercase tracking-tighter mt-1">
              Zero pending fulfillment cycles
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-white/[0.05]">
            <table className="w-full text-sm text-left border-collapse">
              <thead className="text-[10px] text-white/30 bg-white/[0.03] uppercase tracking-wider font-black">
                <tr>
                  <th className="px-4 py-3">Reference</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Value</th>
                  <th className="px-4 py-3 text-right">ETA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03]">
                {orders.map((order) => {
                  const hasDeliveryDate = !!order.estimatedDelivery;
                  return (
                    <tr key={order.orderNumber} className={`transition-all duration-200 group ${hasDeliveryDate ? 'bg-amber-500/[0.03] hover:bg-amber-500/[0.08]' : 'hover:bg-white/[0.02]'}`}>
                      <td className="px-4 py-4">
                        <span className="font-bold text-white/90 tabular-nums tracking-tight">#{order.orderNumber}</span>
                        {order.createdAt && (
                          <div className="text-[10px] text-white/30 font-medium uppercase mt-0.5">
                            {formatDate(order.createdAt)}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-tighter bg-white/5 text-white/60 border border-white/10">
                          {order.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-right text-white font-bold tabular-nums">
                        {formatCurrency(order.total, order.currencyCode)}
                      </td>
                      <td className="px-4 py-4 text-right">
                        {hasDeliveryDate ? (
                          <div className="flex items-center justify-end gap-1.5 text-amber-400 font-bold tabular-nums">
                            <span className="text-[10px]">{formatDate(order.estimatedDelivery!)}</span>
                            <Calendar size={12} className="text-amber-500/50" />
                          </div>
                        ) : (
                          <span className="text-white/20 italic text-[10px] font-medium tracking-tighter uppercase">Undefined</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
