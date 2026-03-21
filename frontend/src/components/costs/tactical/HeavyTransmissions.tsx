import React from 'react';
import { formatCost } from '../../../types/cost';

interface Transmission {
  id: string;
  category: string;
  load: string;
  investment: number;
}

export const HeavyTransmissions: React.FC<{ transmissions: Transmission[] }> = ({ transmissions }) => {
  return (
    <div className="bg-white/[0.03] rounded-2xl p-8 backdrop-blur-md relative group/transmissions">
      {/* Ghost Border */}
      <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/transmissions:border-[var(--mantis-glow)]/10 transition-colors" />
      
      <div className="flex justify-between items-center mb-8 relative z-10">
        <h3 className="text-xl font-black text-white uppercase tracking-tight">Heavy Transmissions</h3>
        <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">Top 3 Expensive Clusters</span>
      </div>

      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-white/5 pb-4">
            <th className="text-[9px] font-black text-white/20 uppercase tracking-widest pb-4">Session Hash</th>
            <th className="text-[9px] font-black text-white/20 uppercase tracking-widest pb-4">Spectral Data</th>
            <th className="text-[9px] font-black text-white/20 uppercase tracking-widest pb-4">Token Load</th>
            <th className="text-[9px] font-black text-white/20 uppercase tracking-widest pb-4 text-right">Investment</th>
          </tr>
        </thead>
        <tbody>
          {transmissions.map((t) => (
            <tr key={t.id} className="group hover:bg-white/[0.02] transition-colors border-b border-white/[0.03]">
              <td className="py-5 font-mono text-[10px] text-[var(--mantis-glow)] tracking-widest">{t.id}</td>
              <td className="py-5 text-xs text-white/80 font-medium">{t.category}</td>
              <td className="py-5 text-[10px] text-white/40 font-black uppercase tracking-widest">{t.load}</td>
              <td className="py-5 text-right">
                <span className="text-sm font-black text-[var(--mantis-glow)] group-hover:mantis-glow-text transition-all tracking-tighter">
                  {formatCost(t.investment, 2)}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
