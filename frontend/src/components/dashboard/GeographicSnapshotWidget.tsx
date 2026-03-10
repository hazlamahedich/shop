import { useQuery } from '@tanstack/react-query';
import { Globe, MapPin } from 'lucide-react';
import { analyticsService, GeographicBreakdown } from '../../services/analyticsService';

const FLAG_EMOJI: Record<string, string> = {
  US: '🇺🇸', CA: '🇨🇦', GB: '🇬🇧', AU: '🇦🇺', PH: '🇵🇭',
  SG: '🇸🇬', MY: '🇲🇾', IN: '🇮🇳', DE: '🇩🇪', FR: '🇫🇷',
  NZ: '🇳🇿', AE: '🇦🇪', JP: '🇯🇵', KR: '🇰🇷', ID: '🇮🇩',
};

function formatRevenue(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function CountryBar({
  row,
  maxRevenue,
  rank,
}: {
  row: GeographicBreakdown;
  maxRevenue: number;
  rank: number;
}) {
  const pct = maxRevenue > 0 ? (row.totalRevenue / maxRevenue) * 100 : 0;
  const flag = FLAG_EMOJI[row.country] ?? '🌍';
  const BAR_COLORS = ['bg-purple-500', 'bg-blue-500', 'bg-teal-500', 'bg-indigo-400'];
  const barColor = BAR_COLORS[rank] ?? 'bg-gray-400';

  return (
    <div className="group">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="text-sm" aria-hidden="true">{flag}</span>
          <span className="text-sm text-gray-700 font-medium">
            {row.countryName ?? row.country}
          </span>
          <span className="text-xs text-gray-400">
            {row.orderCount} {row.orderCount === 1 ? 'order' : 'orders'}
          </span>
        </div>
        <span className="text-sm font-semibold text-gray-800">
          {formatRevenue(row.totalRevenue)}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div
          className={`h-1.5 rounded-full ${barColor} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function GeographicSnapshotWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'geographic'],
    queryFn: () => analyticsService.getGeographic(),
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const topCountries: GeographicBreakdown[] = (data?.byCountry ?? [])
    .filter((c) => c.totalRevenue > 0 || c.orderCount > 0)
    .sort((a, b) => b.totalRevenue - a.totalRevenue)
    .slice(0, 5);

  const maxRevenue = topCountries[0]?.totalRevenue ?? 1;
  const totalRevenue = data?.totalRevenue ?? 0;

  return (
    <div
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm"
      data-testid="geographic-widget"
    >
      {/* Top accent strip */}
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-teal-400 to-green-400 opacity-60" />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-600 ring-4 ring-teal-100">
              <Globe size={16} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 leading-none">
                Top Markets
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {isLoading ? '…' : `${formatRevenue(totalRevenue)} total`}
              </p>
            </div>
          </div>
        </div>

        {/* Body */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i}>
                <div className="flex justify-between mb-1">
                  <div className="h-4 w-32 rounded bg-gray-200 animate-pulse" />
                  <div className="h-4 w-16 rounded bg-gray-200 animate-pulse" />
                </div>
                <div className="h-1.5 w-full rounded-full bg-gray-100 animate-pulse" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Could not load geographic data.
          </p>
        ) : topCountries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-50 mb-2">
              <MapPin size={18} className="text-gray-300" />
            </div>
            <p className="text-sm text-gray-400">No order location data yet.</p>
            <p className="text-xs text-gray-300 mt-0.5">
              Sales by country will appear once Shopify orders arrive.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {topCountries.map((row, i) => (
              <CountryBar key={row.country} row={row} maxRevenue={maxRevenue} rank={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default GeographicSnapshotWidget;
