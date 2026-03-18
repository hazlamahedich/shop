/**
 * Register Page
 * 
 * Re-imagined with Mantis Neural aesthetic.
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { RegisterRequest } from '../types/auth';
import { GlassCard } from '../components/ui/GlassCard';
import { Cpu, Lock, User, Sparkles, ShieldAlert, ArrowRight, Zap, Check } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const { register, isAuthenticated, error, clearError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/onboarding', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password || !confirmPassword) {
      setLocalError('Neural synthesis incomplete');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Encryption keys do not match');
      return;
    }

    setIsLoading(true);
    setLocalError(null);

    try {
      const credentials: RegisterRequest = { email, password };
      await register(credentials);
      navigate('/onboarding', { replace: true });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Architecture generation failed';
      setLocalError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const errorMessage = localError || error;

  return (
    <div data-theme="mantis" className="min-h-screen flex items-center justify-center bg-[#050505] py-12 px-6 relative overflow-hidden">
      {/* Background Neural Ambience */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute bottom-1/2 right-1/2 translate-x-1/2 translate-y-1/2 w-full max-w-7xl h-[800px] bg-emerald-500/5 blur-[160px] rounded-full opacity-50" />
        <div className="absolute inset-0 opacity-[0.03] bg-[url('/neural-pattern.svg')] bg-center bg-repeat" />
      </div>

      <div className="max-w-md w-full relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
        <GlassCard accent="mantis" className="border-white/[0.05] shadow-[0_0_100px_rgba(0,0,0,0.5)] p-12 overflow-hidden group">
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
          
          <div className="space-y-10">
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-24 h-24 bg-emerald-500/10 rounded-[32px] border border-emerald-500/20 text-emerald-400 mb-2 relative group-hover:scale-110 transition-transform duration-700">
                <Sparkles size={40} className="animate-pulse" />
                <div className="absolute inset-0 animate-ping rounded-[32px] border-2 border-emerald-500/10 opacity-40" />
              </div>
              <div>
                <h1 className="text-4xl font-black text-white tracking-tight leading-none uppercase mantis-glow-text">Neural Origin</h1>
                <p className="text-[10px] font-black text-[var(--mantis-text-muted)] uppercase tracking-[0.4em] mt-3 ml-[0.4em]">Synthesize Agent Account</p>
              </div>
            </div>

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div className="space-y-2 group/input">
                  <label className="text-[9px] font-black text-[var(--mantis-text-muted)] uppercase tracking-[0.3em] ml-1">Entity Identifier</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-[var(--mantis-text-dim)]/30 group-focus-within/input:text-emerald-400 transition-colors">
                      <User size={18} />
                    </div>
                    <input
                      type="email"
                      required
                      placeholder="Neural ID (Email)"
                      className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500/40 focus:bg-emerald-500/[0.03] transition-all duration-500 placeholder:text-white/10"
                      value={email}
                      onChange={(e) => setEmail(e.target.value.trim())}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="space-y-2 group/input">
                  <label className="text-[9px] font-black text-[var(--mantis-text-muted)] uppercase tracking-[0.3em] ml-1">Primary Encryption</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-[var(--mantis-text-dim)]/30 group-focus-within/input:text-emerald-400 transition-colors">
                      <Lock size={18} />
                    </div>
                    <input
                      type="password"
                      required
                      placeholder="Assign Neural Key"
                      className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500/40 focus:bg-emerald-500/[0.03] transition-all duration-500 placeholder:text-white/10"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="space-y-2 group/input">
                  <label className="text-[9px] font-black text-[var(--mantis-text-muted)] uppercase tracking-[0.3em] ml-1">Key Verification</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-[var(--mantis-text-dim)]/30 group-focus-within/input:text-emerald-400 transition-colors">
                      <ShieldAlert size={18} />
                    </div>
                    <input
                      type="password"
                      required
                      placeholder="Confirm Neural Key"
                      className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500/40 focus:bg-emerald-500/[0.03] transition-all duration-500 placeholder:text-white/10"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>

              {errorMessage && (
                <div role="alert" className="p-5 bg-red-500/[0.03] border border-red-500/10 rounded-2xl flex items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                  <ShieldAlert size={18} className="text-red-500 flex-shrink-0" />
                  <p className="text-[11px] font-black text-red-500 uppercase tracking-widest">{errorMessage}</p>
                </div>
              )}

              <div className="space-y-6 pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full h-16 bg-emerald-500 hover:bg-emerald-400 text-black font-black text-[11px] uppercase tracking-[0.4em] rounded-2xl transition-all duration-500 shadow-[0_0_30px_rgba(16,185,129,0.2)] hover:shadow-[0_0_50px_rgba(16,185,129,0.4)] hover:-translate-y-1 flex items-center justify-center gap-3"
                >
                  {isLoading ? (
                    <>
                      <Zap size={18} className="animate-spin" />
                      Synthesizing...
                    </>
                  ) : (
                    <>
                      Register Agent
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>

                 <div className="text-center">
                  <Link to="/login" className="text-[10px] font-black text-[var(--mantis-text-dim)]/40 uppercase tracking-[0.2em] hover:text-emerald-400 transition-colors">Existing Entity? Uplink Here</Link>
                </div>
              </div>
            </form>
          </div>
        </GlassCard>

        {/* Requirements Card */}
        <div className="mt-8 grid grid-cols-3 gap-3 animate-in fade-in duration-1000 delay-500">
          {[
            { label: 'Entropy', val: '8+ chars' },
            { label: 'Casing', val: 'Mixed' },
            { label: 'Uplink', val: 'Secure' },
          ].map((req, i) => (
            <div key={i} className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-4 text-center space-y-1">
              <p className="text-[8px] font-black text-emerald-900/40 uppercase tracking-wider">{req.label}</p>
              <p className="text-[10px] font-black text-white/40 uppercase tracking-widest">{req.val}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
