import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DollarSign, AlertTriangle, Cpu, ChevronRight, Zap } from 'lucide-react';
import { costTrackingService } from '../../services/costTracking';
import type { CostSummary } from '../../types/cost';
import { StatCard } from './StatCard';

function formatUSD(value: number): string {
  if (value < 0.001) return '$0.00';
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

interface ProviderRow {
  provider: string;
  cost: number;
  percentage: number;
}

function getProviderBreakdown(data: CostSummary | undefined): ProviderRow[] {
  if (!data?.costsByProvider) return [];
  const total = Object.values(data.costsByProvider).reduce((s, v) => s + v.costUsd, 0);
  if (total === 0) return [];
  return Object.entries(data.costsByProvider)
    .map(([provider, summary]) => ({
      provider,
      cost: summary.costUsd,
      percentage: Math.round((summary.costUsd / total) * 100),
    }))
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 3);
}

const PROVIDER_ACCENTS = [
  'text-blue-400 bg-blue-400/10 border-blue-400/20',
  'text-purple-400 bg-purple-400/10 border-purple-400/20',
  'text-[#00f5d4] bg-[#00f5d4]/10 border-[#00f5d4]/20',
];

export function AICostWidget() {
  const navigate = useNavigate();

  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    .toISOString()
    .split('T')[0];

  const { data: envelope, isLoading, isError } = useQuery({
    queryKey: ['costs', 'summary', 'monthly'],
    queryFn: () => costTrackingService.getCostSummary({ dateFrom: monthStart }),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const summaryData = envelope?.data as CostSummary | undefined;
  const totalCost = typeof summaryData?.totalCostUsd === 'number' ? summaryData.totalCostUsd : 0;
  const requestCount = typeof summaryData?.requestCount === 'number' ? summaryData.requestCount : 0;

  const previousCost = summaryData?.previousPeriodSummary?.totalCostUsd;
  const momChangePercent = previousCost && previousCost > 0
    ? ((totalCost - previousCost) / previousCost) * 100
    : null;

  const budgetCap: number | null = null;
  const budgetPct = budgetCap && budgetCap > 0 ? (totalCost / budgetCap) * 100 : null;
  const isNearBudget = budgetPct !== null && budgetPct >= 80;

  const providers = getProviderBreakdown(summaryData);

  return (
    <StatCard
      title="Machine Tax"
      value={isLoading ? '...' : formatUSD(totalCost)}
      subValue="COMPUTE_BURN_MTD"
      icon={<Cpu size={18} />}
      accentColor={isNearBudget ? 'red' : 'blue'}
      isLoading={isLoading}
      trend={momChangePercent ?? undefined}
      data-testid="ai-cost-widget"
    >
      <div className="space-y-4 mt-4">
        {isError ? (
           <div className="flex items-center justify-center py-8">
             <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">BILLING_TELEMETRY_ERR</p>
           </div>
        ) : (
          <>
            <div className="flex items-center justify-between p-3 bg-white/5 border border-white/5 rounded-xl">
               <div>
                 <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">REQUEST_CYCLES</p>
                 <p className="text-xl font-black text-white">{requestCount.toLocaleString()}</p>
               </div>
               <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                 <Zap size={14} fill="currentColor" />
               </div>
            </div>

            {budgetPct !== null && (
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[9px] font-black uppercase tracking-widest">
                  <span className="text-white/20">CORE_BUDGET_LOAD</span>
                  <span className={isNearBudget ? 'text-rose-400 shine' : 'text-blue-400'}>{budgetPct.toFixed(0)}%</span>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ${isNearBudget ? 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]' : 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.3)]'}`}
                    style={{ width: `${Math.min(budgetPct, 100)}%` }}
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
               <p className="text-[9px] font-black text-white/10 uppercase tracking-[0.3em]">RESOURCE_DISTRIBUTION</p>
               <div className="space-y-1.5">
                  {providers.map((p, i) => (
                    <div key={p.provider} className="flex items-center justify-between group/provider">
                       <div className="flex items-center gap-2">
                          <div className={`w-1 h-3 rounded-full ${PROVIDER_ACCENTS[i].split(' ')[1]}`} />
                          <span className="text-[10px] font-black text-white/40 uppercase group-hover/provider:text-white/60 transition-colors">{p.provider}</span>
                       </div>
                       <div className="flex items-center gap-3">
                          <span className="text-[10px] font-black text-white/80">{formatUSD(p.cost)}</span>
                          <span className="text-[9px] font-black text-white/20">{p.percentage}%</span>
                       </div>
                    </div>
                  ))}
               </div>
            </div>

            <button
               onClick={() => navigate('/costs')}
               className="flex items-center justify-center gap-2 w-full mt-2 py-2.5 text-[10px] font-black text-blue-400/60 hover:text-blue-400 transition-all uppercase tracking-[0.2em] border border-blue-400/10 rounded-xl group/manage"
            >
               AUDIT_EXPENDITURE <ChevronRight size={12} className="group-hover/manage:translate-x-1 transition-transform" />
            </button>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default AICostWidget;
