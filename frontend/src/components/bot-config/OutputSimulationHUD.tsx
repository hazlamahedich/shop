import React from 'react';
import { useBotConfigStore } from '../../stores/botConfigStore';

export const OutputSimulationHUD: React.FC = () => {
    const { botName, personality } = useBotConfigStore();

    const getPreviewMessage = () => {
        const name = botName?.trim() || 'Neural Assistant';
        const business = 'the store';

        switch (personality) {
            case 'professional':
                return `Good day. I'm ${name}, here to assist you with inquiries about ${business}.`;
            case 'enthusiastic':
                return `Hey there!!! I'm ${name}, super excited to help you with ${business}!!!`;
            case 'friendly':
            default:
                return `Hi! I'm ${name}, here to help you with questions about ${business}.`;
        }
    };

    return (
        <section className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex flex-col gap-4 flex-1 shadow-[0_0_32px_rgba(0,187,249,0.05)] transition-all duration-500 hover:border-[var(--mantis-glow)]/20">
            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                <div className="w-2 h-2 rounded-full bg-[var(--mantis-glow)] animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></div>
                <h4 className="font-headline text-sm font-bold text-white tracking-wide uppercase italic">Output Simulation</h4>
            </div>
            
            <div className="bg-black/60 rounded-xl p-5 font-mono text-sm border border-white/5 flex flex-col gap-4 min-h-[160px] shadow-inner">
                <div className="flex items-start gap-3">
                    <span className="text-[var(--mantis-glow)] font-bold shrink-0">{botName || 'System'}:</span>
                    <span className="text-white/80 leading-relaxed italic">&quot;{getPreviewMessage()}&quot;</span>
                </div>
                <div className="flex items-start gap-3 opacity-30">
                    <span className="text-[#82d3ff] font-bold shrink-0">System:</span>
                    <span className="text-white/40 animate-pulse">Awaiting tactical input..._</span>
                </div>
            </div>
            
            <p className="text-[10px] text-white/30 leading-tight uppercase font-bold tracking-tighter mt-auto">
                * Identity module propagates to all customer-facing touchpoints
            </p>
        </section>
    );
};
