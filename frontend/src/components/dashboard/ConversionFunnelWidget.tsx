import { useQuery } from '@tanstack/react-query';
import { Target, ChevronRight, ArrowDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface FunnelStage {
  name: string;
  count: number;
  percent: number;
  prevPercent?: number;
  dropoffPercent?: number;
}

interface FunnelData {
  stages: FunnelStage[];
  totalSessions: number;
  overallConversionRate: number;
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
}

export function ConversionFunnelWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'conversion-funnel'],
    queryFn: () => analyticsService.getConversionFunnel(30),
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const funnelData = data as FunnelData | undefined;
  const stages = funnelData?.stages || [];
  const conversionRate = Math.round((funnelData?.overallConversionRate || 0) * 100);

  return (
    <StatCard
      title="Commerce Junction"
      value={isLoading ? '...' : `${conversionRate}%`}
      subValue="CORE_CONVERSION_EFFICIENCY"
      icon={<Target size={18} />}
      accentColor={conversionRate > 3 ? 'mantis' : conversionRate > 1 ? 'yellow' : 'red'}
      data-testid="conversion-funnel-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="py-10 text-center border border-rose-500/20 rounded-3xl bg-rose-500/5">
            <span className="text-[10px] font-black text-rose-500/60 uppercase tracking-widest">Funnel Sync Offline</span>
          </div>
        ) : (
          <div className="space-y-3">
            {stages.map((stage, idx) => (
              <div key={stage.name} className="relative">
                <div className="flex items-center justify-between mb-1.5 px-1">
                   <div className="flex items-center gap-2">
                      <span className="text-[10px] font-black text-white/80 uppercase tracking-tighter">{stage.name}</span>
                      <span className="text-[9px] font-bold text-white/20 uppercase tracking-widest">#{idx + 1}</span>
                   </div>
                   <span className="text-[10px] font-black text-white group-hover:text-[#00f5d4] transition-colors">{stage.count.toLocaleString()}</span>
                </div>
                
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5 p-[1px]">
                  <div
                    className="h-full bg-gradient-to-r from-[#00f5d4]/20 to-[#00f5d4] rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(0,245,212,0.2)]"
                    style={{ width: `${stage.percent}%` }}
                  />
                </div>

                {stage.dropoffPercent !== undefined && stage.dropoffPercent > 0 && (
                   <div className="flex items-center justify-center gap-1 mt-1 opacity-40 hover:opacity-100 transition-opacity">
                      <ArrowDown size={8} className="text-rose-400" />
                      <span className="text-[8px] font-black text-rose-400 uppercase tracking-widest">LEAKAGE: {Math.round(stage.dropoffPercent)}%</span>
                   </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="pt-4 border-t border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#00f5d4] animate-pulse" />
                <span className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em]">MESH_FLOW_OPTIMIZED</span>
            </div>
            <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 rounded-xl border border-white/10 hover:border-[#00f5d4]/40 hover:bg-[#00f5d4]/10 transition-all group/opt">
                <span className="text-[9px] font-black text-[#00f5d4]/60 group-hover/opt:text-[#00f5d4] uppercase tracking-widest">OPTIMIZE</span>
                <ChevronRight size={10} className="text-[#00f5d4]/40 group-hover/opt:text-[#00f5d4]" />
            </button>
        </div>
      </div>
    </StatCard>
  );
}

export default ConversionFunnelWidget;
