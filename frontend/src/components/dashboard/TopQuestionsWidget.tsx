import { useQuery } from '@tanstack/react-query';
import { MessageSquare, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import type { TopQuestionsResponse } from '../../types/analytics';

export function TopQuestionsWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'top-questions'],
    queryFn: () => analyticsService.getTopQuestions(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const questionsData = data as TopQuestionsResponse | undefined;
  const questions = questionsData?.questions || [];

  return (
    <StatCard
      title="Top Customer Questions"
      value={isLoading ? '...' : `${questions.length}`}
      subValue="QUESTIONS_THIS_PERIOD"
      icon={<MessageSquare size={18} />}
      accentColor="purple"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-3 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Questions Unavailable</p>
          </div>
        ) : questions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-white/30 uppercase tracking-widest">No questions yet</p>
          </div>
        ) : (
          <>
            {/* Questions List */}
            <div className="space-y-2">
              {questions.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric hover:bg-white/10 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      {/* Question */}
                      <p className="text-[10px] font-semibold text-white/90 mb-2 line-clamp-2">
                        {item.question}
                      </p>

                      {/* Metrics */}
                      <div className="flex items-center gap-4 text-[9px]">
                        {/* Frequency */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-white/30 uppercase tracking-tighter">Asked</span>
                          <span className="font-black text-white">{item.frequency}x</span>
                        </div>

                        {/* Match Rate */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-white/30 uppercase tracking-tighter">Match</span>
                          <span
                            className={`font-black ${
                              item.matchRate >= 80
                                ? 'text-[#00f5d4]'
                                : item.matchRate >= 50
                                ? 'text-orange-400'
                                : 'text-rose-400'
                            }`}
                          >
                            {Math.round(item.matchRate)}%
                          </span>
                        </div>

                        {/* Confidence */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-white/30 uppercase tracking-tighter">Conf</span>
                          <span className="font-black text-white/60">
                            {Math.round(item.avgConfidence * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Trend Indicator */}
                    <div className="flex-shrink-0">
                      {item.trend === 'rising' ? (
                        <div className="flex items-center justify-center w-8 h-8 bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded-lg">
                          <TrendingUp size={14} className="text-[#00f5d4]" />
                        </div>
                      ) : item.trend === 'falling' ? (
                        <div className="flex items-center justify-center w-8 h-8 bg-rose-400/10 border border-rose-400/20 rounded-lg">
                          <TrendingDown size={14} className="text-rose-400" />
                        </div>
                      ) : (
                        <div className="flex items-center justify-center w-8 h-8 bg-white/5 border border-white/10 rounded-lg">
                          <Minus size={14} className="text-white/40" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Category Badge */}
                  <div className="mt-2">
                    <span className="inline-block px-2 py-0.5 bg-purple-400/10 border border-purple-400/20 rounded text-[8px] font-black text-purple-400 uppercase tracking-wider">
                      {item.category}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Period Summary */}
            {questionsData?.period && (
              <div className="pt-2 border-t border-white/5">
                <div className="flex items-center justify-between text-[9px]">
                  <span className="text-white/30 uppercase tracking-widest">Period</span>
                  <span className="font-black text-white">
                    {questionsData.period.days} days
                  </span>
                </div>
              </div>
            )}

            {/* Last Updated */}
            {questionsData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(questionsData.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default TopQuestionsWidget;
