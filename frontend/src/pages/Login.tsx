/**
 * Login Page
 * 
 * Re-imagined with Mantis Neural aesthetic.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { LoginRequest } from '../types/auth';
import { GlassCard } from '../components/ui/GlassCard';
import { Cpu, Lock, User, ShieldAlert, ArrowRight, Zap } from 'lucide-react';
import { CostValuePanel } from '../components/auth/CostValuePanel';
import { Interactive3DBackground } from '../components/ui/Interactive3DBackground';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, error, clearError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      setLocalError('Neural signature incomplete');
      return;
    }

    setIsLoading(true);
    setLocalError(null);

    try {
      const credentials: LoginRequest = { email, password };
      await login(credentials);

      const from = (location.state as any)?.from?.pathname
        || sessionStorage.getItem('intendedDestination')
        || '/dashboard';

      sessionStorage.removeItem('intendedDestination');
      navigate(from, { replace: true });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Uplink failed';
      if ((err as any).code === 2011) {
        setLocalError('Rate limit exceeded. Await neural recovery.');
      } else {
        setLocalError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const errorMessage = localError || error;

  return (
    <div data-theme="mantis" className="min-h-screen flex bg-[#0e0e13] relative overflow-hidden">
      {/* 3D Background */}
      <Interactive3DBackground />

      <div className="flex w-full h-screen z-10 relative">
        {/* Left Pane: Cost & Value Proposition */}
        <div className="hidden lg:block lg:w-1/2 xl:w-[55%] h-full">
          <CostValuePanel />
        </div>

        {/* Right Pane: Authentication Form */}
        <div className="w-full lg:w-1/2 xl:w-[45%] h-full flex items-center justify-center p-6 sm:p-12 overflow-y-auto">
          <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <GlassCard accent="mantis" className="bg-[#131318]/80 backdrop-blur-xl border border-white/[0.05] shadow-[0_0_100px_rgba(0,0,0,0.5)] p-10 sm:p-12 overflow-hidden group">
              <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
              
              <div className="space-y-12">
                <div className="space-y-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 text-emerald-400 mb-2 relative group-hover:scale-105 transition-transform duration-700">
                    <Cpu size={32} className="animate-pulse" />
                    <div className="absolute inset-0 animate-ping rounded-2xl border-2 border-emerald-500/10 opacity-40" />
                  </div>
                  <div>
                    <h2 className="text-3xl font-black text-white tracking-tight leading-none uppercase mantis-glow-text" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>Neural Gateway</h2>
                    <p className="text-[10px] font-black text-emerald-500/70 uppercase tracking-[0.4em] mt-3">Initialize Authenticator</p>
                  </div>
                </div>

                <form className="space-y-8" onSubmit={handleSubmit}>
                  <div className="space-y-6">
                    <div className="space-y-2 group/input">
                      <label className="text-[9px] font-black text-white/40 uppercase tracking-[0.3em] pl-1">Credential Interface</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/30 group-focus-within/input:text-emerald-400 transition-colors">
                          <User size={18} />
                        </div>
                        <input
                          type="email"
                          required
                          placeholder="Neural ID (Email)"
                          className="w-full h-14 bg-[#1f1f26] border-b-2 border-transparent pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500 focus:bg-[#25252c] transition-all duration-300 placeholder:text-white/20 rounded-t-lg"
                          value={email}
                          onChange={(e) => setEmail(e.target.value.trim())}
                          disabled={isLoading}
                        />
                      </div>
                    </div>

                    <div className="space-y-2 group/input">
                      <label className="text-[9px] font-black text-white/40 uppercase tracking-[0.3em] pl-1">Encryption Key</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/30 group-focus-within/input:text-emerald-400 transition-colors">
                          <Lock size={18} />
                        </div>
                        <input
                          type="password"
                          required
                          placeholder="Neural Key"
                          className="w-full h-14 bg-[#1f1f26] border-b-2 border-transparent pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500 focus:bg-[#25252c] transition-all duration-300 placeholder:text-white/20 rounded-t-lg"
                          value={password}
                          onChange={(e) => setPassword(e.target.value.trim())}
                          disabled={isLoading}
                        />
                      </div>
                    </div>
                  </div>

                  {errorMessage && (
                    <div role="alert" className="p-4 bg-red-500/[0.05] border border-red-500/20 rounded-lg flex items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                      <ShieldAlert size={18} className="text-red-500 flex-shrink-0" />
                      <p className="text-[11px] font-bold text-red-500 uppercase tracking-wider">{errorMessage}</p>
                    </div>
                  )}

                  <div className="space-y-6">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-14 bg-gradient-to-r from-[#12f8d7] to-[#00e8c9] hover:brightness-110 text-[#00443a] font-black text-[12px] uppercase tracking-[0.3em] rounded-lg transition-all duration-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.4),_0_0_20px_rgba(18,248,215,0.2)] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.5),_0_0_30px_rgba(18,248,215,0.4)] hover:-translate-y-0.5 flex items-center justify-center gap-3"
                    >
                      {isLoading ? (
                        <>
                          <Zap size={18} className="animate-spin" />
                          Decrypting...
                        </>
                      ) : (
                        <>
                          Execute Uplink
                          <ArrowRight size={18} />
                        </>
                      )}
                    </button>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 pt-2">
                      <Link to="/register" className="text-[10px] font-bold text-white/50 uppercase tracking-[0.1em] border-b border-white/10 pb-1 hover:text-emerald-400 hover:border-emerald-400 transition-colors">Generate Account</Link>
                      <div className="hidden sm:block w-px h-3 bg-white/10" />
                      <button type="button" className="text-[10px] font-bold text-white/50 uppercase tracking-[0.1em] border-b border-white/10 pb-1 hover:text-emerald-400 hover:border-emerald-400 transition-colors">Recover ID</button>
                    </div>
                  </div>
                </form>
              </div>
            </GlassCard>

            {/* Security Notice */}
            <div className="mt-8 text-center animate-in fade-in duration-1000 delay-500">
              <div className="inline-flex items-center gap-3 px-5 py-2.5 bg-[#131318]/50 backdrop-blur-md border border-white/[0.05] rounded-full shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                <div className="w-1.5 h-1.5 bg-[#12f8d7] rounded-full animate-pulse shadow-[0_0_8px_#12f8d7]" />
                <p className="text-[9px] font-bold text-white/40 uppercase tracking-[0.2em]">Neural Interface: Secure Encryption Active</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
