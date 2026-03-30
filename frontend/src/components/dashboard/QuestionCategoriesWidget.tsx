import { useQuery } from '@tanstack/react-query';
import { Folder, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface QuestionCategory {
  category: string;
  volume: number;
  matchRate: number;
  avgConfidence: number;
  trend: 'rising' | 'falling' | 'stable';
  topQuestions?: string[];
}

export function QuestionCategoriesWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'question-categories'],
    queryFn: () => analyticsService.getQuestionCategories(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const categories = data as QuestionCategory[] | undefined;

  // Show error state if API fails after retries
  if (isError) {
    return (
      <StatCard
        title="Question Categories"
        value="0"
        subValue="CATEGORIES_WITH_DATA"
        icon={<Folder size={18} />}
        accentColor="purple"
        isLoading={false}
      >
        <div className="flex items-center justify-center py-8">
          <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Unable to load categories</p>
          <p className="text-[8px] text-white/30 mt-2">Please refresh the page</p>
        </div>
      </StatCard>
    );
  }

  return (
    <StatCard
      title="Question Categories"
      value={isLoading ? '...' : `${categories?.length || 0}`}
      subValue="CATEGORIES_WITH_DATA"
      icon={<Folder size={18} />}
      accentColor="purple"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-3 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Unable to load categories</p>
          </div>
        ) : !categories || categories.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-white/30 uppercase tracking-widest">No category data yet</p>
            <p className="text-[8px] text-white/20 mt-2">Start asking questions to see categories</p>
          </div>
        ) : (
          <>
            {/* Categories List */}
            <div className="space-y-2">
              {categories.map((category, idx) => (
                <div
                  key={idx}
                  className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-all"
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex-1">
                      {/* Category Name */}
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-[10px] font-semibold text-white/90">
                          {category.category}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${
                            category.matchRate >= 80
                              ? 'bg-[#00f5d4]/10 text-[#00f5d4]'
                              : category.matchRate >= 60
                              ? 'bg-orange-400/10 text-orange-400'
                              : 'bg-rose-400/10 text-rose-400'
                          }`}
                        >
                          {Math.round(category.matchRate)}% match
                        </span>
                      </div>

                      {/* Metrics Grid */}
                      <div className="grid grid-cols-3 gap-2 text-[9px]">
                        <div>
                          <p className="text-white/30 uppercase tracking-tighter">Volume</p>
                          <p className="font-black text-white">{category.volume}</p>
                        </div>
                        <div>
                          <p className="text-white/30 uppercase tracking-tighter">Conf</p>
                          <p className="font-black text-white">{Math.round(category.avgConfidence * 100)}%</p>
                        </div>
                        <div>
                          <p className="text-white/30 uppercase tracking-tighter">Trend</p>
                          <div className="flex items-center gap-1">
                            {category.trend === 'rising' ? (
                              <TrendingUp size={10} className="text-[#00f5d4]" />
                            ) : category.trend === 'falling' ? (
                              <TrendingDown size={10} className="text-rose-400" />
                            ) : (
                              <Minus size={10} className="text-white/40" />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Match Rate Bar */}
                    <div className="flex-shrink-0 w-16">
                      <div className="h-16 w-full bg-white/5 rounded-lg overflow-hidden relative">
                        <div
                          className={`absolute bottom-0 left-0 right-0 transition-all duration-500 ${
                            category.matchRate >= 80
                              ? 'bg-gradient-to-t from-[#00f5d4]/40 to-[#00f5d4]'
                              : category.matchRate >= 60
                              ? 'bg-gradient-to-t from-orange-400/40 to-orange-400'
                              : 'bg-gradient-to-t from-rose-400/40 to-rose-400'
                          }`}
                          style={{ height: `${category.matchRate}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Top Questions */}
                  {category.topQuestions && category.topQuestions.length > 0 && (
                    <div className="pt-2 border-t border-white/5">
                      <p className="text-[8px] text-white/30 uppercase tracking-wider mb-1">
                        Top Questions
                      </p>
                      <div className="space-y-1">
                        {category.topQuestions.slice(0, 2).map((question, qIdx) => (
                          <p
                            key={qIdx}
                            className="text-[8px] text-white/50 truncate"
                            title={question}
                          >
                            "{question}"
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Category Summary */}
            <div className="pt-2 border-t border-white/5">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-[8px] text-white/30 uppercase tracking-wider">High Perf</p>
                  <p className="text-lg font-black text-[#00f5d4]">
                    {categories.filter((c) => c.matchRate >= 80).length}
                  </p>
                </div>
                <div>
                  <p className="text-[8px] text-white/30 uppercase tracking-wider">Needs Work</p>
                  <p className="text-lg font-black text-orange-400">
                    {categories.filter((c) => c.matchRate >= 60 && c.matchRate < 80).length}
                  </p>
                </div>
                <div>
                  <p className="text-[8px] text-white/30 uppercase tracking-wider">Critical</p>
                  <p className="text-lg font-black text-rose-400">
                    {categories.filter((c) => c.matchRate < 60).length}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default QuestionCategoriesWidget;
