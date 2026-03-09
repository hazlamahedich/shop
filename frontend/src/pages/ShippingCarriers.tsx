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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Shipping Carriers</h2>
          <p className="text-sm text-gray-500 mt-1">
            Manage custom carriers for tracking links. Built-in carriers are automatically detected.
          </p>
        </div>
        <Button onClick={handleAddCarrier} disabled={isLoading}>
          <Plus size={16} className="mr-2" />
          Add Custom Carrier
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
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

            {carriersLoadingState === 'loading' ? (
               <div className="py-8 text-center text-gray-500">
                 Loading carriers...
               </div>
            ) : (carriers || []).length === 0 ? (
              <div className="py-8 text-center text-gray-500">
                <Truck size={40} className="mx-auto mb-3 text-gray-300" />
                <p>No custom carriers configured yet.</p>
                <p className="text-sm mt-1">
                  Built-in carriers (USPS, UPS, FedEx, DHL, etc.) are automatically detected.
                </p>
                <Button variant="outline" className="mt-4" onClick={handleAddCarrier}>
                  Add your first custom carrier
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {carriers
                  .sort((a, b) => a.priority - b.priority)
                  .map((carrier) => (
                    <CarrierCard
                      key={carrier.id}
                      carrier={carrier}
                      onEdit={handleEditCarrier}
                      onDelete={handleDeleteCarrier}
                      onToggleActive={handleToggleActive}
                      isLoading={deletingCarrierId === carrier.id}
                    />
                  ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-1">
          <SupportedCarriersList
            carriers={supportedCarriers}
            isLoading={loadingState === 'loading'}
          />
        </div>
      </div>

      <AddCarrierModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveCarrier}
        carrier={editingCarrier}
        isLoading={isLoading}
      />
    </div>
  );
};

export default ShippingCarriers;
