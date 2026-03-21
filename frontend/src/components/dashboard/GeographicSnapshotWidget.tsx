import { useQuery } from '@tanstack/react-query';
import { Globe, Target } from 'lucide-react';
import { analyticsService, GeographicAnalyticsResponse } from '../../services/analyticsService';
import { StatCard } from './StatCard';

export function GeographicSnapshotWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'geographic'],
    queryFn: () => analyticsService.getGeographic() as Promise<GeographicAnalyticsResponse>,
    staleTime: 60_000,
  });

  const regions = data?.byCountry.slice(0, 5) ?? [];

  return (
    <StatCard
      title="Global Spread"
      value={isLoading ? '...' : regions.length.toString()}
      subValue="ACTIVE_GEOLOCATIONS"
      icon={<Globe size={18} />}
      accentColor="mantis"
      data-testid="geo-snapshot-widget"
      isLoading={isLoading}
    >
      <div className="mt-4 space-y-4">
        <div className="space-y-3">
          {regions.map((region) => (
            <div key={region.country} className="group/geo space-y-1.5 cursor-help">
              <div className="flex items-center justify-between px-1">
                <span className="text-[10px] font-black text-white/80 group-hover/geo:text-[#00f5d4] transition-colors tracking-tight uppercase">
                  REGION::{region.country}
                </span>
                <span className="text-[10px] font-black text-white/40">${region.totalRevenue.toLocaleString()}</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                <div 
                  className="h-full bg-gradient-to-r from-[#00f5d4]/20 to-[#00f5d4] transition-all duration-1000 group-hover/geo:opacity-100"
                  style={{ width: `${Math.min(100, (region.totalRevenue / (regions[0]?.totalRevenue || 1)) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#00f5d4] animate-ping" />
                <span className="text-[9px] font-black text-white/20 uppercase tracking-[0.2em]">MESH_COVERAGE_INTACT</span>
            </div>
            <div className="flex items-center gap-2 bg-[#00f5d4]/5 px-2 py-1 rounded border border-[#00f5d4]/20">
               <Target size={10} className="text-[#00f5d4]" />
               <span className="text-[8px] font-black text-[#00f5d4] uppercase tracking-tighter">NODE_ACTIVE</span>
            </div>
        </div>
      </div>
    </StatCard>
  );
}

export default GeographicSnapshotWidget;
