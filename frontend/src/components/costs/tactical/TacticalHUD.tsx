import React from 'react';
// TacticalHUDHeader and TacticalHUDSidebar removed as they are redundant with the global Mantis layout.

interface TacticalHUDProps {
  children: React.ReactNode;
}

export const TacticalHUD: React.FC<TacticalHUDProps> = ({ children }) => {
  return (
    <div className="relative min-h-[calc(100vh-120px)] w-full bg-[#0d0d12]/40 text-white flex flex-col font-sans overflow-hidden rounded-3xl border border-white/5">
      {/* Global Scanline Overlay */}
      <div className="scanline-overlay pointer-events-none opacity-[0.05] absolute inset-0 z-50" />
      
      {/* Animated Background Orbs */}
      <div className="liquid-orb top-0 -left-20 w-[600px] h-[600px] bg-[var(--mantis-glow)]/10 blur-[100px] pointer-events-none" />
      <div className="liquid-orb bottom-0 -right-20 w-[600px] h-[600px] bg-purple-500/5 blur-[100px] pointer-events-none" />

      <div className="flex flex-1 relative z-10 p-2 sm:p-4 lg:p-10 custom-scrollbar overflow-y-auto">
        <div className="w-full relative">
          {/* Neural Grid Overlay */}
          <div className="absolute inset-0 opacity-[0.02] pointer-events-none" 
               style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.2) 1px, transparent 0)', backgroundSize: '40px 40px' }} />
          
          <div className="max-w-7xl mx-auto space-y-8 relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            {children}
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.02);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(0, 245, 212, 0.2);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 245, 212, 0.4);
        }
      `}</style>
    </div>
  );
};
