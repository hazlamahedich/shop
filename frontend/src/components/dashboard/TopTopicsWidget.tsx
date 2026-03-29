import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ChevronRight, Download, ArrowUp, ArrowDown, Minus, Sparkles, Hash, BarChart3, Lock } from 'lucide-react';
import { analyticsService, TopTopic } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { BarChart } from '../charts/BarChart';
import { sanitizeEncryptedText, isEncrypted } from '../../utils/encryption';

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

/**
 * Format topic name for display
 * Shows readable name or handles encrypted/failed decryption topics
 */
function formatTopicName(topicName: string): string {
  if (!topicName) return '[Unknown Topic]';

  // Check if backend marked as failed decryption
  if (topicName.startsWith('[Encrypted]')) {
    // Show the backend's marker for failed decryption
    return topicName;
  }

  // Check if still encrypted (backend decryption attempt failed but wasn't marked)
  if (isEncrypted(topicName)) {
    // This should NOT happen if backend properly attempted decryption
    const shortId = topicName.substring(0, 8);
    return `Topic #${shortId} (Decryption Failed)`;
  }

  // Truncate very long names
  if (topicName.length > 50) {
    return `${topicName.substring(0, 47)}...`;
  }

  return topicName;
}

export function TopTopicsWidget() {
  const navigate = useNavigate();
  const [days] = useState(7);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'top-topics', days],
    queryFn: () => analyticsService.getTopTopics(days),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const topics = data?.topics ?? [];

  // Prepare data for bar chart
  const chartData = topics.slice(0, 8).map(topic => ({
    name: formatTopicName(topic.name),
    count: topic.queryCount,
    trend: topic.trend,
    color:
      topic.trend === 'up' ? '#00f5d4' :
      topic.trend === 'down' ? '#f87171' :
      topic.trend === 'new' ? '#fb923c' :
      '#a78bfa',
  }));

  // Handle bar click - navigate to filtered conversations
  const handleBarClick = (data: any) => {
    const formattedName = formatTopicName(data.name);
    const topic = topics.find(t => formatTopicName(t.name) === formattedName);
    if (topic) {
      navigate(`/conversations?search=${encodeURIComponent(topic.name)}`);
    }
  };

  return (
    <StatCard
      title="Semantic Clusters"
      value={isLoading ? '...' : topics.length.toString()}
      subValue="CORE_RECURRING_TOPICS"
      icon={<Hash size={18} />}
      accentColor="purple"
      data-testid="top-topics-widget"
      isLoading={isLoading}
      expandable
      className="!pb-2"
    >
      {/* Interactive Bar Chart - Top Topics */}
      {!isLoading && chartData.length > 0 && (
        <div className="mb-4 rounded-xl p-4 backdrop-blur-sm" style={{ background: 'linear-gradient(to bottom right, rgba(168, 85, 247, 0.6), rgba(147, 51, 234, 0.5))', border: '2px solid rgba(168, 85, 247, 0.7)' }}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-black uppercase tracking-wider" style={{ color: '#FFFFFF' }}>
              TOP_QUERIES
            </span>
            <BarChart3 size={14} style={{ color: '#C084FC' }} />
          </div>
          <div className="rounded-lg" style={{ background: 'rgba(0, 0, 0, 0.5)', padding: '12px', border: '1px solid rgba(167, 139, 250, 0.3)' }}>
            <BarChart
              data={chartData}
              dataKey="count"
              xAxisKey="name"
              horizontal
              height={200}
              color="#9333EA"
              onClick={handleBarClick}
              showTooltip={true}
              showGrid={false}
              showXAxis={false}
              showYAxis={false}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
              barSize={24}
              ariaLabel="Top topics by query count"
            />
          </div>
          <p className="text-[10px] mt-3 text-center font-black uppercase tracking-wide" style={{ color: '#FFFFFF' }}>
            Click bar to view conversations
          </p>
        </div>
      )}

      <div className="mt-4 space-y-3 !mb-0">
        {topics.length === 0 && !isLoading ? (
          <div className="py-10 text-center border border-white/10 rounded-3xl bg-white/5">
            <span className="text-[11px] font-black text-white/40 uppercase tracking-widest">No Patterns Detected</span>
          </div>
        ) : (
          topics.map((topic: TopTopic) => (
            <div
              key={topic.name}
              className={`group/item flex items-center justify-between p-3 rounded-2xl border hover:border-[#a78bfa]/50 hover:bg-[#a78bfa]/10 transition-all cursor-pointer ${
                isEncrypted(topic.name)
                  ? 'bg-amber-500/10 border-amber-500/30'
                  : 'bg-white/10 border-white/20'
              }`}
              onClick={() => navigate(`/conversations?search=${encodeURIComponent(topic.name)}`)}
            >
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded-lg border transition-colors ${getTrendColor(topic.trend)}`}>
                   {getTrendIcon(topic.trend)}
                </div>
                <div className="flex items-center gap-2">
                  <div>
                    <p className="text-[11px] font-black text-white group-hover/item:text-purple-300 uppercase tracking-tight">
                      {formatTopicName(topic.name)}
                    </p>
                    <p className="text-[9px] font-bold text-white/70 uppercase tracking-widest mt-0.5">{topic.queryCount} RECITALS</p>
                  </div>
                  {isEncrypted(topic.name) && (
                    <div className="flex items-center gap-1 px-2 py-1 rounded bg-amber-500/20 border border-amber-500/40" title="Topic name is encrypted">
                      <Lock size={10} className="text-amber-400" />
                      <span className="text-[8px] font-black text-amber-300 uppercase tracking-wider">Encrypted</span>
                    </div>
                  )}
                </div>
              </div>
              <ChevronRight size={12} className="text-white/30 group-hover/item:text-white/60 group-hover/item:translate-x-0.5 transition-all" />
            </div>
          ))
        )}

         <button className="w-full mt-2 flex items-center justify-between px-4 py-2 text-[9px] font-black text-white/60 hover:text-white/90 transition-colors uppercase tracking-[0.3em] border border-white/10 hover:border-white/20 rounded-lg" aria-label="Download full topic schema">
           <span>Full Topic Schema</span>
           <Download size={10} />
        </button>
      </div>
    </StatCard>
  );
}

export default TopTopicsWidget;