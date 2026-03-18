import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Funnel, TrendingDown, TrendingUp, ChevronRight } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';

interface FunnelStage {
  name: string;
  count: number;
  percentage: number;
  dropoffFromPrevious: number | null;
}

interface ConversionFunnelData {
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  stages: FunnelStage[];
  overallConversionRate: number;
  momChange: number | null;
}

const STAGE_COLORS = [
  'bg-blue-500',
  'bg-indigo-500',
  'bg-purple-500',
  'bg-pink-500',
  'bg-red-500',
];

export function ConversionFunnelWidget() {
  const navigate = useNavigate();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'conversion-funnel'],
    queryFn: () => analyticsService.getConversionFunnel(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const funnelData = data as ConversionFunnelData | undefined;
  const stages = funnelData?.stages || [];

  return (
    <div
      className="relative overflow-hidden rounded-2xl glass-card border-none shadow-lg"
      data-testid="conversion-funnel-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-400 to-purple-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm font-medium text-white/60 uppercase tracking-wide">
              Conversion Funnel
            </p>
            <p className="text-xs text-white/40 mt-0.5">
              Bot to sale journey
            </p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 ring-4 ring-blue-500/20">
            <Funnel size={18} />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-white/10 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-white/60">Unable to load funnel data</p>
          </div>
        ) : stages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <Funnel size={32} className="text-white/40 mb-2" />
            <p className="text-sm text-white/60">No funnel data yet</p>
            <p className="text-xs text-white/40 mt-1">
              Data will appear after conversations start
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {stages.map((stage, index) => (
                <div key={stage.name}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-white">
                      {stage.name}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-white/60">
                        {stage.count.toLocaleString()}
                      </span>
                      <span className="text-xs font-medium text-white">
                        {stage.percentage}%
                      </span>
                    </div>
                  </div>
                  <div className="relative h-6 bg-white/10 rounded overflow-hidden">
                    <div
                      className={`h-full ${STAGE_COLORS[index]} transition-all duration-500`}
                      style={{ width: `${stage.percentage}%` }}
                    />
                    {index > 0 && stage.dropoffFromPrevious !== null && (
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        {stage.dropoffFromPrevious > 20 ? (
                          <TrendingDown size={12} className="text-red-400" />
                        ) : (
                          <TrendingUp size={12} className="text-green-400" />
                        )}
                        <span
                          className={`text-xs ${
                            stage.dropoffFromPrevious > 20
                              ? 'text-red-400'
                              : 'text-green-400'
                          }`}
                        >
                          -{stage.dropoffFromPrevious}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-white/60">Overall Conversion</p>
                  <div className="flex items-center gap-2">
                    <p className="text-lg font-bold text-white">
                      {funnelData?.overallConversionRate || 0}%
                    </p>
                    {funnelData?.momChange !== null && funnelData?.momChange !== undefined && (
                      <span
                        className={`text-xs font-medium ${
                          funnelData.momChange >= 0
                            ? 'text-green-400'
                            : 'text-red-400'
                        }`}
                      >
                        {funnelData.momChange >= 0 ? '▲' : '▼'}{' '}
                        {Math.abs(funnelData.momChange)}% MoM
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => navigate('/analytics')}
                  className="flex items-center gap-1 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors"
                >
                  View Details
                  <ChevronRight size={12} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ConversionFunnelWidget;
