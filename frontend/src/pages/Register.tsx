/**
 * Register Page
 *
 * Simple, easy-to-understand language for all users.
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { RegisterRequest } from '../types/auth';
import { GlassCard } from '../components/ui/GlassCard';
import { Lock, User, ShieldAlert, ArrowRight, Zap } from 'lucide-react';
import { CostValuePanel } from '../components/auth/CostValuePanel';
import { Interactive3DBackground } from '../components/ui/Interactive3DBackground';

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
      setLocalError('Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }

    setIsLoading(true);
    setLocalError(null);

    try {
      const credentials: RegisterRequest = { email, password };
      await register(credentials);
      navigate('/onboarding', { replace: true });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Account creation failed';
      setLocalError(errorMessage);
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

              <div className="space-y-10">
                <div className="space-y-6">
                  <div>
                    <h2 className="text-3xl font-black text-white tracking-tight leading-none uppercase mantis-glow-text" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>Create Your Account</h2>
                    <p className="text-[10px] font-black text-emerald-500/70 uppercase tracking-[0.4em] mt-3">Get started in minutes</p>
                  </div>
                </div>

                <form className="space-y-6" onSubmit={handleSubmit}>
                  <div className="space-y-4">
                    <div className="space-y-1.5 group/input">
                      <label className="text-[9px] font-black text-white/40 uppercase tracking-[0.3em] pl-1">Email Address</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/30 group-focus-within/input:text-emerald-400 transition-colors">
                          <User size={18} />
                        </div>
                        <input
                          type="email"
                          required
                          placeholder="your@email.com"
                          className="w-full h-14 bg-[#1f1f26] border-b-2 border-transparent pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500 focus:bg-[#25252c] transition-all duration-300 placeholder:text-white/20 rounded-t-lg"
                          value={email}
                          onChange={(e) => setEmail(e.target.value.trim())}
                          disabled={isLoading}
                        />
                      </div>
                    </div>

                    <div className="space-y-1.5 group/input">
                      <label className="text-[9px] font-black text-white/40 uppercase tracking-[0.3em] pl-1">Password</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/30 group-focus-within/input:text-emerald-400 transition-colors">
                          <Lock size={18} />
                        </div>
                        <input
                          type="password"
                          required
                          placeholder="Create a password"
                          className="w-full h-14 bg-[#1f1f26] border-b-2 border-transparent pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500 focus:bg-[#25252c] transition-all duration-300 placeholder:text-white/20 rounded-t-lg"
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>
                    </div>

                    <div className="space-y-1.5 group/input">
                      <label className="text-[9px] font-black text-white/40 uppercase tracking-[0.3em] pl-1">Confirm Password</label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-white/30 group-focus-within/input:text-emerald-400 transition-colors">
                          <ShieldAlert size={18} />
                        </div>
                        <input
                          type="password"
                          required
                          placeholder="Re-enter your password"
                          className="w-full h-14 bg-[#1f1f26] border-b-2 border-transparent pl-14 pr-6 text-white font-bold text-sm focus:outline-none focus:border-emerald-500 focus:bg-[#25252c] transition-all duration-300 placeholder:text-white/20 rounded-t-lg"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
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

                  <div className="space-y-6 pt-2">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-14 bg-gradient-to-r from-[#12f8d7] to-[#00e8c9] hover:brightness-110 text-[#00443a] font-black text-[12px] uppercase tracking-[0.3em] rounded-lg transition-all duration-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.4),_0_0_20px_rgba(18,248,215,0.2)] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.5),_0_0_30px_rgba(18,248,215,0.4)] hover:-translate-y-0.5 flex items-center justify-center gap-3"
                    >
                      {isLoading ? (
                        <>
                          <Zap size={18} className="animate-spin" />
                          Creating account...
                        </>
                      ) : (
                        <>
                          Create Account
                          <ArrowRight size={18} />
                        </>
                      )}
                    </button>

                     <div className="text-center">
                      <Link to="/login" className="text-[10px] font-bold text-white/50 uppercase tracking-[0.1em] border-b border-white/10 pb-1 hover:text-emerald-400 hover:border-emerald-400 transition-colors">Already have an account? Sign in</Link>
                    </div>
                  </div>
                </form>
              </div>
            </GlassCard>

            {/* Requirements Card */}
            <div className="mt-6 grid grid-cols-3 gap-3 animate-in fade-in duration-1000 delay-500">
              {[
                { label: 'Length', val: '8+ chars' },
                { label: 'Strength', val: 'Mixed case' },
                { label: 'Security', val: 'Encrypted' },
              ].map((req, i) => (
                <div key={i} className="bg-[#131318]/50 backdrop-blur-md border border-white/[0.05] rounded-xl p-3 text-center space-y-1">
                  <p className="text-[8px] font-black text-emerald-500/70 uppercase tracking-wider">{req.label}</p>
                  <p className="text-[10px] font-bold text-white/50 uppercase tracking-widest">{req.val}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
