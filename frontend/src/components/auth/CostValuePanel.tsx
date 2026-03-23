import { BarChart3, TrendingUp, ShieldCheck, Zap } from 'lucide-react';

export function CostValuePanel() {
  return (
    <div className="hidden lg:flex flex-col justify-between w-full h-full p-12 bg-black/40 backdrop-blur-3xl border-r border-white/[0.05] relative overflow-hidden">
      {/* Glow effects */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[50%] bg-emerald-500/10 blur-[120px] rounded-full mix-blend-screen" />
        <div className="absolute bottom-0 right-0 w-[50%] h-[50%] bg-blue-500/5 blur-[100px] rounded-full mix-blend-screen" />
      </div>

      <div className="relative z-10 flex flex-col h-full justify-between">
        <div className="space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold tracking-widest uppercase shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <Zap size={14} className="animate-pulse" />
            <span>Mantis Pricing Engine</span>
          </div>
          <h1 className="text-5xl font-black text-white tracking-tight leading-[1.1] uppercase mantis-glow-text" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Total Control Over Your <br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-200">AI Spend.</span>
          </h1>
          <p className="text-white/60 text-lg leading-relaxed max-w-md">
            Deploy autonomous agents with absolute transparency. Zero hidden fees. Infinite ROI potential. Maximize your digital workforce efficiency.
          </p>
        </div>

        <div className="space-y-6 mt-12">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/[0.03] border border-white/[0.08] p-6 rounded-2xl hover:bg-white/[0.05] transition-colors group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4 text-emerald-400">
                  <BarChart3 size={20} />
                  <span className="text-xs font-black tracking-widest uppercase">Avg. ROI</span>
                </div>
                <div className="text-4xl font-black text-white group-hover:text-emerald-300 transition-colors drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>324%</div>
                <div className="text-xs font-medium text-white/40 mt-2">Across all enterprise deployments</div>
              </div>
            </div>
            
            <div className="bg-white/[0.03] border border-white/[0.08] p-6 rounded-2xl hover:bg-white/[0.05] transition-colors group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4 text-emerald-400">
                  <TrendingUp size={20} />
                  <span className="text-xs font-black tracking-widest uppercase">Cost Reduction</span>
                </div>
                <div className="text-4xl font-black text-white group-hover:text-emerald-300 transition-colors drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>-42%</div>
                <div className="text-xs font-medium text-white/40 mt-2">Compared to legacy support</div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-emerald-500/10 to-transparent border border-emerald-500/20 p-5 rounded-2xl flex items-start gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg shrink-0">
              <ShieldCheck size={24} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white mb-1 uppercase tracking-wider">Predictable Trajectory</h3>
              <p className="text-xs text-white/50 leading-relaxed">
                Our dynamic pricing model scales predictably with your usage. Set hard limits, monitor real-time token burn, and never face surprise charges at billing cycles.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 flex items-center justify-between text-xs text-white/30 uppercase tracking-widest font-black">
          <span>Neural Gateway v2.4</span>
          <span>End-to-End Encrypted</span>
        </div>
      </div>
    </div>
  );
}
