import React from 'react';
import { MetricHUDCard } from './MetricHUDCard';

interface NeuralInvestmentCardProps {
  totalCost: number;
  efficiencyDelta: number;
  predictedBurn: number;
}

export const NeuralInvestmentCard: React.FC<NeuralInvestmentCardProps> = ({
  totalCost,
  efficiencyDelta,
  predictedBurn
}) => {
  return (
    <MetricHUDCard
      title="Total AI Usage"
      value={`$${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
      accent="mantis"
      trend={{
        value: `Efficiency Change: ${efficiencyDelta > 0 ? '+' : ''}${efficiencyDelta.toFixed(1)}%`,
        isPositive: efficiencyDelta >= 0
      }}
    >
      <div className="flex flex-col items-end">
        <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">Predicted Cost</span>
        <span className="text-sm font-black text-white tracking-widest">${predictedBurn.toLocaleString()}/Day</span>
      </div>
    </MetricHUDCard>
  );
};
