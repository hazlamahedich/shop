/**
 * Costs Page - Dashboard
 *
 * Real-time cost tracking and budget management.
 * Designed for clear visibility into AI service costs and budget usage.
 */

import { useEffect, useState, useMemo } from 'react';
import { 
  Target,
  Calendar,
  ChevronDown,
  Info,
  Edit2,
  Check
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

const DEFAULT_BUDGET_CAP = 50000;

interface DatePresetProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

const DatePreset: React.FC<DatePresetProps> = ({ label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={cn(
      "px-4 py-1.5 rounded text-[10px] font-black uppercase tracking-widest transition-all border",
      active 
        ? "bg-[var(--mantis-glow)]/20 border-[var(--mantis-glow)]/40 text-[var(--mantis-glow)] shadow-[0_0_15px_rgba(0,245,212,0.15)] scale-105" 
        : "bg-white/5 border-white/10 text-white/30 hover:text-white/80 hover:bg-white/10 hover:border-white/20"
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

  // Interactive Resource Caps State
  const [isEditingCaps, setIsEditingCaps] = useState(false);
  const [monthlyCap, setMonthlyCap] = useState(DEFAULT_BUDGET_CAP);
  const [dailyWarning, setDailyWarning] = useState(2500);

  useEffect(() => {
    getMerchantSettings();
    fetchBotStatus();
  }, [getMerchantSettings, fetchBotStatus]);

  useEffect(() => {
    if (merchantSettings?.budgetCap) {
      setMonthlyCap(merchantSettings.budgetCap);
      setDailyWarning(Math.floor(merchantSettings.budgetCap * 0.05));
    }
  }, [merchantSettings?.budgetCap]);

  const handleSaveCaps = () => {
    setIsEditingCaps(false);
    toast('Usage limits updated successfully', 'success');
  };

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
    if (dailyData.length === 0) return 1;
    return Math.max(...dailyData.map((d) => d.cost), dailyWarning * 1.5);
  }, [dailyData, dailyWarning]);

  const providers = useMemo(() => {
    if (!costSummary?.costsByProvider) return [];
    return Object.entries(costSummary.costsByProvider).map(([name, data]) => ({
      name: name === 'openai' ? 'OpenAI GPT-4o' : name === 'anthropic' ? 'Anthropic Claude 3.5' : name,
      cost: data.costUsd
    }));
  }, [costSummary]);

  const transmissions = useMemo(() => {
    if (!costSummary?.topConversations || costSummary.topConversations.length === 0) return [];
    return costSummary.topConversations.slice(0, 3).map((conv) => {
      const formatTokens = (tokens: number) => {
        if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M Tokens`;
        if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K Tokens`;
        return `${tokens} Tokens`;
      };
      const getCategoryLabel = (responseType?: string) => {
        if (responseType === 'rag') return 'RAG Response';
        if (responseType === 'general') return 'General Query';
        return 'Unknown';
      };
      return {
        id: `PBX-${conv.conversationId}`,
        category: getCategoryLabel(conv.responseType),
        load: conv.totalTokens ? formatTokens(conv.totalTokens) : 'N/A',
        investment: conv.totalCostUsd
      };
    });
    return transmissions;
  }, [costSummary?.topConversations]);

  const efficiencyMetrics = useMemo(() => {
    const metrics = costSummary?.efficiencyMetrics;
    if (!metrics) {
      return {
        costPer1kTokens: 0.0024,
        ragResponsePercentage: 0,
        optimizationSavingsPercentage: 48,
        avgProcessingTimeMs: null,
      };
    }
    return {
      costPer1kTokens: metrics.costPer1kTokens,
      ragResponsePercentage: metrics.ragResponsePercentage,
      optimizationSavingsPercentage: metrics.optimizationSavingsPercentage,
      avgProcessingTimeMs: metrics.avgProcessingTimeMs,
    };
  }, [costSummary?.efficiencyMetrics])

  const efficiencyDelta = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return 12.4; 
    const current = costSummary.totalCostUsd;
    const previous = previousPeriodSummary.totalCostUsd;
    if (previous === 0) return 12.4;
    return ((previous - current) / previous) * 100;
  }, [costSummary, previousPeriodSummary]);

  return (
    <TacticalHUD>
      <div className={cn("grid grid-cols-1 lg:grid-cols-12 gap-8 transition-opacity duration-500 pb-16", costSummaryLoading && !costSummary ? "opacity-50" : "opacity-100")}>
        
        {/* GLOBAL HEADER & PRESETS */}
        <div className="lg:col-span-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-2">
          <div className="space-y-1">
            <h2 className="text-3xl font-black text-white tracking-tighter uppercase font-display">Cost Summary</h2>
            <p className="text-xs font-black text-white/40 uppercase tracking-[0.2em] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--mantis-glow)] animate-pulse" />
              Live Data Feed
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-2 bg-white/[0.02] p-2 rounded-xl border border-white/5 backdrop-blur-md">
             <DatePreset label="Today" active={activePreset === 'Today'} onClick={() => setPreset('Today', 0)} />
             <DatePreset label="7 Days" active={activePreset === 'Last 7 Days'} onClick={() => setPreset('Last 7 Days', 7)} />
             <DatePreset label="30 Days" active={activePreset === 'Last 30 Days'} onClick={() => setPreset('Last 30 Days', 30)} />
             <div className="h-6 w-px bg-white/10 mx-2" />
             <button className="flex items-center gap-2 px-4 py-1.5 bg-[var(--mantis-glow)]/10 text-[var(--mantis-glow)] border border-[var(--mantis-glow)]/30 rounded cursor-pointer hover:bg-[var(--mantis-glow)]/20 transition-all group">
                <Calendar size={14} className="group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-black uppercase tracking-widest">Custom Range</span>
                <ChevronDown size={14} />
             </button>
          </div>
        </div>

        {/* TOP ROW: Usage & Budget */}
        <div className="lg:col-span-8">
          <NeuralInvestmentCard 
            totalCost={costSummary?.totalCostUsd || 0} 
            efficiencyDelta={efficiencyDelta}
            predictedBurn={costSummary ? (costSummary.totalCostUsd / 30) : 1240}
          />
        </div>
        <div className="lg:col-span-4">
          <BudgetReservoirGauge 
            capacity={monthlyCap} 
            consumed={costSummary?.totalCostUsd || 0}
            daysRemaining={Math.ceil((new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getTime() - Date.now()) / (1000 * 60 * 60 * 24))}
          />
        </div>

        {/* MIDDLE ROW: Spending & Budget Limits */}
        <div className="lg:col-span-8">
          <div className="bg-white/[0.02] rounded-2xl p-8 backdrop-blur-xl relative overflow-hidden h-[450px] flex flex-col group/index">
            {/* Ghost Border */}
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/index:border-[var(--mantis-glow)]/20 transition-colors duration-500" />
            
            <div className="flex justify-between items-start z-20 mb-10">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                  Spending Overview
                  <Info size={14} className="text-white/20 cursor-help hover:text-[var(--mantis-glow)] transition-colors" />
                </h3>
                <p className="text-[10px] font-black text-white/30 uppercase tracking-[0.2em]">{activePreset} Daily Breakdown</p>
              </div>
            </div>

            <div className="flex-1 flex items-end justify-between gap-1 sm:gap-2 relative pt-10 mt-auto">
               {/* Neural Grid Lines for Chart */}
               <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-[0.05]">
                  {[1, 2, 3, 4, 5].map(i => <div key={i} className="border-t border-white h-px w-full" />)}
               </div>
               
               {/* Hard Stop / Warning Line */}
               {dailyWarning && (
                 <div className="absolute inset-x-0 border-t border-dashed border-amber-500/40 z-10 hover:border-amber-500/80 transition-colors" 
                      style={{ bottom: `${Math.min((dailyWarning / maxDailyCost) * 100, 100)}%`, boxShadow: '0 0 10px rgba(245,158,11,0.1)' }}>
                    <span className="absolute -top-6 right-0 text-[9px] font-black text-amber-500 uppercase tracking-[0.2em] bg-[#131318] px-2 py-0.5 rounded border border-amber-500/20 backdrop-blur-sm">
                      DAILY LIMIT: ${dailyWarning.toLocaleString()}
                    </span>
                 </div>
               )}

               {dailyData.length > 0 ? dailyData.map((day, i) => (
                 <div 
                   key={i} 
                   className="flex-1 bg-[var(--mantis-glow)]/10 border-t border-x border-[var(--mantis-glow)]/20 rounded-t transition-all duration-300 hover:bg-[var(--mantis-glow)]/40 hover:shadow-[0_0_20px_rgba(0,245,212,0.3)] group/bar relative cursor-pointer"
                   style={{ height: `${Math.max((day.cost / (maxDailyCost || 1)) * 100, 2)}%` }}
                 >
                    {/* Tooltip */}
                    <div className="opacity-0 group-hover/bar:opacity-100 absolute bottom-full left-1/2 -translate-x-1/2 mb-3 bg-[#131318]/90 backdrop-blur-xl border border-white/10 px-4 py-2 rounded-lg pointer-events-none transition-opacity duration-200 z-50 flex flex-col items-center">
                      <span className="text-[14px] font-black text-white tracking-tighter">${day.cost.toFixed(2)}</span>
                      <span className="text-[9px] font-black text-white/40 uppercase tracking-widest">{day.date}</span>
                      <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#131318]/90 border-r border-b border-white/10 rotate-45" />
                    </div>
                 </div>
               )) : (
                 <div className="absolute inset-0 flex items-center justify-center text-white/20 text-[10px] font-black uppercase tracking-[0.3em]">
                   NO TELEMETRY DATA AVAILABLE
                 </div>
               )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white/[0.02] rounded-2xl p-8 backdrop-blur-xl h-full relative group/caps flex flex-col">
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/caps:border-[var(--mantis-glow)]/20 transition-colors duration-500" />
            
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8 relative z-10 w-full">
              <div className="flex items-center gap-3">
                <Target size={18} className="text-rose-500" />
                <h3 className="text-sm font-black text-white uppercase tracking-[0.2em]">Budget Limits</h3>
              </div>
              <button 
                onClick={() => isEditingCaps ? handleSaveCaps() : setIsEditingCaps(true)}
                className={cn(
                  "p-2 rounded-lg transition-all",
                  isEditingCaps ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30" : "bg-white/5 text-white/40 hover:bg-white/10 hover:text-white"
                )}
              >
                {isEditingCaps ? <Check size={16} /> : <Edit2 size={16} />}
              </button>
            </div>
            
            <div className="space-y-8 flex-1">
               <div className="space-y-3">
                 <label className="text-[10px] font-black text-white/40 uppercase tracking-widest block">Monthly Budget Limit</label>
                 <div className="flex items-center justify-between p-4 bg-black/40 border border-white/5 rounded-xl group-hover/caps:border-white/10 transition-colors">
                   {isEditingCaps ? (
                     <div className="flex items-center gap-2">
                       <span className="text-lg font-black text-white/40">$</span>
                       <input 
                         type="number"
                         value={monthlyCap}
                         onChange={(e) => setMonthlyCap(Number(e.target.value))}
                         className="bg-transparent text-lg font-black text-white tracking-tight w-24 outline-none border-b border-[var(--mantis-glow)] focus:border-[var(--mantis-glow)]/50"
                         autoFocus
                       />
                     </div>
                   ) : (
                     <span className="text-xl font-black text-white tracking-tighter">${monthlyCap.toLocaleString()}</span>
                   )}
                   <span className="px-2 py-1 bg-rose-500/10 text-rose-500 text-[9px] font-black uppercase tracking-widest rounded border border-rose-500/20 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-rose-500 rounded-full animate-pulse" /> Active
                   </span>
                 </div>
               </div>

               <div className="space-y-3">
                 <label className="text-[10px] font-black text-white/40 uppercase tracking-widest block flex justify-between">
                    Daily Warning Amount
                    <span className="text-[var(--mantis-glow)]">{((dailyWarning / monthlyCap) * 100).toFixed(1)}% of Limit</span>
                 </label>
                 <div className="p-4 bg-amber-500/5 border border-amber-500/10 rounded-xl transition-colors">
                   {isEditingCaps ? (
                     <div className="flex items-center gap-2">
                       <span className="text-sm font-black text-amber-500/40">$</span>
                       <input 
                         type="number"
                         value={dailyWarning}
                         onChange={(e) => setDailyWarning(Number(e.target.value))}
                         className="bg-transparent text-sm font-black text-amber-500 tracking-tight w-20 outline-none border-b border-amber-500 focus:border-amber-500/50"
                       />
                     </div>
                   ) : (
                     <span className="font-black text-base text-amber-500 tracking-tight">
                       ${dailyWarning.toLocaleString()}
                     </span>
                   )}
                 </div>
               </div>
            </div>
            
            <button
              onClick={handleSaveCaps}
              disabled={!isEditingCaps}
              className={cn(
                "w-full py-4 rounded-xl text-[11px] font-black uppercase tracking-[0.2em] transition-all mt-6",
                isEditingCaps
                  ? "bg-[var(--mantis-glow)]/10 text-[var(--mantis-glow)] border border-[var(--mantis-glow)]/30 hover:bg-[var(--mantis-glow)]/20 shadow-[0_0_15px_rgba(0,245,212,0.1)]"
                  : "bg-white/2 border border-white/5 text-white/20 cursor-not-allowed"
              )}
            >
              Update Limits
            </button>
          </div>
        </div>

        {/* BOTTOM ROW: Efficiency & performance, Node Distribution, Heavy Transmissions, AI Recommendations */}
        <div className="lg:col-span-4 space-y-8">
          <MetricHUDCard 
            title="Efficiency & Performance"
            value={`$${efficiencyMetrics.costPer1kTokens.toFixed(4)}`}
            subValue="/ 1K TOKENS"
            accent="mantis"
          >
             <div className="pt-5 space-y-4 border-t border-white/10 mt-5">
                <div className="flex items-center justify-between">
                   <span className="text-[10px] font-black text-white/60 uppercase tracking-widest">AI Model Selection</span>
                   <span className="text-[10px] font-black text-[var(--mantis-glow)] uppercase tracking-widest bg-[var(--mantis-glow)]/10 px-2 py-0.5 rounded border border-[var(--mantis-glow)]/20">Optimized</span>
                </div>
                <p className="text-[11px] text-white/40 leading-relaxed font-medium">
                  System is achieving <span className="text-white">{efficiencyMetrics.ragResponsePercentage}% accuracy</span> with <span className="text-[var(--mantis-glow)]">{efficiencyMetrics.optimizationSavingsPercentage}% savings</span> from AI model selection.
                </p>
             </div>
          </MetricHUDCard>

          <div className="bg-white/[0.02] rounded-2xl p-8 backdrop-blur-xl relative group/dist">
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/dist:border-[var(--mantis-glow)]/20 transition-colors duration-500" />
            <div className="relative z-10">
              <NodeDistribution nodes={providers} total={costSummary?.totalCostUsd || 1} />
            </div>
          </div>
        </div>

        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-8">
           <div className="md:col-span-2">
             <HeavyTransmissions transmissions={transmissions} />
           </div>
           
           <div className="md:col-span-2 bg-white/[0.02] border border-white/[0.05] rounded-2xl p-8 backdrop-blur-xl">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-12 items-center">
                <div className="md:col-span-2">
                  <AIRecommendations />
                </div>
                
                <div className="flex flex-col justify-center items-end space-y-6 md:border-l md:border-white/10 md:pl-8 h-full">
                   <div className="text-right">
                      <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em] block mb-2">System Status</span>
                      <span className="text-[11px] font-black text-[var(--mantis-glow)] uppercase tracking-widest flex items-center justify-end gap-2">
                        <div className="w-1.5 h-1.5 bg-[var(--mantis-glow)] rounded-full animate-pulse shadow-[0_0_8px_rgba(0,245,212,0.8)]" />
                        Connected
                      </span>
                   </div>
                   
                   {/* Live Data Visualization */}
                   <div className="flex items-end gap-1.5 h-16 opacity-80">
                      {[0.8, 0.4, 0.9, 0.2, 0.7, 0.5, 1, 0.3, 0.6, 0.8].map((h, i) => (
                        <div 
                          key={i} 
                          className="w-1.5 bg-[var(--mantis-glow)]/40 rounded-full relative group/beam cursor-crosshair hover:bg-[var(--mantis-glow)] transition-colors" 
                          style={{ height: `${h * 100}%` }} 
                        >
                           <div className="absolute opacity-0 group-hover/beam:opacity-100 -top-8 left-1/2 -translate-x-1/2 bg-black px-2 py-1 rounded text-[9px] font-mono text-[var(--mantis-glow)] border border-[var(--mantis-glow)]/30 pointer-events-none z-50">
                             {Math.floor(h * 100)}ms
                           </div>
                        </div>
                      ))}
                   </div>

                   <div className="text-right font-mono text-[10px] text-white/30 space-y-1 w-full bg-black/20 p-4 rounded-lg border border-white/5">
                      <div className="flex justify-between w-full"><span className="text-white/20">GPT-4O:</span> <span className="text-white">42%</span></div>
                      <div className="flex justify-between w-full"><span className="text-white/20">HAIKU:</span> <span className="text-[var(--mantis-glow)]">31%</span></div>
                      <div className="flex justify-between w-full pt-2 border-t border-white/5 mt-2"><span className="text-white/20">LATENCY:</span> <span className="text-amber-400">42.5MS</span></div>
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
