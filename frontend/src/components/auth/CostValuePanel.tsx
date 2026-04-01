import { MessageSquare, ShoppingBag, Clock, ShieldCheck } from 'lucide-react';

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
          {/* Logo */}
          <div className="pb-8">
            <img
              src="/src/assets/logo.png"
              alt="Logo"
              className="h-40 w-auto object-contain drop-shadow-[0_0_40px_rgba(18,248,215,0.4)]"
            />
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold tracking-widest uppercase shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <MessageSquare size={14} className="animate-pulse" />
            <span>AI Assistant Platform</span>
          </div>
          <h1 className="text-5xl font-black text-white tracking-tight leading-[1.1] uppercase mantis-glow-text" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Your AI Assistant,<br/><span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-200">Your Way.</span>
          </h1>
          <p className="text-white/60 text-lg leading-relaxed max-w-md">
            Choose how you want to help your customers - answer questions, help with shopping, or both. Available 24/7 to support your business.
          </p>
        </div>

        <div className="space-y-6 mt-12">
          {/* Feature Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/[0.03] border border-white/[0.08] p-6 rounded-2xl hover:bg-white/[0.05] transition-colors group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4 text-emerald-400">
                  <MessageSquare size={20} />
                  <span className="text-xs font-black tracking-widest uppercase">Customer Support</span>
                </div>
                <p className="text-sm font-medium text-white/60 leading-relaxed">
                  Answer customer questions instantly, 24/7
                </p>
              </div>
            </div>

            <div className="bg-white/[0.03] border border-white/[0.08] p-6 rounded-2xl hover:bg-white/[0.05] transition-colors group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4 text-emerald-400">
                  <ShoppingBag size={20} />
                  <span className="text-xs font-black tracking-widest uppercase">Shopping Helper</span>
                </div>
                <p className="text-sm font-medium text-white/60 leading-relaxed">
                  Help customers find the right products
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white/[0.03] border border-white/[0.08] p-6 rounded-2xl hover:bg-white/[0.05] transition-colors group relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4 text-emerald-400">
                <Clock size={20} />
                <span className="text-xs font-black tracking-widest uppercase">Always Available</span>
              </div>
              <p className="text-sm font-medium text-white/60 leading-relaxed">
                Never miss a customer inquiry. Your AI assistant works around the clock so you don't have to.
              </p>
            </div>
          </div>

          <div className="bg-gradient-to-r from-emerald-500/10 to-transparent border border-emerald-500/20 p-5 rounded-2xl flex items-start gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg shrink-0">
              <ShieldCheck size={24} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white mb-1 uppercase tracking-wider">Simple & Transparent</h3>
              <p className="text-xs text-white/50 leading-relaxed">
                Set up your AI assistant in minutes. Choose the mode that fits your business needs - customer support, shopping assistance, or both.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-12 flex items-center justify-between text-xs text-white/30 uppercase tracking-widest font-black">
          <span>v2.4</span>
          <span>Secure & encrypted</span>
        </div>
      </div>
    </div>
  );
}
