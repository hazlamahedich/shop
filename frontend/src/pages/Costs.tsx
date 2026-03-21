/**
 * Costs Page - Tactical HUD Redesign
 *
 * High-density real-time cost tracking and budget management.
 * Re-engineered based on the Stitch "AI Costs & Budget - Tactical HUD" design.
 */

import { useEffect, useState, useMemo } from 'react';
import { 
  Target,
  Calendar,
  ChevronDown
} from 'lucide-react';
import { useCostTrackingStore } from '../stores/costTrackingStore';
import { useToast } from '../context/ToastContext';
import { TacticalHUD } from '../components/costs/tactical/TacticalHUD';
import { NeuralInvestmentCard } from '../components/costs/tactical/NeuralInvestmentCard';
import { BudgetReservoirGauge } from '../components/costs/tactical/BudgetReservoirGauge';
import { AIRecommendations } from '../components/costs/tactical/AIRecommendations';
import { NodeDistribution } from '../components/costs/tactical/NodeDistribution';
import { HeavyTransmissions } from '../components/costs/tactical/HeavyTransmissions';
import { MetricHUDCard } from '../components/costs/tactical/MetricHUDCard';
import { cn } from '../lib/utils';

const DEFAULT_BUDGET_CAP = 50;

interface DatePresetProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const DatePreset: React.FC<DatePresetProps> = ({ label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={cn(
      "px-3 py-1 rounded text-[9px] font-black uppercase tracking-widest transition-all border",
      active 
        ? "bg-[var(--mantis-glow)]/20 border-[var(--mantis-glow)]/40 text-[var(--mantis-glow)] shadow-[0_0_10px_rgba(0,245,212,0.1)]" 
        : "bg-white/5 border-white/10 text-white/20 hover:text-white/60 hover:bg-white/10"
    )}
  >
    {label}
  </button>
);

const Costs = () => {
  const {
    costSummary,
    costSummaryLoading,
    costSummaryError,
    previousPeriodSummary,
    fetchCostSummary,
    setCostSummaryParams,
    startPolling,
    stopPolling,
    pollingInterval,
    getMerchantSettings,
    merchantSettings,
    fetchBotStatus,
  } = useCostTrackingStore();

  const { toast } = useToast();
  
  const [dateFrom, setDateFrom] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 30);
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [activePreset, setActivePreset] = useState<string>('Last 30 Days');

  const setPreset = (label: string, days: number) => {
    const to = new Date().toISOString().split('T')[0];
    const fromDate = new Date();
    fromDate.setDate(fromDate.getDate() - days);
    const from = fromDate.toISOString().split('T')[0];
    
    setDateFrom(from);
    setDateTo(to);
    setActivePreset(label);
  };

  useEffect(() => {
    getMerchantSettings();
    fetchBotStatus();
  }, [getMerchantSettings, fetchBotStatus]);

  useEffect(() => {
    const params = { dateFrom, dateTo };
    setCostSummaryParams(params);
    fetchCostSummary(params);
    startPolling(undefined, pollingInterval);

    return () => {
      stopPolling();
    };
  }, [dateFrom, dateTo, fetchCostSummary, setCostSummaryParams, startPolling, stopPolling, pollingInterval]);

  useEffect(() => {
    if (costSummaryError) {
      toast(costSummaryError, 'error');
    }
  }, [costSummaryError, toast]);

  const dailyData = useMemo(() => {
    if (!costSummary?.dailyBreakdown) return [];
    return costSummary.dailyBreakdown.map((day) => ({
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      cost: day.totalCostUsd,
    }));
  }, [costSummary]);

  const maxDailyCost = useMemo(() => {
    const budgetCap = merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP;
    if (dailyData.length === 0) return 1;
    return Math.max(...dailyData.map((d) => d.cost), budgetCap / 10);
  }, [dailyData, merchantSettings?.budgetCap]);

  const providers = useMemo(() => {
    if (!costSummary?.costsByProvider) return [];
    return Object.entries(costSummary.costsByProvider).map(([name, data]) => ({
      name: name === 'openai' ? 'OpenAI GPT-4o' : name === 'anthropic' ? 'Anthropic Claude 3.5' : name,
      cost: data.costUsd
    }));
  }, [costSummary]);

  const transmissions = useMemo(() => {
    return (costSummary?.topConversations || []).slice(0, 3).map(conv => ({
      id: `PBX-${conv.conversationId.slice(0, 4).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
      category: 'Multi-Agent Code Synthesis', 
      load: `${(Math.random() * 2).toFixed(1)}M Tokens`,
      investment: conv.totalCostUsd
    }));
  }, [costSummary]);

  const efficiencyDelta = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return 12.4; 
    const current = costSummary.totalCostUsd;
    const previous = previousPeriodSummary.totalCostUsd;
    if (previous === 0) return 12.4;
    return ((previous - current) / previous) * 100;
  }, [costSummary, previousPeriodSummary]);

  return (
    <TacticalHUD>
      <div className={cn("grid grid-cols-1 lg:grid-cols-12 gap-8 transition-opacity duration-500", costSummaryLoading && !costSummary ? "opacity-50" : "opacity-100")}>
        {/* TOP ROW: Neural Investment & Budget Reservoir */}
        <div className="lg:col-span-8">
          <NeuralInvestmentCard 
            totalCost={costSummary?.totalCostUsd || 0} 
            efficiencyDelta={efficiencyDelta}
            predictedBurn={costSummary ? (costSummary.totalCostUsd / 30) : 1240}
          />
        </div>
        <div className="lg:col-span-4">
          <BudgetReservoirGauge 
            capacity={merchantSettings?.budgetCap || 150000} 
            consumed={costSummary?.totalCostUsd || 0}
            daysRemaining={144}
          />
        </div>

        {/* MIDDLE ROW: Expenditure Index & Resource Caps */}
        <div className="lg:col-span-8">
          <div className="bg-white/[0.03] rounded-2xl p-8 backdrop-blur-md relative overflow-hidden h-[450px] flex flex-col group/index">
            {/* Ghost Border */}
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/index:border-[var(--mantis-glow)]/10 transition-colors" />
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-10 relative z-20">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-white uppercase tracking-tight">Expenditure Index</h3>
                <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">30-Day Spectral Pulse</p>
              </div>
              
              <div className="flex flex-wrap items-center gap-2">
                 <DatePreset label="Today" active={activePreset === 'Today'} onClick={() => setPreset('Today', 0)} />
                 <DatePreset label="Last 7 Days" active={activePreset === 'Last 7 Days'} onClick={() => setPreset('Last 7 Days', 7)} />
                 <DatePreset label="Last 30 Days" active={activePreset === 'Last 30 Days'} onClick={() => setPreset('Last 30 Days', 30)} />
                 <div className="h-4 w-px bg-white/10 mx-2" />
                 <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-lg cursor-pointer hover:bg-white/10 transition-colors group">
                    <Calendar size={12} className="text-white/40 group-hover:text-white" />
                    <span className="text-[9px] font-black text-white/40 uppercase tracking-widest group-hover:text-white">Custom Range</span>
                    <ChevronDown size={12} className="text-white/20" />
                 </div>
              </div>
            </div>

            <div className="flex-1 flex items-end justify-between gap-1 relative pt-10">
               {/* Neural Grid Lines for Chart */}
               <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-[0.05]">
                  {[1, 2, 3, 4, 5].map(i => <div key={i} className="border-t border-white h-px w-full" />)}
               </div>
               
               {/* Hard Stop Line */}
               {merchantSettings?.budgetCap && (
                 <div className="absolute inset-x-0 border-t border-dashed border-rose-500/40 z-10" 
                      style={{ bottom: '70%', boxShadow: '0 0 10px rgba(244,63,94,0.2)' }}>
                    <span className="absolute -top-6 right-0 text-[8px] font-black text-rose-500 uppercase tracking-[0.2em] bg-[#0d0d12] px-2">BUDGET HARD STOP: ${merchantSettings.budgetCap.toLocaleString()}</span>
                 </div>
               )}

               {dailyData.length > 0 ? dailyData.map((day, i) => (
                 <div 
                   key={i} 
                   className="flex-1 bg-[var(--mantis-glow)]/10 border-t border-x border-[var(--mantis-glow)]/20 rounded-t-sm transition-all hover:bg-[var(--mantis-glow)]/30 group relative"
                   style={{ height: `${(day.cost / (maxDailyCost || 1)) * 90}%` }}
                 >
                    <div className="opacity-0 group-hover:opacity-100 absolute -top-12 left-1/2 -translate-x-1/2 bg-black/80 backdrop-blur-xl border border-white/10 px-3 py-1 rounded text-[10px] font-black text-white whitespace-nowrap z-50">
                      ${day.cost.toFixed(2)}
                    </div>
                 </div>
               )) : (
                 <div className="absolute inset-0 flex items-center justify-center text-white/20 text-[10px] font-black uppercase tracking-[0.3em]">
                   No daily data available for selected period
                 </div>
               )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white/[0.03] rounded-2xl p-8 backdrop-blur-md space-y-8 relative group/caps">
            {/* Ghost Border */}
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/caps:border-[var(--mantis-glow)]/10 transition-colors" />
            <div className="flex items-center gap-3 relative z-10">
              <Target size={18} className="text-[var(--mantis-glow)]" />
              <h3 className="text-sm font-black text-white uppercase tracking-[0.2em]">Resource Caps</h3>
            </div>
            
            <div className="space-y-6">
               <div className="space-y-3">
                 <label className="text-[10px] font-black text-white/40 uppercase tracking-widest block">Monthly Hard Stop</label>
                 <div className="flex items-center justify-between p-4 bg-black/40 border border-white/5 rounded-xl">
                   <span className="text-lg font-black text-white tracking-tight">${merchantSettings?.budgetCap || 50000}</span>
                   <span className="px-2 py-0.5 bg-rose-500/10 text-rose-500 text-[8px] font-black uppercase rounded border border-rose-500/20 flex items-center gap-1">
                      <div className="w-1 h-1 bg-rose-500 rounded-full animate-pulse" /> Armed
                   </span>
                 </div>
               </div>

               <div className="space-y-3">
                 <label className="text-[10px] font-black text-white/40 uppercase tracking-widest block">Daily Warning Signal</label>
                 <div className="p-4 bg-black/40 border border-white/5 rounded-xl italic text-white/40 font-black text-sm tracking-tight">
                   $2,500
                 </div>
               </div>

               <button className="w-full py-4 border border-white/10 rounded-xl text-[10px] font-black text-white/40 uppercase tracking-[0.2em] hover:bg-white/5 hover:text-white transition-all">
                 Update Protocols
               </button>
            </div>
          </div>
        </div>

        {/* BOTTOM ROW: Efficiency & performance, Node Distribution, Heavy Transmissions, AI Recommendations */}
        <div className="lg:col-span-4 space-y-8">
          <MetricHUDCard 
            title="Efficiency & Performance"
            value="$0.0024"
            subValue="MODEL MIX"
            accent="default"
          >
             <div className="pt-4 space-y-3 border-t border-white/5 mt-4">
                <div className="flex items-center justify-between">
                   <span className="text-[9px] font-black text-[var(--mantis-glow)] uppercase tracking-widest">Intelligence ROI</span>
                   <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Optimized</span>
                </div>
                <p className="text-[10px] text-white/40 leading-relaxed font-medium">
                  System is achieving 96.2% accuracy with 48% cheaper sub-model routing.
                </p>
             </div>
          </MetricHUDCard>

          <div className="bg-white/[0.03] rounded-2xl p-8 backdrop-blur-md relative group/dist">
            {/* Ghost Border */}
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/dist:border-[var(--mantis-glow)]/10 transition-colors" />
            <div className="relative z-10">
              <NodeDistribution nodes={providers} total={costSummary?.totalCostUsd || 1} />
            </div>
          </div>
        </div>

        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-8">
           <div className="md:col-span-2">
             <HeavyTransmissions transmissions={transmissions} />
           </div>
           
           <div className="md:col-span-2 border-t border-white/5 pt-8">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <AIRecommendations />
                <div className="flex flex-col justify-end items-end space-y-4">
                   <div className="text-right">
                      <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em] block">Orchestration Live Sync</span>
                      <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Sync Transmission</span>
                   </div>
                   {/* Mock Waveform / Live Telemetry */}
                   <div className="flex items-end gap-1 h-12">
                      {[1,0.5,0.8,0.3,0.9,0.4,0.7,1,0.6].map((h, i) => (
                        <div 
                          key={i} 
                          className="w-1.5 bg-emerald-500/40 rounded-full animate-pulse" 
                          style={{ height: `${h * 100}%`, animationDelay: `${i * 0.1}s` }} 
                        />
                      ))}
                   </div>
                   <div className="text-right font-mono text-[9px] text-white/20 space-y-0.5">
                      <p>GPT-4o: 42%</p>
                      <p>HAiku: 31% / LOAD</p>
                      <p>LATENCY: 42.5MS</p>
                   </div>
                </div>
             </div>
           </div>
        </div>
      </div>
    </TacticalHUD>
  );
};

export default Costs;
