import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ChevronRight, BookOpen, Download, ArrowUp, ArrowDown, Minus, Sparkles } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import type { TopTopicsResponse, TopTopic } from '../../services/analyticsService';

interface TopTopicsWidgetProps {
  days?: number;
}

const formatRelativeTime = (date: Date): string => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 1) return `${diffDays}d ago`
    return `${diffDays}d ago`
};

const getTrendIcon = (trend: string) => {
    switch (trend) {
        case 'up':
            return <ArrowUp size={14} className="text-green-400" />;
        case 'down':
            return <ArrowDown size={14} className="text-red-400" />;
        case 'new':
            return <Sparkles size={14} className="text-blue-400" />;
        default:
            return <Minus size={14} className="text-gray-400" />;
    }
};

const getTrendColor = (trend: string) => {
    switch (trend) {
        case 'up':
            return 'text-green-400';
        case 'down':
            return 'text-red-400';
        case 'new':
            return 'text-blue-400';
        default:
            return 'text-gray-400';
    }
};

export function TopTopicsWidget({ days: initialDays = 7 }: TopTopicsWidgetProps) {
    const navigate = useNavigate()
    const [days, setDays] = useState(initialDays)

    const { data, isLoading, isError } = useQuery({
        queryKey: ['analytics', 'top-topics', days],
        queryFn: () => analyticsService.getTopTopics(days),
        staleTime: 60_000,
        refetchInterval: 60_000,
    })

    const topicsData = data as TopTopicsResponse | undefined
    const topics = topicsData?.topics ?? []
    const lastUpdated = topicsData?.lastUpdated ?? new Date().toISOString()
    const period = topicsData?.period

    const handleTopicClick = (topic: string) => {
        navigate(`/conversations?search=${encodeURIComponent(topic)}`)
    }

    const handleExportCSV = () => {
        if (!topicsData || topics.length === 0) return

        const csvContent =
            'Topic Name,Query Count,Trend\n' +
            topics.map((t) => `${t.name},${t.queryCount},${t.trend}`).join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
        const filename = `top-topics-${new Date().toISOString().split('T')[0]}.csv`
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(link.href)
    }

    const handleTimeRangeChange = (newDays: number) => {
        setDays(newDays)
    }

    return (
        <div
            className="relative overflow-hidden rounded-2xl glass-card border-none shadow-lg"
            data-testid="top-topics-widget"
        >
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-500 opacity-80" />

            <div className="p-5">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <p className="text-sm font-medium text-white/60 uppercase tracking-wide">
                            Top Topics
                        </p>
                        <p className="text-xs text-white/40 mt-0.5">
                            Most Asked Questions
                        </p>
                    </div>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 ring-4 ring-emerald-500/20">
                        <TrendingUp size={18} />
                    </div>
                </div>

                {isLoading ? (
                    <div data-testid="top-topics-skeleton" className="space-y-4">
                        <div className="h-8 bg-white/5 rounded animate-pulse" />
                        <div className="h-8 bg-white/5 rounded animate-pulse" />
                        <div className="h-8 bg-white/5 rounded animate-pulse" />
                    </div>
                ) : isError ? (
                    <div data-testid="top-topics-error" className="flex items-center justify-center py-8">
                        <p className="text-sm text-white/60">Unable to load topics data</p>
                    </div>
                ) : !topicsData || topics.length === 0 ? (
                    <div data-testid="top-topics-empty" className="flex flex-col items-center justify-center py-8">
                        <BookOpen size={32} className="text-white/30 mb-2" />
                        <p className="text-sm text-white/60">No topics yet</p>
                        <p className="text-xs text-white/40 mt-1">Topics will appear as shoppers ask questions</p>
                        <button
                            onClick={() => navigate('/knowledge')}
                            className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors mt-2"
                        >
                            Add knowledge
                        </button>
                    </div>
                ) : (
                    <>
                        <div className="flex items-center gap-2 mb-4" data-testid="time-range-selector">
                            <select
                                value={days}
                                onChange={(e) => handleTimeRangeChange(Number(e.target.value))}
                                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white/80 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            >
                                <option value={7}>7 days</option>
                                <option value={30}>30 days</option>
                                <option value={90}>90 days</option>
                            </select>
                            <button
                                data-testid="export-csv-button"
                                onClick={handleExportCSV}
                                className="flex items-center gap-2 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                            >
                                <Download size={12} />
                                Export CSV
                            </button>
                        </div>

                        <div className="space-y-2">
                            {topics.map((topic, index) => (
                                <div
                                    key={index}
                                    data-testid="topic-item"
                                    onClick={() => handleTopicClick(topic.name)}
                                    className="flex items-center justify-between p-3 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10 transition-colors"
                                    role="button"
                                    tabIndex={0}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                            handleTopicClick(topic.name)
                                        }
                                    }}
                                    aria-label={`Topic: ${topic.name}, ${topic.queryCount} queries, trend: ${topic.trend}`}
                                >
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate">{topic.name}</p>
                                        <p className="text-xs text-white/40">{topic.queryCount} queries</p>
                                    </div>
                                    <div className={`flex items-center gap-1 ${getTrendColor(topic.trend)}`}>
                                        {getTrendIcon(topic.trend)}
                                        <span className="text-xs capitalize">{topic.trend}</span>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-4 pt-4 border-t border-white/10">
                            <p className="text-xs text-white/50">Last updated</p>
                            <p className="text-xs text-white/40">
                                {formatRelativeTime(new Date(lastUpdated))}
                            </p>
                        </div>

                        <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                            <button
                                data-testid="export-csv-button"
                                onClick={handleExportCSV}
                                className="flex items-center gap-2 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                            >
                                <Download size={12} />
                                Export CSV
                            </button>
                            <button
                                data-testid="view-details-button"
                                onClick={() => navigate('/analytics')}
                                className="flex items-center gap-2 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                            >
                                <ChevronRight size={12} />
                                View details
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}