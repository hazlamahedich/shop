/**
 * Shipping Carriers Settings Page
 *
 * Story 6.4: Frontend Settings Page
 *
 * Page for managing custom shipping carrier configurations.
 * Allows merchants to add, edit, delete, and toggle carrier configurations.
 */

import React, { useEffect, useState } from 'react';
import { Plus, Truck, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { CarrierCard } from '../components/shipping/CarrierCard';
import { AddCarrierModal } from '../components/shipping/AddCarrierModal';
import { SupportedCarriersList } from '../components/shipping/SupportedCarriersList';
import { useShippingCarriersStore } from '../stores/shippingCarriersStore';
import { useAuthStore } from '../stores/authStore';
import type { CarrierConfig, CreateCarrierRequest, UpdateCarrierRequest } from '../services/shippingCarriers';

const ShippingCarriers: React.FC = () => {
  const merchant = useAuthStore((state) => state.merchant);
  const {
    carriers,
    supportedCarriers,
    loadingState,
    carriersLoadingState,
    error,
    fetchCarriers,
    fetchSupportedCarriers,
    createCarrier,
    updateCarrier,
    deleteCarrier,
    clearError,
  } = useShippingCarriersStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCarrier, setEditingCarrier] = useState<CarrierConfig | null>(null);
  const [deletingCarrierId, setDeletingCarrierId] = useState<number | null>(null);

  useEffect(() => {
    if (merchant?.id) {
      fetchCarriers(merchant.id);
      fetchSupportedCarriers();
    }
  }, [merchant?.id, fetchCarriers, fetchSupportedCarriers]);

  const handleAddCarrier = () => {
    setEditingCarrier(null);
    setIsModalOpen(true);
  };

  const handleEditCarrier = (carrier: CarrierConfig) => {
    setEditingCarrier(carrier);
    setIsModalOpen(true);
  };

  const handleDeleteCarrier = async (carrierId: number) => {
    if (!merchant?.id) return;
    if (!window.confirm('Are you sure you want to delete this carrier?')) return;

    setDeletingCarrierId(carrierId);
    try {
      await deleteCarrier(merchant.id, carrierId);
    } catch (err) {
      console.error('Failed to delete carrier:', err);
    } finally {
      setDeletingCarrierId(null);
    }
  };

  const handleToggleActive = async (carrier: CarrierConfig) => {
    if (!merchant?.id) return;

    try {
      await updateCarrier(merchant.id, carrier.id, {
        is_active: !carrier.is_active,
      });
    } catch (err) {
      console.error('Failed to toggle carrier:', err);
    }
  };

  const handleSaveCarrier = async (data: CreateCarrierRequest | UpdateCarrierRequest) => {
    if (!merchant?.id) return;

    if (editingCarrier) {
      await updateCarrier(merchant.id, editingCarrier.id, data as UpdateCarrierRequest);
    } else {
      await createCarrier(merchant.id, data as CreateCarrierRequest);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingCarrier(null);
    clearError();
  };

  const isLoading = carriersLoadingState === 'loading' || loadingState === 'loading';

  return (
    <div className="space-y-6">
      {/* Custom Carriers Section */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <Truck size={20} />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Custom Carriers</h3>
              <p className="text-sm text-gray-500">
                {(carriers?.length || 0)} custom carrier{(carriers?.length || 0) !== 1 ? 's' : ''} configured
              </p>
            </div>
          </div>

          <Button
            onClick={handleAddCarrier}
            disabled={carriersLoadingState === 'loading'}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            Add Carrier
          </Button>
        </div>

        {carriersLoadingState === 'loading' ? (
          <div className="py-8 text-center text-gray-500">
            Loading carriers...
          </div>
        ) : (carriers || []).length === 0 ? (
          <div className="py-8 text-center text-gray-500">
            <Truck size={40} className="mx-auto mb-3 text-gray-300" />
            <p>No custom carriers configured yet.</p>
            <p className="text-sm mt-1">
              Add custom carriers for local shipping providers that aren't in the supported list.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {carriers.map((carrier) => (
              <CarrierCard
                key={carrier.id}
                carrier={carrier}
                isDeleting={deletingCarrierId === carrier.id}
                onEdit={() => handleEditCarrier(carrier)}
                onDelete={() => handleDeleteCarrier(carrier.id)}
                onToggle={(active) => handleToggleCarrier(carrier, active)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Supported Carriers Section */}
      <div>
        {loadingState === 'loading' ? (
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-gray-500 text-sm">Loading supported carriers...</p>
          </div>
        ) : (
          <SupportedCarriersList
            carriers={supportedCarriers || []}
            isLoading={loadingState === 'loading'}
          />
        )}
      </div>
    </div>
  );
};

export default ShippingCarriers;
