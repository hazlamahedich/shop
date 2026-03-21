import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, Zap, BarChart3, Activity } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { costTrackingService } from '../../services/costTracking';
import type { CostSummary } from '../../types/cost';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from './StatCard';

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

export function FinancialOverviewWidget() {
  const navigate = useNavigate();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  const { data: summaryData, isLoading: revLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsService.getSummary(),
    staleTime: 30_000,
  });

  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];

  const { data: costEnvelope, isLoading: costLoading } = useQuery({
    queryKey: ['costs', 'summary', 'monthly'],
    queryFn: () => costTrackingService.getCostSummary({ dateFrom: monthStart }),
    staleTime: 30_000,
  });

  const isLoading = revLoading || costLoading;
  const orderStats = summaryData?.orderStats;
  const costData = costEnvelope?.data as CostSummary | undefined;

  const totalRevenue = orderStats?.totalRevenue ?? 0;
  const totalCost = costData?.totalCostUsd ?? 0;
  const roi = totalCost > 0 ? totalRevenue / totalCost : 0;
  const revenueTrend = orderStats?.momComparison?.revenueChangePercent;

  return (
    <StatCard
      title="Economic Telemetry"
      value={isLoading ? '...' : formatCurrency(totalRevenue)}
      subValue="TOTAL_NETWORK_REVENUE"
      icon={<BarChart3 size={18} />}
      accentColor="mantis"
      data-testid="financial-overview-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        <div className="grid grid-cols-2 gap-2">
           <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/card">
              <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">AI_OVERHEAD</p>
              <p className="text-lg font-black text-white group-hover/card:text-rose-400 transition-colors">${totalCost.toFixed(2)}</p>
              <div className="mt-2 flex items-center gap-1">
                 <Zap size={10} className="text-rose-400/40" />
                 <span className="text-[8px] font-black text-white/20 uppercase tracking-[0.2em]">Tokens active</span>
              </div>
           </div>
           <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/card">
              <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">ROI_COEFFICIENT</p>
              <p className="text-lg font-black text-[#00f5d4] group-hover/card:scale-110 origin-left transition-transform">{roi.toFixed(1)}x</p>
              <div className="mt-2 flex items-center gap-1">
                 <Activity size={10} className="text-[#00f5d4]/40" />
                 <span className="text-[8px] font-black text-white/20 uppercase tracking-[0.2em]">Yield density</span>
              </div>
           </div>
        </div>

        <div className="bg-white/5 border border-white/5 p-4 rounded-xl">
           <div className="flex items-center justify-between mb-3 text-[9px] font-black text-white/20 uppercase tracking-widest">
              <span>MOM_COMPARISON</span>
              <span className={revenueTrend && revenueTrend >= 0 ? 'text-[#00f5d4]' : 'text-rose-400'}>
                 {revenueTrend && revenueTrend >= 0 ? '+' : ''}{revenueTrend?.toFixed(1)}%
              </span>
           </div>
           <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden flex gap-1">
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <div 
                  key={i} 
                  className={`flex-1 rounded-full transition-all duration-700 ${i < 6 ? 'bg-[#00f5d4]/40 shadow-[0_0_8px_rgba(0,245,212,0.2)]' : 'bg-white/5'}`}
                  style={{ transitionDelay: `${i * 100}ms` }}
                />
              ))}
           </div>
        </div>

        <button
          onClick={() => navigate('/costs')}
          className="w-full flex items-center justify-between px-4 py-2 bg-[#00f5d4]/5 hover:bg-[#00f5d4]/10 border border-[#00f5d4]/10 rounded-xl transition-all group/btn"
        >
          <span className="text-[9px] font-black text-[#00f5d4]/60 group-hover/btn:text-[#00f5d4] uppercase tracking-[0.3em]">Full Audit Trails</span>
           <TrendingUp size={12} className="text-[#00f5d4]/40" />
        </button>
      </div>
    </StatCard>
  );
}

export default FinancialOverviewWidget;
