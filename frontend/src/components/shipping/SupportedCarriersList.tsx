/**
 * Supported Carriers List Component
 *
 * Story 6.4: Frontend Settings Page
 *
 * Displays a collapsible list of supported carriers organized by region.
 */

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Search, Globe, Plus } from 'lucide-react';
import type { SupportedCarrier } from '../../services/shippingCarriers';

interface SupportedCarriersListProps {
  carriers: SupportedCarrier[];
  isLoading?: boolean;
  onCarrierClick?: (carrier: SupportedCarrier) => void;
}

export const SupportedCarriersList: React.FC<SupportedCarriersListProps> = ({
  carriers,
  isLoading = false,
  onCarrierClick,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredCarriers = useMemo(() => {
    if (!carriers || !Array.isArray(carriers)) return [];
    if (!searchQuery.trim()) return carriers;
    const query = searchQuery.toLowerCase();
    return carriers.filter(
      (c) =>
        c.name.toLowerCase().includes(query) ||
        c.region.toLowerCase().includes(query)
    );
  }, [carriers, searchQuery]);

  const carriersByRegion = useMemo(() => {
    const grouped: Record<string, SupportedCarrier[]> = {};
    for (const carrier of filteredCarriers) {
      if (!grouped[carrier.region]) {
        grouped[carrier.region] = [];
      }
      grouped[carrier.region].push(carrier);
    }
    return Object.entries(grouped).sort((a, b) => a[0].localeCompare(b[0]));
  }, [filteredCarriers]);

  if (isLoading) {
    return (
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <p className="text-gray-600 text-sm">Loading supported carriers...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Globe size={20} className="text-gray-500" />
          <div className="text-left">
            <h4 className="font-medium text-gray-900">Supported Carriers</h4>
            <p className="text-sm text-gray-600">
              {filteredCarriers.length} carriers across {carriersByRegion.length} regions
            </p>
          </div>
        </div>
        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200">
          <div className="p-4 bg-gray-50 border-b border-gray-200">
            <div className="relative">
              <Search
                size={16}
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500"
              />
              <input
                type="text"
                placeholder="Search carriers..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {carriersByRegion.length === 0 ? (
              <p className="p-4 text-sm text-gray-600 text-center">No carriers found</p>
            ) : (
              carriersByRegion.map(([region, regionCarriers]) => (
                <div key={region} className="border-b border-gray-100 last:border-b-0">
                  <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    {region} ({regionCarriers.length})
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-gray-100">
                    {regionCarriers.map((carrier, idx) => (
                      <div
                        key={`${carrier.name}-${idx}`}
                        className="group px-3 py-2 bg-white text-sm text-gray-700 hover:bg-blue-50 cursor-pointer flex items-center justify-between transition-colors"
                        title={carrier.tracking_url_template}
                        onClick={() => onCarrierClick?.(carrier)}
                      >
                        <span>{carrier.name}</span>
                        <Plus 
                          size={14} 
                          className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
