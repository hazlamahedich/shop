import React from 'react';

interface ProviderNode {
  name: string;
  cost: number;
}

interface NodeDistributionProps {
  nodes: ProviderNode[];
  total: number;
}

export const NodeDistribution: React.FC<NodeDistributionProps> = ({ nodes, total }) => {
  return (
    <div className="space-y-6">
      <h3 className="text-sm font-black text-white uppercase tracking-[0.2em]">Node Distribution</h3>
      
      <div className="space-y-6">
        {nodes.map((node) => {
          const percentage = (node.cost / total) * 100;
          return (
            <div key={node.name} className="space-y-2">
              <div className="flex justify-between items-end">
                <span className="text-[10px] font-black text-white/60 uppercase tracking-widest">{node.name}</span>
                <span className="text-sm font-black text-[var(--mantis-glow)] tracking-tighter">
                  ${node.cost.toLocaleString()}
                </span>
              </div>
              <div className="relative w-full h-2 bg-white/5 rounded-full overflow-hidden p-[1px] shadow-[inset_0_1px_2px_rgba(0,0,0,0.4)]">
                <div 
                  className="h-full bg-[var(--mantis-glow)] rounded-full shadow-[0_0_10px_rgba(0,245,212,0.3)] transition-all duration-1000"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
