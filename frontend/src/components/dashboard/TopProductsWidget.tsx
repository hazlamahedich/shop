import { useQuery } from '@tanstack/react-query';
import { ShoppingBag, Image as ImageIcon } from 'lucide-react';
import { analyticsService, TopProduct } from '../../services/analyticsService';

function formatRevenue(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

export function TopProductsWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'top-products'],
    queryFn: () => analyticsService.getTopProducts(30, 5),
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const products: TopProduct[] = data?.items ?? [];

  return (
    <div
      className="relative overflow-hidden rounded-2xl glass-card border-none shadow-lg col-span-1 lg:col-span-2"
      data-testid="top-products-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-pink-400 to-orange-400 opacity-60" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-pink-500/10 text-pink-400 ring-4 ring-pink-500/20">
              <ShoppingBag size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white leading-none">
                Top Products
              </h3>
              <p className="text-xs text-white/60 mt-0.5">
                By quantity sold (Last 30 Days)
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="h-12 w-12 rounded bg-white/10 animate-pulse flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-white/10 animate-pulse" />
                  <div className="h-3 w-1/4 rounded bg-white/10 animate-pulse" />
                </div>
                <div className="flex flex-col items-end gap-2">
                   <div className="h-4 w-16 rounded bg-white/10 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-white/60 text-center py-4">
            Could not load top products.
          </p>
        ) : products.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5 mb-2">
              <ShoppingBag size={18} className="text-white/40" />
            </div>
            <p className="text-sm text-white/60">No top products yet.</p>
            <p className="text-xs text-white/40 mt-0.5">
              Top selling products will appear once orders are placed.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-white/60 bg-white/5 border-b border-white/10">
                <tr>
                  <th className="font-medium px-4 py-2 rounded-tl-lg">Product</th>
                  <th className="font-medium px-4 py-2 text-right">Qty</th>
                  <th className="font-medium px-4 py-2 text-right rounded-tr-lg">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {products.map((product) => (
                  <tr key={product.productId} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        {product.imageUrl ? (
                          <div className="h-10 w-10 flex-shrink-0 rounded-lg overflow-hidden border border-white/10 bg-white/5">
                            <img src={product.imageUrl} alt={product.title} className="h-full w-full object-cover" />
                          </div>
                        ) : (
                          <div className="h-10 w-10 flex-shrink-0 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white/40">
                            <ImageIcon size={16} />
                          </div>
                        )}
                        <span className="font-medium text-white line-clamp-2 max-w-[200px] sm:max-w-xs" title={product.title}>
                          {product.title}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-medium text-white/80 bg-white/10 px-2 py-0.5 rounded-md">
                        {product.quantitySold}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-white font-medium whitespace-nowrap">
                      {formatRevenue(product.totalRevenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default TopProductsWidget;
