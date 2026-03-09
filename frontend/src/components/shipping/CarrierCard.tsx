/**
 * Carrier Card Component
 *
 * Story 6.4: Frontend Settings Page
 *
 * Displays a single custom carrier configuration with edit/delete actions.
 */

import React from 'react';
import { Truck, Edit2, Trash2, Power, PowerOff } from 'lucide-react';
import type { CarrierConfig } from '../../services/shippingCarriers';

interface CarrierCardProps {
  carrier: CarrierConfig;
  onEdit: (carrier: CarrierConfig) => void;
  onDelete: (carrierId: number) => void;
  onToggleActive: (carrier: CarrierConfig) => void;
  isLoading?: boolean;
}

export const CarrierCard: React.FC<CarrierCardProps> = ({
  carrier,
  onEdit,
  onDelete,
  onToggleActive,
  isLoading = false,
}) => {
  return (
    <div
      className={`bg-white p-4 rounded-lg border ${
        carrier.is_active ? 'border-gray-200' : 'border-gray-100 bg-gray-50'
      } shadow-sm`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <div
            className={`p-2 rounded-lg ${
              carrier.is_active ? 'bg-blue-50 text-blue-600' : 'bg-gray-100 text-gray-400'
            }`}
          >
            <Truck size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-gray-900 truncate">{carrier.carrier_name}</h4>
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  carrier.is_active
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {carrier.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1 truncate">
              {carrier.tracking_url_template}
            </p>
            {carrier.tracking_number_pattern && (
              <p className="text-xs text-gray-400 mt-1 font-mono truncate">
                Pattern: {carrier.tracking_number_pattern}
              </p>
            )}
            <p className="text-xs text-gray-400 mt-1">Priority: {carrier.priority}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggleActive(carrier)}
            disabled={isLoading}
            className={`p-2 rounded-lg transition-colors ${
              carrier.is_active
                ? 'text-green-600 hover:bg-green-50'
                : 'text-gray-400 hover:bg-gray-100'
            } disabled:opacity-50`}
            title={carrier.is_active ? 'Deactivate' : 'Activate'}
          >
            {carrier.is_active ? <Power size={16} /> : <PowerOff size={16} />}
          </button>
          <button
            onClick={() => onEdit(carrier)}
            disabled={isLoading}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            title="Edit"
          >
            <Edit2 size={16} />
          </button>
          <button
            onClick={() => onDelete(carrier.id)}
            disabled={isLoading}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            title="Delete"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
