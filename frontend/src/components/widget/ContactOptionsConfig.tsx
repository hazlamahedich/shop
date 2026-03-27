/**
 * Contact Options Configuration Component
 *
 * Story 10-5: Merchant Configuration UI
 *
 * Allows merchants to configure contact methods (phone, email, custom links)
 * for the widget's contact card.
 */

import React from 'react';
import { Mail, Phone, ExternalLink, Plus, Trash2, MessageCircle } from 'lucide-react';
import { GlassCard } from '../ui/GlassCard';
import { useWidgetSettingsStore } from '../../stores/widgetSettingsStore';
import type { ContactOption } from '../../widget/types/widget';

export function ContactOptionsConfig() {
  const { config, setConfig } = useWidgetSettingsStore();
  
  if (!config) return null;
  
  const options = config.contactOptions || [];

  const handleAddOption = () => {
    const newOption: ContactOption = {
      type: 'email',
      label: 'Email Support',
      value: '',
      icon: 'mail'
    };
    setConfig({
      contactOptions: [...options, newOption]
    });
  };

  const handleRemoveOption = (index: number) => {
    const newOptions = options.filter((_, i) => i !== index);
    setConfig({
      contactOptions: newOptions
    });
  };

  const handleUpdateOption = (index: number, updates: any) => {
    const newOptions = [...options];
    newOptions[index] = { ...newOptions[index], ...updates };
    
    // Auto-update icon based on type if not explicitly set
    if (updates.type) {
      if (updates.type === 'email') newOptions[index].icon = 'mail';
      else if (updates.type === 'phone') newOptions[index].icon = 'phone';
      else if (updates.type === 'custom') newOptions[index].icon = 'link';
    }
    
    setConfig({
      contactOptions: newOptions
    });
  };

  return (
    <GlassCard accent="mantis" className="border-emerald-500/10 bg-emerald-500/[0.01]">
      <div className="p-4 border-b border-white/[0.03] flex items-center justify-between bg-white/[0.01]">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/20">
            <MessageCircle size={18} />
          </div>
          <div>
            <h2 className="text-sm font-black text-white uppercase tracking-tight">
              Contact Parameters
            </h2>
            <p className="text-[9px] text-emerald-900/40 font-bold uppercase tracking-widest">
              Configure escalation channels
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleAddOption}
          className="h-8 px-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-black text-[9px] uppercase tracking-widest rounded-xl hover:bg-emerald-500 hover:text-black transition-all flex items-center gap-2"
        >
          <Plus size={12} />
          Add Channel
        </button>
      </div>

      <div className="p-4 space-y-4">
        {options.length === 0 ? (
          <div className="text-center py-6 bg-white/[0.01] border border-dashed border-white/10 rounded-xl">
            <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-[0.2em]">
              No escalation channels active
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {options.map((option, index) => (
              <div 
                key={index}
                className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-2xl space-y-3 animate-in fade-in slide-in-from-top-2 duration-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/5 rounded-xl text-white/40">
                      {option.type === 'email' && <Mail size={16} />}
                      {option.type === 'phone' && <Phone size={16} />}
                      {option.type === 'custom' && <ExternalLink size={16} />}
                    </div>
                    <span className="text-[10px] font-black text-white uppercase tracking-widest">
                      Channel #{index + 1}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveOption(index)}
                    className="p-2 text-red-500/40 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest ml-1">Type</label>
                    <select
                      value={option.type}
                      onChange={(e) => handleUpdateOption(index, { type: e.target.value })}
                      className="w-full h-10 bg-white/5 border border-white/10 rounded-lg px-3 text-white font-black text-[10px] uppercase tracking-widest appearance-none transition-all focus:border-emerald-500/40 focus:bg-emerald-500/[0.03]"
                    >
                      <option value="email">Email</option>
                      <option value="phone">Phone</option>
                      <option value="custom">Custom Link</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest ml-1">Label</label>
                    <input
                      type="text"
                      value={option.label}
                      onChange={(e) => handleUpdateOption(index, { label: e.target.value })}
                      placeholder="e.g. Email Support"
                      className="w-full h-10 bg-white/5 border border-white/10 rounded-lg px-3 text-white font-black text-[10px] uppercase tracking-widest transition-all focus:border-emerald-500/40 focus:bg-emerald-500/[0.03]"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest ml-1">Value</label>
                    <input
                      type="text"
                      value={option.value}
                      onChange={(e) => handleUpdateOption(index, { value: e.target.value })}
                      placeholder={option.type === 'email' ? 'support@store.com' : option.type === 'phone' ? '+1...' : 'https://...'}
                      className="w-full h-10 bg-white/5 border border-white/10 rounded-lg px-3 text-white font-black text-[10px] uppercase tracking-widest transition-all focus:border-emerald-500/40 focus:bg-emerald-500/[0.03]"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  );
}
