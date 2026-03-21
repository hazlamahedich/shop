import { useQuery } from '@tanstack/react-query';
import { ShoppingBag, ChevronRight, Package } from 'lucide-react';
import { analyticsService, TopProduct } from '../../services/analyticsService';
import { StatCard } from './StatCard';

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
    <div className="md:col-span-2">
      <StatCard
        title="Inventory Velocity"
        value={isLoading ? '...' : products.length.toString()}
        subValue="TOP_PERFORMING_SKUS"
        icon={<ShoppingBag size={18} />}
        accentColor="mantis"
        data-testid="top-products-widget"
        isLoading={isLoading}
      >
        <div className="mt-4 space-y-2">
          {isError ? (
            <div className="py-10 text-center border border-rose-500/20 rounded-3xl bg-rose-500/5">
              <span className="text-[10px] font-black text-rose-500/60 uppercase tracking-widest">Velocity Data N/A</span>
            </div>
          ) : products.length === 0 && !isLoading ? (
            <div className="py-10 text-center border border-white/5 rounded-3xl bg-white/[0.02]">
              <Package size={24} className="mx-auto text-white/10 mb-2" />
              <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">No Sales Traffic</span>
            </div>
          ) : (
            <div className="space-y-1">
              {products.map((product) => (
                <div key={product.productId} className="flex items-center justify-between p-2 rounded-xl group/item hover:bg-white/5 transition-all border border-transparent hover:border-white/5">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-10 w-10 flex-shrink-0 rounded-lg overflow-hidden border border-white/10 bg-white/5 relative">
                      {product.imageUrl ? (
                        <img src={product.imageUrl} alt={product.title} className="h-full w-full object-cover group-hover/item:scale-110 transition-transform duration-500" />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center text-white/10"><Package size={14} /></div>
                      )}
                      <div className="absolute inset-0 bg-[#00f5d4]/10 opacity-0 group-hover/item:opacity-100 transition-opacity" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[11px] font-black text-white/80 group-hover/item:text-white truncate uppercase tracking-tight">
                        {product.title}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                         <span className="text-[9px] font-black text-[#00f5d4] uppercase tracking-tighter bg-[#00f5d4]/5 px-1.5 py-0.5 rounded border border-[#00f5d4]/10">
                            {product.quantitySold} QTY
                         </span>
                         <span className="text-[8px] font-bold text-white/20 uppercase tracking-widest">REVENUE: {formatRevenue(product.totalRevenue)}</span>
                      </div>
                      {/* Sales Density Indicator */}
                      <div className="mt-1.5 h-1 w-full bg-white/5 rounded-full overflow-hidden flex">
                        <div className="h-full bg-[#00f5d4] shadow-[0_0_5px_rgba(0,245,212,0.5)]" style={{ width: `${Math.min(100, (product.quantitySold / 50) * 100)}%` }} />
                      </div>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-white/10 group-hover/item:text-white/60 group-hover/item:translate-x-1 transition-all" />
                </div>
              ))}
            </div>
          )}
          
          <button className="w-full mt-2 py-2 flex items-center justify-center gap-2 text-[9px] font-black text-white/20 hover:text-white hover:bg-white/5 rounded-xl transition-all uppercase tracking-[0.3em]">
             Full Inventory Scan <ChevronRight size={10} />
          </button>
        </div>
      </StatCard>
    </div>
  );
}

export default TopProductsWidget;
