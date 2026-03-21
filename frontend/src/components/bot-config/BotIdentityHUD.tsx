import React from 'react';
import { Save, Verified } from 'lucide-react';
import { useBotConfigStore } from '../../stores/botConfigStore';
import { useToast } from '../../context/ToastContext';
import { useOnboardingPhaseStore } from '../../stores/onboardingPhaseStore';

export const BotIdentityHUD: React.FC = () => {
    const { botName, setBotName, updateBotName, loadingState, isDirty } = useBotConfigStore();
    const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);
    const { toast } = useToast();

    const isLoading = loadingState === 'loading';

    const handleSave = async () => {
        try {
            await updateBotName({ bot_name: botName || '' });
            markBotConfigComplete('botName');
            toast('Bot identity profile updated.', 'success');
        } catch (err) {
            toast('Failed to update identity.', 'error');
        }
    };

    return (
        <section className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex flex-col gap-6 shadow-[0_0_32px_rgba(0,187,249,0.05)] transition-all duration-500 hover:border-[var(--mantis-glow)]/20">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="font-headline text-xl text-[var(--mantis-glow)] font-bold tracking-tight">Identity Module</h3>
                    <p className="text-[10px] text-white/40 tracking-wider uppercase font-bold mt-1">Core Designation Layer</p>
                </div>
                <div className="flex items-center gap-2 bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 px-3 py-1.5 rounded-full">
                    <Verified size={14} className="text-[var(--mantis-glow)]" fill="currentColor" fillOpacity={0.2} />
                    <span className="text-[10px] font-bold text-[var(--mantis-glow)] uppercase tracking-tighter">Verified Agent</span>
                </div>
            </div>
            
            <div className="flex flex-col gap-4">
                <div className="relative group">
                    <label className="text-[10px] text-[var(--mantis-glow)] font-bold absolute -top-2.5 left-3 bg-[#131318] px-1.5 z-10 transition-colors group-focus-within:text-white">
                        Bot Designation
                    </label>
                    <input 
                        className="w-full bg-black/40 border-b-2 border-white/10 focus:border-[var(--mantis-glow)] text-lg font-headline p-4 transition-all focus:ring-0 text-white placeholder:text-white/10"
                        type="text" 
                        value={botName || ''}
                        onChange={(e) => setBotName(e.target.value)}
                        disabled={isLoading}
                        placeholder="Assign Designation..."
                    />
                </div>
                <button 
                    onClick={handleSave}
                    disabled={isLoading || !isDirty}
                    className="bg-[var(--mantis-glow)] text-black font-bold py-3.5 px-6 rounded-xl flex items-center justify-center gap-2 hover:brightness-110 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(34,197,94,0.2)] disabled:opacity-20 disabled:cursor-not-allowed"
                >
                    <Save size={18} />
                    {isLoading ? 'Deploying Changes...' : 'Save Identity Profile'}
                </button>
            </div>
        </section>
    );
};
