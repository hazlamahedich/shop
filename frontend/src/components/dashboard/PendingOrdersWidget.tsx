import { useQuery } from '@tanstack/react-query';
import { Clock, Calendar } from 'lucide-react';
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
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm w-full"
      data-testid="pending-orders-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-amber-400 to-orange-500 opacity-60" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-50 text-amber-600 ring-4 ring-amber-100">
              <Clock size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 leading-none">
                Pending Orders
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Unfulfilled orders needing attention
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="h-10 w-10 rounded bg-gray-200 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-gray-200 animate-pulse" />
                  <div className="h-3 w-1/4 rounded bg-gray-200 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Could not load pending orders.
          </p>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 mb-2">
              <Clock size={18} className="text-gray-300" />
            </div>
            <p className="text-sm text-gray-400">All caught up!</p>
            <p className="text-xs text-gray-300 mt-0.5">
              No pending orders at the moment.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-500 bg-gray-50/50 border-b border-gray-100">
                <tr>
                  <th className="font-medium px-4 py-2 rounded-tl-lg">Order</th>
                  <th className="font-medium px-4 py-2">Status</th>
                  <th className="font-medium px-4 py-2 text-right">Total</th>
                  <th className="font-medium px-4 py-2 rounded-tr-lg">Estimated Delivery</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {orders.map((order) => {
                  const hasDeliveryDate = !!order.estimatedDelivery;
                  return (
                    <tr key={order.orderNumber} className={`transition-colors ${hasDeliveryDate ? 'bg-amber-50/30 hover:bg-amber-50/60' : 'hover:bg-gray-50/50'}`}>
                      <td className="px-4 py-3">
                        <span className="font-medium text-gray-900">#{order.orderNumber}</span>
                        {order.createdAt && (
                          <div className="text-xs text-gray-400 mt-0.5">
                            {formatDate(order.createdAt)}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                          {order.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-900 font-medium whitespace-nowrap">
                        {formatCurrency(order.total, order.currencyCode)}
                      </td>
                      <td className="px-4 py-3">
                        {hasDeliveryDate ? (
                          <div className="flex items-center gap-1.5 text-amber-700 font-medium">
                            <Calendar size={14} className="text-amber-500" />
                            {formatDate(order.estimatedDelivery!)}
                          </div>
                        ) : (
                          <span className="text-gray-400 italic text-xs">Not specified</span>
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
