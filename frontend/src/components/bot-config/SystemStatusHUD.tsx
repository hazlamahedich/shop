import React from 'react';
import { Brain, ChevronRight } from 'lucide-react';
import { useBotConfigStore } from '../../stores/botConfigStore';

export const SystemStatusHUD: React.FC = () => {
    const { personality, latency, cognitiveLoad } = useBotConfigStore();

    const personalityName = personality ? personality.charAt(0).toUpperCase() + personality.slice(1) : 'Uninitialized';

    return (
        <section className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl h-full flex flex-col gap-8 relative overflow-hidden shadow-[0_0_32px_rgba(0,187,249,0.05)] transition-all duration-500 hover:border-[var(--mantis-glow)]/20">
            {/* Subtle background glow */}
            <div className="absolute top-[-20%] right-[-20%] w-64 h-64 rounded-full bg-[var(--mantis-glow)]/5 blur-[80px]"></div>
            
            <div className="relative z-10">
                <h3 className="font-headline text-xl text-[var(--mantis-glow)] font-bold tracking-tight">System Status Intelligence</h3>
                <p className="text-[10px] text-white/40 tracking-wider uppercase font-bold mt-1">Real-time heuristics</p>
            </div>

            <div className="flex flex-col gap-6 relative z-10">
                <div className="flex items-center justify-between p-5 bg-white/5 rounded-2xl border border-white/5 transition-colors hover:bg-white/10">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-[var(--mantis-glow)]/10 flex items-center justify-center relative">
                            <Brain size={24} className="text-[var(--mantis-glow)] animate-pulse" />
                            <div className="absolute inset-0 bg-[var(--mantis-glow)]/20 blur-lg rounded-full animate-pulse"></div>
                        </div>
                        <div>
                            <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest">Core Personality</p>
                            <p className="text-lg font-headline text-white font-medium">{personalityName}</p>
                        </div>
                    </div>
                    <a 
                        href="/personality"
                        className="flex items-center gap-1 text-[var(--mantis-glow)] text-xs font-bold hover:brightness-125 transition-all group"
                    >
                        Tune Personality
                        <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
                    </a>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 p-5 rounded-2xl border border-white/5">
                        <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest mb-1">Response Latency</p>
                        <p className="text-3xl font-headline text-[#82d3ff] font-bold">{latency}ms</p>
                    </div>
                    <div className="bg-white/5 p-5 rounded-2xl border border-white/5">
                        <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest mb-1">Cognitive Load</p>
                        <p className="text-3xl font-headline text-[#82d3ff] font-bold">{cognitiveLoad}%</p>
                    </div>
                </div>
            </div>
        </section>
    );
};
