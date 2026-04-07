import React from 'react';

interface BudgetReservoirGaugeProps {
  capacity: number;
  consumed: number;
  daysRemaining: number;
}

export const BudgetReservoirGauge: React.FC<BudgetReservoirGaugeProps> = ({
  capacity,
  consumed,
  daysRemaining
}) => {
  const percentage = (consumed / capacity) * 100;
  
  return (
    <div className="bg-white/[0.03] rounded-2xl p-6 relative overflow-hidden backdrop-blur-md group/gauge">
       {/* Ghost Border */}
       <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/gauge:border-[var(--mantis-glow)]/10 transition-colors" />
       
       {/* High-Contrast Design matching screenshot */}
       <div className="absolute inset-x-0 top-0 h-1 bg-[var(--mantis-glow)]/20 shadow-[0_0_10px_rgba(0,245,212,0.2)]" />
       
       <div className="flex justify-between items-start mb-6 relative z-10">
         <div className="space-y-1">
           <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">Budget Remaining</h4>
           <div className="flex items-baseline gap-2">
             <span className="text-3xl font-black text-white tracking-tighter">${capacity.toLocaleString()}</span>
           </div>
         </div>
       </div>

       <div className="space-y-4 relative z-10">
          <div className="relative w-full h-8 bg-black/40 rounded-lg overflow-hidden p-1 shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]">
            <div 
              className="h-full bg-[var(--mantis-glow)] rounded-md shadow-[0_0_15px_rgba(0,245,212,0.4)] transition-all duration-1000"
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
               <span className="text-[10px] font-black text-white uppercase tracking-widest mix-blend-difference">
                 {percentage.toFixed(1)}% Used
               </span>
            </div>
          </div>
          
          <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
             <span className="text-white/20">{daysRemaining} Days Remaining</span>
             <span className="text-[var(--mantis-glow)]">${(capacity - consumed).toLocaleString()} Available</span>
          </div>
       </div>
    </div>
  );
};
