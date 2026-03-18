import React from 'react';
import { CheckCircle, ArrowRight, Play, Sparkles, Trophy, Rocket, MessageSquare } from 'lucide-react';
import { GlassCard } from '../components/ui/GlassCard';

const OnboardingSuccess = () => {
  return (
    <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-500/10 blur-[160px] rounded-full -z-10 animate-pulse" />
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent" />
      
      <div className="max-w-2xl w-full text-center space-y-12 relative z-10 animate-in fade-in zoom-in-95 duration-1000">
        <div className="space-y-6">
          <div className="relative inline-flex items-center justify-center">
            <div className="w-24 h-24 bg-emerald-500/10 rounded-[32px] border border-emerald-500/20 flex items-center justify-center text-emerald-400 relative z-10 shadow-[0_0_50px_rgba(16,185,129,0.2)]">
              <Trophy size={48} className="animate-bounce" />
            </div>
            {/* Ping Animations */}
            <div className="absolute inset-0 bg-emerald-500/20 rounded-[32px] animate-ping opacity-40" />
            <div className="absolute -inset-4 bg-emerald-500/10 rounded-[40px] animate-pulse blur-xl" />
          </div>

          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[9px] font-black uppercase tracking-[0.4em] text-emerald-400">
              <Sparkles size={12} />
              Synchronization Complete
            </div>
            <h1 className="text-7xl font-black text-white leading-none tracking-tight mantis-glow-text">
              Agent Awakened
            </h1>
            <p className="text-xl text-emerald-900/60 font-medium leading-relaxed max-w-lg mx-auto">
              Neural pathways are fully established. Your autonomous assistant is now active and monitoring the messenger uplink.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 max-w-md mx-auto">
          <button
            onClick={() => (window.location.pathname = '/dashboard')}
            className="group h-16 w-full bg-emerald-500 hover:bg-emerald-400 text-black font-black text-[11px] uppercase tracking-[0.4em] rounded-2xl transition-all duration-500 shadow-[0_0_40px_rgba(16,185,129,0.2)] hover:shadow-[0_0_60px_rgba(16,185,129,0.4)] hover:-translate-y-1 flex items-center justify-center gap-3"
          >
            Enter Dashboard
            <ArrowRight size={18} className="transition-transform group-hover:translate-x-2" />
          </button>

          <button
            className="group h-16 w-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-white font-black text-[11px] uppercase tracking-[0.4em] rounded-2xl transition-all duration-500 flex items-center justify-center gap-3"
          >
            <MessageSquare size={18} className="text-emerald-400 group-hover:scale-110 transition-transform" />
            Test Neural Uplink
          </button>
        </div>

        <div className="pt-8 flex items-center justify-center gap-12">
          <div className="flex flex-col items-center gap-2">
            <span className="text-[9px] font-black text-emerald-900/30 uppercase tracking-[0.2em]">Efficiency</span>
            <span className="text-white font-black tracking-widest text-lg">+94%</span>
          </div>
          <div className="w-px h-8 bg-white/[0.05]" />
          <div className="flex flex-col items-center gap-2">
            <span className="text-[9px] font-black text-emerald-900/30 uppercase tracking-[0.2em]">Latency</span>
            <span className="text-white font-black tracking-widest text-lg">14ms</span>
          </div>
          <div className="w-px h-8 bg-white/[0.05]" />
          <div className="flex flex-col items-center gap-2">
            <span className="text-[9px] font-black text-emerald-900/30 uppercase tracking-[0.2em]">Uptime</span>
            <span className="text-white font-black tracking-widest text-lg">∞</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingSuccess;
