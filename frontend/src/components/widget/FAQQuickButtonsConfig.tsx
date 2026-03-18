/**
 * FAQ Quick Buttons Configuration Component
 *
 * Story 10-2 AC5: Merchant Configuration UI
 *
 * Allows merchants to select which FAQs appear as quick buttons in the widget.
 * - Only shown for merchants in General Mode
 * - Max 5 FAQs can be selected
 * - Shows FAQ question and allows setting custom icons
 */

import React, { useEffect, useState } from 'react';
import { HelpCircle, GripVertical, Check, Loader2, MessageSquare } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { apiClient } from '../../services/api';
import { useToast } from '../../context/ToastContext';

interface FAQ {
  id: number;
  question: string;
  icon: string | null;
  order_index: number;
}

interface FAQQuickButtonsConfigProps {
  merchantId: number;
  initialConfig?: {
    enabled: boolean;
    faqIds: number[];
  };
  onConfigChange?: (config: { enabled: boolean; faqIds: number[] }) => void;
}

export function FAQQuickButtonsConfig({
  merchantId,
  initialConfig,
  onConfigChange,
}: FAQQuickButtonsConfigProps) {
  const { toast } = useToast();
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>(initialConfig?.faqIds || []);
  const [enabled, setEnabled] = useState(initialConfig?.enabled ?? true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchFAQs();
  }, [merchantId]);

  useEffect(() => {
    if (initialConfig) {
      setSelectedIds(initialConfig.faqIds);
      setEnabled(initialConfig.enabled);
    }
  }, [initialConfig]);

  const fetchFAQs = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ data: FAQ[] }>(`/api/v1/merchants/faqs`);
      setFaqs(response.data || []);
    } catch (error) {
      console.error('Failed to fetch FAQs:', error);
      toast('Failed to load FAQs', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFAQ = (faqId: number) => {
    let newSelectedIds: number[];
    if (selectedIds.includes(faqId)) {
      newSelectedIds = selectedIds.filter((id) => id !== faqId);
    } else {
      if (selectedIds.length >= 5) {
        toast('Maximum 5 FAQs allowed', 'error');
        return;
      }
      newSelectedIds = [...selectedIds, faqId];
    }
    setSelectedIds(newSelectedIds);
    onConfigChange?.({ enabled, faqIds: newSelectedIds });
  };

  const handleToggleEnabled = () => {
    const newEnabled = !enabled;
    setEnabled(newEnabled);
    onConfigChange?.({ enabled: newEnabled, faqIds: selectedIds });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await apiClient.patch(`/api/v1/merchants/widget-config`, {
        faq_quick_buttons: {
          enabled,
          faq_ids: selectedIds,
        },
      });
      toast('FAQ quick buttons configuration saved', 'success');
    } catch (error) {
      console.error('Failed to save config:', error);
      toast('Failed to save configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <GlassCard className="p-8">
        <div className="flex items-center justify-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
          <span className="text-[10px] font-black text-emerald-900/40 uppercase tracking-widest">
            Loading FAQs...
          </span>
        </div>
      </GlassCard>
    );
  }

  if (faqs.length === 0) {
    return (
      <GlassCard className="p-8">
        <div className="text-center space-y-4">
          <div className="p-3 bg-white/5 rounded-xl inline-block">
            <MessageSquare className="w-8 h-8 text-white/40" />
          </div>
          <div>
            <p className="text-white font-black text-sm uppercase tracking-tight">No FAQs Found</p>
            <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-widest mt-1">
              Create FAQs first to enable quick buttons
            </p>
          </div>
          <a
            href="/business-info/faq"
            className="inline-block h-10 px-6 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-black text-[9px] uppercase tracking-widest rounded-xl hover:bg-emerald-500 hover:text-black transition-all"
          >
            Create FAQs
          </a>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard accent="mantis" className="border-emerald-500/10 bg-emerald-500/[0.01]">
      <div className="p-8 border-b border-white/[0.03] flex items-center justify-between bg-white/[0.01]">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/20">
            <HelpCircle size={20} />
          </div>
          <div>
            <h2 className="text-lg font-black text-white uppercase tracking-tight">
              FAQ Quick Buttons
            </h2>
            <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-widest">
              Select FAQs to show as quick buttons (max 5)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleToggleEnabled}
            className={`
              relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-4 border-transparent transition-all duration-500 
              ${enabled ? 'bg-emerald-500' : 'bg-white/10'}
            `}
            title={enabled ? 'Disable FAQ buttons' : 'Enable FAQ buttons'}
          >
            <span
              className={`
              pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-xl transition-all duration-500
              ${enabled ? 'translate-x-6' : 'translate-x-0'}
            `}
            />
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="h-10 px-6 bg-emerald-500 text-black font-black text-[9px] uppercase tracking-widest rounded-xl hover:bg-emerald-400 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      <div className="p-8 space-y-4">
        <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl">
          <p className="text-[10px] text-amber-400 font-bold uppercase tracking-widest">
            ⚡ Selected: {selectedIds.length}/5 FAQs
          </p>
        </div>

        <div className="space-y-2">
          {faqs.map((faq) => {
            const isSelected = selectedIds.includes(faq.id);
            return (
              <button
                key={faq.id}
                type="button"
                onClick={() => handleToggleFAQ(faq.id)}
                className={`
                  w-full p-4 rounded-2xl border transition-all duration-300 text-left flex items-center gap-4
                  ${
                    isSelected
                      ? 'bg-emerald-500/10 border-emerald-500/30'
                      : 'bg-white/[0.02] border-white/[0.05] hover:border-white/[0.1] hover:bg-white/[0.03]'
                  }
                `}
              >
                <div
                  className={`
                  w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all
                  ${isSelected ? 'bg-emerald-500 border-emerald-500' : 'border-white/20'}
                `}
                >
                  {isSelected && <Check className="w-4 h-4 text-black" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-bold text-sm truncate">{faq.question}</p>
                  {faq.icon && (
                    <p className="text-[10px] text-emerald-400 font-bold mt-1">Icon: {faq.icon}</p>
                  )}
                </div>
                <GripVertical className="w-4 h-4 text-white/20" />
              </button>
            );
          })}
        </div>

        {selectedIds.length > 0 && (
          <div className="pt-4 border-t border-white/[0.05]">
            <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-widest mb-3">
              Preview Order
            </p>
            <div className="flex flex-wrap gap-2">
              {selectedIds.map((id, index) => {
                const faq = faqs.find((f) => f.id === id);
                if (!faq) return null;
                return (
                  <div
                    key={id}
                    className="h-10 px-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-2"
                  >
                    <span className="text-[9px] font-black text-emerald-400">{index + 1}</span>
                    <span className="text-white font-bold text-xs truncate max-w-[150px]">
                      {faq.icon ? `${faq.icon} ` : ''}
                      {faq.question}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}
