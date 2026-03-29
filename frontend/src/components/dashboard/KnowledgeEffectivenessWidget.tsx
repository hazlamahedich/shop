import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { GitCompare, Target, Zap, Wifi, WifiOff, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { getDashboardWebSocketService, closeDashboardWebSocket } from '../../services/dashboardWebSocketService';
import { StatCard } from './StatCard';
import { DonutGauge } from '../charts/DonutChart';
import { MiniAreaChart } from '../charts/AreaChart';

interface KnowledgeEffectivenessData {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;
  avgConfidence: number | null;
  trend: number[];
  lastUpdated: string;
  dailyData?: Array<{ date: string; rate: number; count: number }>; // NEW: For sparkline
}

export function KnowledgeEffectivenessWidget() {
  const queryClient = useQueryClient();
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'knowledge-effectiveness'],
    queryFn: () => analyticsService.getKnowledgeEffectiveness(),
    staleTime: 10_000, // 10 seconds - reduced from 30s
    refetchInterval: false, // Disabled - using WebSocket instead
    refetchOnWindowFocus: true, // Enable refresh on window focus
  });

  // Also query connection status
  useQuery({
    queryKey: ['dashboard', 'websocket', 'status'],
    queryFn: () => Promise.resolve({ connected: false, timestamp: null }),
    staleTime: 0,
    refetchInterval: false,
  });

  useEffect(() => {
    // Get merchant ID from environment or use default
    const merchantId = parseInt(import.meta.env?.VITE_MERCHANT_ID || '1', 10);
    const wsService = getDashboardWebSocketService(merchantId);

    // Connect to WebSocket
    wsService.connect(queryClient);

    // Check initial connection status
    const status = wsService.getConnectionStatus();
    setIsWebSocketConnected(status.connected);

    // Poll connection status
    const statusInterval = setInterval(() => {
      const currentStatus = wsService.getConnectionStatus();
      setIsWebSocketConnected(currentStatus.connected);
    }, 5000);

    return () => {
      clearInterval(statusInterval);
      // Don't disconnect on unmount - keep connection alive for other widgets
    };
  }, [queryClient]);

  const effectivenessData = data as KnowledgeEffectivenessData | undefined;
  const total = effectivenessData?.totalQueries || 0;
  const resolved = effectivenessData?.successfulMatches || 0;
  const rate = total > 0 ? Math.round((resolved / total) * 100) : 0;

  // Calculate trend change (compare last 7 days to previous 7 days)
  const trend = effectivenessData?.trend || [];
  const recentTrend = trend.slice(-7);
  const previousTrend = trend.slice(-14, -7);
  const avgRecent = recentTrend.length > 0 ? recentTrend.reduce((a, b) => a + b, 0) / recentTrend.length : 0;
  const avgPrevious = previousTrend.length > 0 ? previousTrend.reduce((a, b) => a + b, 0) / previousTrend.length : 0;
  const trendChange = avgPrevious > 0 ? ((avgRecent - avgPrevious) / avgPrevious) * 100 : 0;

  // Determine color zone
  const getColorZone = () => {
    if (rate >= 80) return 'green';
    if (rate >= 60) return 'yellow';
    return 'red';
  };

  // Prepare sparkline data
  const sparklineData = (effectivenessData?.dailyData || effectivenessData?.trend || []).slice(-14).map((val, idx) => {
    if (typeof val === 'number') {
      return { name: `Day ${idx + 1}`, value: val * 100 };
    }
    return { name: val.date, value: val.rate * 100 };
  });

  return (
    <StatCard
      title="Knowledge Effectiveness"
      value={isLoading ? '...' : `${rate}%`}
      subValue="CORE_RELIABILITY_SCORE"
      icon={<GitCompare size={18} />}
      accentColor={rate >= 80 ? 'mantis' : rate >= 60 ? 'orange' : 'red'}
      data-testid="knowledge-effectiveness-widget"
      isLoading={isLoading}
      miniChart={
        !isLoading && (
          <div className="flex items-center gap-4 mt-4">
            {/* Donut Gauge */}
            <DonutGauge
              value={rate}
              maxValue={100}
              width={100}
              height={100}
              showLabel={false}
            />
            <div className="flex-1">
              {/* Mini sparkline chart */}
              <div className="mb-2">
                {sparklineData.length > 0 && (
                  <MiniAreaChart
                    data={sparklineData}
                    dataKey="value"
                    height={50}
                    color={rate >= 80 ? '#00f5d4' : rate >= 60 ? '#fb923c' : '#f87171'}
                  />
                )}
              </div>
              {/* Trend indicator */}
              <div className="flex items-center gap-2 text-[10px]">
                {trendChange > 5 ? (
                  <div className="flex items-center gap-1 text-[#00f5d4]">
                    <TrendingUp size={12} />
                    <span className="font-black">+{trendChange.toFixed(1)}%</span>
                  </div>
                ) : trendChange < -5 ? (
                  <div className="flex items-center gap-1 text-rose-400">
                    <TrendingDown size={12} />
                    <span className="font-black">{trendChange.toFixed(1)}%</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-white/40">
                    <span className="font-black">Stable</span>
                  </div>
                )}
                <span className="text-white/30">14-day trend</span>
              </div>
            </div>
          </div>
        )
      }
      expandable
    >
      {/* Connection Status Indicator */}
      <div className="flex items-center justify-end mb-2">
        {isWebSocketConnected ? (
          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00f5d4]/5 border border-[#00f5d4]/10 rounded">
            <Wifi size={10} className="text-[#00f5d4]" />
            <span className="text-[9px] font-black text-[#00f5d4] uppercase tracking-wider">Live</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2 py-0.5 bg-white/5 border border-white/5 rounded">
            <WifiOff size={10} className="text-white/30" />
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">Offline</span>
          </div>
        )}
      </div>

      <div className="space-y-4 mt-4">
        {isError ? (
           <div className="flex items-center justify-center py-8">
             <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">SIGNAL_DECAP_ERROR</p>
           </div>
        ) : (
          <>
            <div className="relative group/gauge">
               <div className="flex items-center justify-between mb-2">
                  <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">AUTONOMOUS_RESOLUTION</span>
                  <span className="text-[10px] font-black text-[#00f5d4]">{rate}%</span>
               </div>
               <div className="h-6 w-full bg-white/5 rounded-xl border border-white/5 overflow-hidden p-1 relative">
                  <div
                    className="h-full bg-gradient-to-r from-[#00f5d4]/40 to-[#00f5d4] rounded-lg transition-all duration-1000 shadow-[0_0_15px_rgba(0,245,212,0.3)]"
                    style={{ width: `${rate}%` }}
                  />
                  <div className="absolute inset-y-0 left-0 flex items-center px-3">
                     <span className="text-[9px] font-black text-white/40 group-hover/gauge:text-white/80 transition-colors uppercase">LINK_ESTABLISHED</span>
                  </div>
               </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
                <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                   <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">RESOLVED</p>
                   <p className="text-xl font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">{resolved}</p>
                   <Target size={12} className="mt-2 text-white/10 group-hover/metric:text-[#00f5d4]/40 transition-colors" />
                </div>
                <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                   <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">SESSIONS</p>
                   <p className="text-xl font-black text-white">{total}</p>
                   <Zap size={12} className="mt-2 text-white/10" />
                </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.2em]">INTEL_SYNC_ACTIVE</span>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00f5d4]/5 border border-[#00f5d4]/10 rounded text-[9px] font-black text-[#00f5d4]">
                   HIGH_CONF_AUTO_PASS
                </div>
            </div>

            {/* Last Updated Timestamp */}
            {effectivenessData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(effectivenessData.lastUpdated).toLocaleTimeString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default KnowledgeEffectivenessWidget;
