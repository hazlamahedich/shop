import { useQuery } from '@tanstack/react-query';
import { Clock, Zap } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface HeatmapData {
  heatmap: number[][]; // [day_of_week][hour]
  peakHour: number;
  peakDay: number;
}

export function PeakHoursHeatmapWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'peak-hours'],
    queryFn: () => analyticsService.getPeakHours(30) as Promise<HeatmapData>,
    staleTime: 60_000,
    refetchInterval: 300_000,
  });

  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  
  return (
    <StatCard
      title="Traffic Density"
      value={isLoading ? '...' : data?.peakHour ? `${data.peakHour}:00` : '--:--'}
      subValue="PEAK_TEMPORAL_NODE"
      icon={<Clock size={18} />}
      accentColor="mantis"
      data-testid="peak-hours-widget"
      isLoading={isLoading}
    >
      <div className="mt-4 space-y-4">
        <div className="grid grid-cols-7 gap-1">
          {days.map((day) => (
            <div key={day} className="text-[8px] font-black text-white/20 text-center uppercase tracking-tighter">{day}</div>
          ))}
          {isLoading ? (
            Array.from({ length: 28 }).map((_, i) => (
              <div key={i} className="h-3 bg-white/5 rounded animate-pulse" />
            ))
          ) : (
            data?.heatmap?.slice(0, 4).map((row, i) => (
              row.slice(10, 17).map((val, j) => (
                <div 
                  key={`${i}-${j}`} 
                  className="h-3 rounded-sm transition-all duration-700 hover:scale-125 hover:z-10 cursor-crosshair border border-white/5"
                  style={{ 
                    backgroundColor: `rgba(0, 245, 212, ${Math.max(0.05, val / 10)})`,
                    boxShadow: val > 7 ? '0 0 10px rgba(0, 245, 212, 0.3)' : 'none'
                  }}
                  title={`Activity Level: ${val}`}
                />
              ))
            ))
          )}
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[9px] font-black text-white/20 uppercase tracking-widest">
           <div className="flex items-center gap-1.5">
              <Zap size={10} className="text-[#00f5d4]/40" />
              <span>SYNC_STABLE</span>
           </div>
           <span className="text-[#00f5d4]/40">4x4_GRID_SAMPLE</span>
        </div>
      </div>
    </StatCard>
  );
}

export default PeakHoursHeatmapWidget;
