import * as React from 'react';
import { Widget } from '../widget/Widget';
import { GlassCard } from '../components/ui/GlassCard';
import { Terminal, Shield, Info, Palette } from 'lucide-react';

const defaultTheme = {
  primaryColor: '#10b981', // Emerald 500
  backgroundColor: '#0a0a0a',
  textColor: '#ffffff',
  botBubbleColor: '#121212',
  userBubbleColor: '#10b981',
  position: 'bottom-right' as const,
  borderRadius: 24,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

function parseThemeFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const theme: Record<string, unknown> = {};

  for (const [key, value] of params) {
    if (key.startsWith('theme[')) {
      const themeKey = key.match(/theme\[(.+)\]/)?.[1];
      if (themeKey) {
        if (value.startsWith('%23') || value.startsWith('#')) {
          theme[themeKey] = decodeURIComponent(value);
        } else if (!isNaN(Number(value))) {
          theme[themeKey] = parseInt(value, 10);
        } else {
          theme[themeKey] = value;
        }
      }
    }
  }

  return Object.keys(theme).length > 0 ? theme : {};
}

function getMerchantId() {
  const params = new URLSearchParams(window.location.search);
  return params.get('merchantId') || '1';
}

function getSessionId() {
  const params = new URLSearchParams(window.location.search);
  return params.get('sessionId') || undefined;
}

export default function WidgetTestPage() {
  const theme = { ...defaultTheme, ...parseThemeFromUrl() };
  const merchantId = getMerchantId();
  const sessionId = getSessionId();

  return (
    <div className="min-h-screen bg-[#030303] text-white p-10 font-sans relative overflow-hidden">
      {/* Background Depth */}
      <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-emerald-500/10 to-transparent pointer-events-none"></div>

      <div className="max-w-4xl mx-auto space-y-12">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <Terminal size={12} />
            E2E Testing Module
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Widget Validation
          </h1>
          <p className="text-lg text-emerald-900/40 font-medium max-w-xl">
            Isolated environment for verifying UI performance and neural link fidelity.
          </p>
        </div>

        <GlassCard accent="mantis" className="p-12 space-y-10 border-white/[0.03] bg-white/[0.01]">
          <div className="flex items-start gap-8">
            <div className="w-16 h-16 bg-white/5 rounded-[24px] flex items-center justify-center text-emerald-500 border border-white/5 shadow-2xl">
              <Shield size={32} />
            </div>
            <div className="space-y-3">
              <h2 className="text-xl font-black text-white uppercase tracking-tight">Active Shielding</h2>
              <p className="text-sm text-emerald-900/60 font-medium max-w-lg leading-relaxed">
                This diagnostic terminal is optimized for automated quality assurance. The live widget instance is active in the bottom-right quadrant.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl space-y-4">
              <div className="flex items-center gap-3 text-emerald-400">
                 <Palette size={18} />
                 <span className="text-[10px] font-black uppercase tracking-widest">Calibration Parameters</span>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center justify-between text-[11px] font-black uppercase tracking-widest border-b border-white/[0.03] pb-2 text-white/40">
                  <span>Primary Color</span>
                  <code className="text-emerald-500">?theme[primaryColor]=%23ff0000</code>
                </li>
                <li className="flex items-center justify-between text-[11px] font-black uppercase tracking-widest border-b border-white/[0.03] pb-2 text-white/40">
                  <span>Alignment</span>
                  <code className="text-emerald-500">?theme[position]=bottom-left</code>
                </li>
                <li className="flex items-center justify-between text-[11px] font-black uppercase tracking-widest border-b border-white/[0.03] pb-2 text-white/40">
                  <span>Curvature</span>
                  <code className="text-emerald-500">?theme[borderRadius]=24</code>
                </li>
              </ul>
            </div>

            <div className="p-6 bg-white/[0.02] border border-white/5 rounded-2xl space-y-4">
              <div className="flex items-center gap-3 text-emerald-400">
                 <Info size={18} />
                 <span className="text-[10px] font-black uppercase tracking-widest">Diagnostic Info</span>
              </div>
              <p className="text-[11px] font-medium text-emerald-900/60 leading-relaxed uppercase tracking-[0.1em]">
                This page utilizes standard browser APIs for E2E validation. Ensure the target merchant ID is correctly mapped in the URL registry.
              </p>
              <div className="pt-2">
                 <code className="px-3 py-1 bg-white/5 rounded-lg text-[10px] font-black text-emerald-500 lowercase">?merchantId={merchantId}</code>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>

      <Widget merchantId={merchantId} theme={theme} initialSessionId={sessionId} />
    </div>
  );
}
