import { useQuery } from '@tanstack/react-query';
import { Clock, Users } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';

interface HourData {
  hour: number;
  dayOfWeek: number;
  count: number;
}

interface PeakHoursData {
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  hourlyBreakdown: HourData[];
  peakHours: number[];
  peakDay: number | null;
  peakHour: number | null;
  totalConversations: number;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function getIntensityColor(count: number, maxCount: number): string {
  if (count === 0) return 'bg-gray-50';
  const intensity = count / maxCount;
  if (intensity >= 0.8) return 'bg-red-500';
  if (intensity >= 0.6) return 'bg-orange-400';
  if (intensity >= 0.4) return 'bg-yellow-300';
  if (intensity >= 0.2) return 'bg-green-300';
  return 'bg-green-100';
}

function formatHour(hour: number): string {
  if (hour === 0) return '12am';
  if (hour === 12) return '12pm';
  if (hour < 12) return `${hour}am`;
  return `${hour - 12}pm`;
}

export function PeakHoursHeatmapWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'peak-hours'],
    queryFn: () => analyticsService.getPeakHours(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const peakHoursData = data as PeakHoursData | undefined;

  const hourlyBreakdown = peakHoursData?.hourlyBreakdown || [];
  const maxCount = Math.max(...hourlyBreakdown.map((h) => h.count), 1);

  const getCellCount = (dayOfWeek: number, hour: number): number => {
    const cell = hourlyBreakdown.find(
      (h) => h.dayOfWeek === dayOfWeek && h.hour === hour
    );
    return cell?.count || 0;
  };

  const formatPeakHour = (hour: number | null): string => {
    if (hour === null) return 'N/A';
    return formatHour(hour);
  };

  const formatPeakDay = (day: number | null): string => {
    if (day === null) return 'N/A';
    return DAYS[day] || 'N/A';
  };

  return (
    <div
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm"
      data-testid="peak-hours-heatmap-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-amber-400 to-orange-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Peak Hours
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              When customers need you most
            </p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-50 text-amber-600 ring-4 ring-amber-100">
            <Clock size={18} />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-gray-500">Unable to load peak hours data</p>
          </div>
        ) : hourlyBreakdown.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <Users size={32} className="text-gray-300 mb-2" />
            <p className="text-sm text-gray-500">No conversation data yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Peak hours will appear after conversations start
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <div className="min-w-[600px]">
                <div className="flex gap-0.5 mb-1">
                  <div className="w-10" />
                  {HOURS.slice(6, 22).map((hour) => (
                    <div
                      key={hour}
                      className="w-6 text-center text-[10px] text-gray-400"
                    >
                      {formatHour(hour)}
                    </div>
                  ))}
                </div>

                {DAYS.map((day, dayIndex) => (
                  <div key={day} className="flex gap-0.5 mb-0.5">
                    <div className="w-10 text-xs text-gray-500 flex items-center">
                      {day}
                    </div>
                    {HOURS.slice(6, 22).map((hour) => {
                      const count = getCellCount(dayIndex, hour);
                      return (
                        <div
                          key={hour}
                          className={`w-6 h-6 rounded-sm ${getIntensityColor(
                            count,
                            maxCount
                          )} flex items-center justify-center`}
                          title={`${DAYS[dayIndex]} ${formatHour(hour)}: ${count} conversations`}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Busiest Day</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {formatPeakDay(peakHoursData?.peakDay ?? null)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Peak Hour</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {formatPeakHour(peakHoursData?.peakHour ?? null)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-sm bg-green-100" />
                  <div className="w-3 h-3 rounded-sm bg-green-300" />
                  <div className="w-3 h-3 rounded-sm bg-yellow-300" />
                  <div className="w-3 h-3 rounded-sm bg-orange-400" />
                  <div className="w-3 h-3 rounded-sm bg-red-500" />
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default PeakHoursHeatmapWidget;
