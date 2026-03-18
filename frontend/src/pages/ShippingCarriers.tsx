/**
 * Shipping Carriers Settings Page
 *
 * Story 6.4: Frontend Settings Page
 *
 * Re-imagined with Mantis aesthetic.
 */

import React, { useEffect, useState } from 'react';
import { Plus, Truck, AlertCircle, Sparkles, ShieldCheck, ChevronRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { CarrierCard } from '../components/shipping/CarrierCard';
import { AddCarrierModal } from '../components/shipping/AddCarrierModal';
import { SupportedCarriersList } from '../components/shipping/SupportedCarriersList';
import { useShippingCarriersStore } from '../stores/shippingCarriersStore';
import { useAuthStore } from '../stores/authStore';
import { GlassCard } from '../components/ui/GlassCard';
import type { CarrierConfig, CreateCarrierRequest, UpdateCarrierRequest, SupportedCarrier } from '../services/shippingCarriers';

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
  const [prefillCarrier, setPrefillCarrier] = useState<SupportedCarrier | null>(null);
  const [deletingCarrierId, setDeletingCarrierId] = useState<number | null>(null);

  useEffect(() => {
    if (merchant?.id) {
      fetchCarriers(merchant.id);
      fetchSupportedCarriers();
    }
  }, [merchant?.id, fetchCarriers, fetchSupportedCarriers]);

  const handleAddCarrier = () => {
    setEditingCarrier(null);
    setPrefillCarrier(null);
    setIsModalOpen(true);
  };

  const handleEditCarrier = (carrier: CarrierConfig) => {
    setEditingCarrier(carrier);
    setPrefillCarrier(null);
    setIsModalOpen(true);
  };

  const handleSupportedCarrierClick = (carrier: SupportedCarrier) => {
    setPrefillCarrier(carrier);
    setEditingCarrier(null);
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
    setPrefillCarrier(null);
    clearError();
  };

  const isLoading = carriersLoadingState === 'loading' || loadingState === 'loading';

  return (
    <div className="space-y-12 pb-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header section consistent with page themes */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <Truck size={12} />
            Logistics Protocol
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Shipping Carriers
          </h1>
          <p className="text-lg text-emerald-900/40 font-medium max-w-xl">
            Configure neural links for real-time order tracking and logistics synchronization.
          </p>
        </div>

        <button
          onClick={handleAddCarrier}
          disabled={carriersLoadingState === 'loading'}
          className="h-14 px-8 bg-emerald-500 text-black font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all duration-300 shadow-[0_0_30px_rgba(16,185,129,0.2)] flex items-center justify-center gap-3 active:scale-95"
        >
          <Plus size={18} />
          Register Carrier
        </button>
      </div>

      {/* Custom Carriers Section */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-black text-white uppercase tracking-[0.4em]">Active Protocols</span>
          <div className="h-px flex-1 bg-white/[0.05]" />
        </div>

        <GlassCard accent="mantis" className="border-emerald-500/10 bg-emerald-500/[0.01]">
          <div className="p-8 border-b border-white/[0.03] flex items-center justify-between bg-white/[0.01]">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <ShieldCheck size={24} />
              </div>
              <div>
                <h3 className="text-lg font-black text-white uppercase tracking-tight">Custom Carriers</h3>
                <p className="text-xs font-bold text-emerald-900/40 uppercase tracking-widest mt-1">
                  {(carriers?.length || 0)} node{(carriers?.length || 0) !== 1 ? 's' : ''} synchronized
                </p>
              </div>
            </div>
          </div>

          <div className="divide-y divide-white/[0.03]">
            {carriersLoadingState === 'loading' ? (
              <div className="p-20 text-center text-emerald-900/40 flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
                <span className="text-[10px] font-black uppercase tracking-[0.3em]">Accessing Distributed Ledger...</span>
              </div>
            ) : (carriers || []).length === 0 ? (
              <div className="p-20 text-center space-y-6">
                <div className="w-20 h-20 bg-white/[0.02] border border-white/[0.05] rounded-full flex items-center justify-center mx-auto text-emerald-900/20">
                  <Truck size={40} />
                </div>
                <div className="space-y-2">
                  <p className="text-white/60 font-bold">No custom carriers initialized.</p>
                  <p className="text-xs text-emerald-900/30 max-w-sm mx-auto uppercase tracking-widest font-black">
                    Link custom logistics providers to expand neural coverage.
                  </p>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-white/[0.03]">
                {carriers.map((carrier) => (
                  <CarrierCard
                    key={carrier.id}
                    carrier={carrier}
                    isDeleting={deletingCarrierId === carrier.id}
                    onEdit={() => handleEditCarrier(carrier)}
                    onDelete={() => handleDeleteCarrier(carrier.id)}
                    onToggle={(active) => handleToggleActive(carrier)}
                  />
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Supported Carriers Section */}
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-black text-white uppercase tracking-[0.4em]">Pre-Integrated Arrays</span>
          <div className="h-px flex-1 bg-white/[0.05]" />
        </div>

        {loadingState === 'loading' ? (
          <GlassCard className="p-12 text-center border-white/[0.03]">
            <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em] animate-pulse">Scanning Global Logistics Network...</p>
          </GlassCard>
        ) : (
          <SupportedCarriersList
            carriers={supportedCarriers || []}
            isLoading={loadingState === 'loading'}
            onCarrierClick={handleSupportedCarrierClick}
          />
        )}
      </div>

      {/* Add/Edit Carrier Modal */}
      <AddCarrierModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveCarrier}
        carrier={editingCarrier}
        prefillData={prefillCarrier}
        isLoading={carriersLoadingState === 'loading'}
      />
    </div>
  );
};

export default ShippingCarriers;
