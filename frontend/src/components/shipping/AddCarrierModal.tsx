/**
 * Add/Edit Carrier Modal Component
 *
 * Story 6.4: Frontend Settings Page
 *
 * Modal for creating or editing a custom carrier configuration.
 */

import React, { useState, useEffect } from 'react';
import { X, HelpCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import type { CarrierConfig, CreateCarrierRequest, UpdateCarrierRequest } from '../../services/shippingCarriers';

interface AddCarrierModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: CreateCarrierRequest | UpdateCarrierRequest) => Promise<void>;
  carrier?: CarrierConfig | null;
  isLoading?: boolean;
}

export const AddCarrierModal: React.FC<AddCarrierModalProps> = ({
  isOpen,
  onClose,
  onSave,
  carrier,
  isLoading = false,
}) => {
  const [carrierName, setCarrierName] = useState('');
  const [trackingUrlTemplate, setTrackingUrlTemplate] = useState('');
  const [trackingNumberPattern, setTrackingNumberPattern] = useState('');
  const [priority, setPriority] = useState('100');
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isEditing = !!carrier;

  useEffect(() => {
    if (carrier) {
      setCarrierName(carrier.carrier_name);
      setTrackingUrlTemplate(carrier.tracking_url_template);
      setTrackingNumberPattern(carrier.tracking_number_pattern || '');
      setPriority(String(carrier.priority));
      setIsActive(carrier.is_active);
    } else {
      setCarrierName('');
      setTrackingUrlTemplate('');
      setTrackingNumberPattern('');
      setPriority('100');
      setIsActive(true);
    }
    setError(null);
  }, [carrier, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!carrierName.trim()) {
      setError('Carrier name is required');
      return;
    }
    if (!trackingUrlTemplate.trim()) {
      setError('Tracking URL template is required');
      return;
    }
    if (!trackingUrlTemplate.includes('{tracking_number}')) {
      setError('Tracking URL template must include {tracking_number} placeholder');
      return;
    }

    const priorityNum = parseInt(priority, 10);
    if (isNaN(priorityNum) || priorityNum < 1 || priorityNum > 100) {
      setError('Priority must be between 1 and 100');
      return;
    }

    try {
      const data: CreateCarrierRequest | UpdateCarrierRequest = {
        carrier_name: carrierName.trim(),
        tracking_url_template: trackingUrlTemplate.trim(),
        tracking_number_pattern: trackingNumberPattern.trim() || null,
        is_active: isActive,
        priority: priorityNum,
      };
      await onSave(data);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save carrier');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
          <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {isEditing ? 'Edit Carrier' : 'Add Custom Carrier'}
              </h3>
              <button
                onClick={onClose}
                className="rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div>
                <Label htmlFor="carrier-name">Carrier Name *</Label>
                <Input
                  id="carrier-name"
                  value={carrierName}
                  onChange={(e) => setCarrierName(e.target.value)}
                  placeholder="e.g., LBC Express, J&T Express"
                  disabled={isLoading}
                />
              </div>

              <div>
                <Label htmlFor="tracking-url">Tracking URL Template *</Label>
                <Input
                  id="tracking-url"
                  value={trackingUrlTemplate}
                  onChange={(e) => setTrackingUrlTemplate(e.target.value)}
                  placeholder="https://track.lbcexpress.com/{tracking_number}"
                  disabled={isLoading}
                />
                 <p className="text-xs text-gray-500 mt-1">
                   Use <code className="bg-gray-100 px-1 rounded">{'{tracking_number}'}</code> as placeholder
                 </p>
                 <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700">
                   <p className="font-medium mb-1">📍 Tracking URL Format:</p>
                   <ul className="space-y-1 ml-3 list-disc">
                     <li>Replace the tracking number in the URL with <code className="bg-green-100 px-1">{'{tracking_number}'}</code></li>
                     <li>Example: <code className="bg-green-100 px-1">https://track.carrier.com/track/{'{tracking_number}'}</code></li>
                     <li>Find this URL by tracking a package on your carrier's website and copying the URL</li>
                   </ul>
                 </div>
               </div>

              <div>
                <Label htmlFor="tracking-pattern">
                  Tracking Number Pattern
                  <span className="ml-1 text-gray-400">(Optional)</span>
                </Label>
                <Input
                  id="tracking-pattern"
                  value={trackingNumberPattern}
                  onChange={(e) => setTrackingNumberPattern(e.target.value)}
                  placeholder="e.g., ^\d{12}$ for 12-digit numbers"
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                  <HelpCircle size={12} />
                  <span>Regex pattern for automatic carrier detection</span>
                </p>
                <div className="mt-2 p-2 bg-blue-50 rounded text-xs text-blue-700">
                  <p className="font-medium mb-1">💡 How to find your tracking number format:</p>
                  <ul className="space-y-1 ml-3 list-disc">
                    <li>Check a sample tracking number from your carrier</li>
                    <li>Common patterns: <code className="bg-blue-100 px-1">^\d{12}$</code> (12 digits), <code className="bg-blue-100 px-1">^[A-Z]{2}\d{9}[A-Z]{2}$</code> (2 letters, 9 digits, 2 letters)</li>
                    <li>Use <code className="bg-blue-100 px-1">\d</code> for digits, <code className="bg-blue-100 px-1">[A-Z]</code> for letters</li>
                    <li>Start with <code className="bg-blue-100 px-1">^</code> and end with <code className="bg-blue-100 px-1">$</code> to match the entire tracking number</li>
                  </ul>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                   <Label htmlFor="priority">Priority</Label>
                   <Input
                     id="priority"
                     type="number"
                     min="1"
                     max="100"
                     value={priority}
                     onChange={(e) => setPriority(e.target.value)}
                     disabled={isLoading}
                   />
                   <p className="text-xs text-gray-500 mt-1">Higher = checked first (1-100)</p>
                 </div>

                <div className="flex items-end">
                  <label className="flex items-center gap-2 cursor-pointer pb-2">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      disabled={isLoading}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Active</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Saving...' : isEditing ? 'Save Changes' : 'Add Carrier'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
