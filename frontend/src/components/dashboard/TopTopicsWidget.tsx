import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ChevronRight, Download, ArrowUp, ArrowDown, Minus, Sparkles, Hash } from 'lucide-react';
import { analyticsService, TopTopic } from '../../services/analyticsService';
import { StatCard } from './StatCard';

function getTrendIcon(trend: string) {
  switch (trend) {
    case 'up': return <ArrowUp size={10} className="text-[#00f5d4]" />;
    case 'down': return <ArrowDown size={10} className="text-rose-400" />;
    case 'new': return <Sparkles size={10} className="text-amber-400" />;
    default: return <Minus size={10} className="text-white/20" />;
  }
}

function getTrendColor(trend: string) {
  switch (trend) {
    case 'up': return 'text-[#00f5d4] bg-[#00f5d4]/5 border-[#00f5d4]/20';
    case 'down': return 'text-rose-400 bg-rose-400/5 border-rose-400/20';
    case 'new': return 'text-amber-400 bg-amber-400/5 border-amber-400/20';
    default: return 'text-white/40 bg-white/5 border-white/10';
  }
}

export function TopTopicsWidget() {
  const navigate = useNavigate();
  const [days] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'top-topics', days],
    queryFn: () => analyticsService.getTopTopics(days),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const topics = data?.topics ?? [];

  return (
    <StatCard
      title="Semantic Clusters"
      value={isLoading ? '...' : topics.length.toString()}
      subValue="CORE_RECURRING_TOPICS"
      icon={<Hash size={18} />}
      accentColor="mantis"
      data-testid="top-topics-widget"
      isLoading={isLoading}
    >
      <div className="mt-4 space-y-3">
        {topics.length === 0 && !isLoading ? (
          <div className="py-10 text-center border border-white/5 rounded-3xl bg-white/[0.02]">
            <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">No Patterns Detected</span>
          </div>
        ) : (
          topics.map((topic: TopTopic) => (
            <div 
              key={topic.name}
              className="group/item flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/5 hover:border-[#00f5d4]/30 hover:bg-[#00f5d4]/5 transition-all cursor-pointer"
              onClick={() => navigate(`/conversations?search=${encodeURIComponent(topic.name)}`)}
            >
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded-lg border transition-colors ${getTrendColor(topic.trend)}`}>
                   {getTrendIcon(topic.trend)}
                </div>
                <div>
                   <p className="text-[11px] font-black text-white/80 group-hover/item:text-white uppercase tracking-tight">{topic.name}</p>
                    <p className="text-[9px] font-bold text-white/50 uppercase tracking-widest mt-0.5">{topic.queryCount} RECITALS</p>
                </div>
              </div>
              <ChevronRight size={12} className="text-white/10 group-hover/item:text-white/40 group-hover/item:translate-x-0.5 transition-all" />
            </div>
          ))
        )}

         <button className="w-full mt-2 flex items-center justify-between px-4 py-2 text-[9px] font-black text-white/50 hover:text-white/70 transition-colors uppercase tracking-[0.3em]">
           <span>Full Topic Schema</span>
           <Download size={10} />
        </button>
      </div>
    </StatCard>
  );
}

export default TopTopicsWidget;