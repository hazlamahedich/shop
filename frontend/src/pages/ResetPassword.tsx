import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Lock, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { authApi } from '../services/auth';
import { useToast } from '../context/ToastContext';

const ResetPassword = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isTokenValid, setIsTokenValid] = useState<boolean | null>(null);
  const [email, setEmail] = useState<string>('');

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setIsTokenValid(false);
        return;
      }

      try {
        const response = await authApi.verifyResetToken(token);
        setIsTokenValid(response.valid);
        setEmail(response.email || '');
      } catch (error) {
        setIsTokenValid(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!password || !confirmPassword) {
      toast('Please fill in all fields', 'error');
      return;
    }

    if (password.length < 8) {
      toast('Password must be at least 8 characters', 'error');
      return;
    }

    if (password !== confirmPassword) {
      toast('Passwords do not match', 'error');
      return;
    }

    if (!token) {
      toast('Invalid reset token', 'error');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.resetPassword(token, password);
      setIsSuccess(true);
      toast('Password has been reset successfully', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reset password';
      toast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state while verifying token
  if (isTokenValid === null) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/20 via-transparent to-primary-container/10" />
        <div className="glass-panel rounded-3xl p-10 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-container mx-auto mb-4" />
          <p className="text-on-surface-variant">Verifying reset link...</p>
        </div>
      </div>
    );
  }

  // Show error if token is invalid
  if (isTokenValid === false) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/20 via-transparent to-primary-container/10" />
        <div className="glass-panel rounded-3xl p-10 text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-error-container/20 flex items-center justify-center mx-auto mb-6 border border-error/30">
            <AlertCircle size={40} className="text-error" />
          </div>
          <h1 className="text-3xl font-bold font-headline text-on-surface mb-3 tracking-tight">
            Invalid or Expired Link
          </h1>
          <p className="text-on-surface-variant mb-8 leading-relaxed">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
          <div className="space-y-3">
            <Link to="/forgot-password">
              <Button className="w-full">Request New Reset Link</Button>
            </Link>
            <Link to="/login" className="block">
              <Button variant="outline" className="w-full">Back to Login</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Show success state
  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/20 via-transparent to-primary-container/10" />
        <div className="glass-panel rounded-3xl p-10 text-center max-w-md animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="w-20 h-20 rounded-full bg-primary-container/20 flex items-center justify-center mx-auto mb-6 border border-primary-container/30">
            <CheckCircle size={40} className="text-primary-container" />
          </div>
          <h1 className="text-3xl font-bold font-headline text-on-surface mb-3 tracking-tight">
            Password Reset Successful
          </h1>
          <p className="text-on-surface-variant mb-8 leading-relaxed">
            Your password has been reset successfully. You can now log in with your new password.
          </p>
          <Link to="/login">
            <Button className="w-full">Continue to Login</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Show reset form
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary-fixed/20 via-transparent to-primary-container/10" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-container/30 rounded-full blur-[128px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary-fixed/20 rounded-full blur-[128px]" />

      <div className="w-full max-w-md relative z-10">
        {/* Back button */}
        <Link
          to="/login"
          className="inline-flex items-center gap-2 text-on-surface-variant hover:text-primary-container transition-colors mb-8 group"
        >
          <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Login</span>
        </Link>

        {/* Header */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 rounded-2xl bg-primary-container/10 flex items-center justify-center mx-auto mb-6 border border-primary-container/20">
            <Lock size={32} className="text-primary-container" />
          </div>
          <h1 className="text-4xl font-bold font-headline text-on-surface mb-3 tracking-tight">
            Reset Password
          </h1>
          <p className="text-on-surface-variant max-w-sm mx-auto leading-relaxed">
            {email && `Resetting password for ${email}`}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="glass-panel rounded-3xl p-10 space-y-6">
          <div>
            <Label htmlFor="password" className="text-sm font-medium text-on-surface mb-2 block">
              New Password
            </Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter new password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="bg-surface-container border-outline-variant text-on-surface placeholder:text-on-surface-variant/50 focus:ring-primary-container/30 focus:border-primary-container pr-10"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <p className="text-xs text-on-surface-variant mt-2">Must be at least 8 characters</p>
          </div>

          <div>
            <Label htmlFor="confirmPassword" className="text-sm font-medium text-on-surface mb-2 block">
              Confirm New Password
            </Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
                className="bg-surface-container border-outline-variant text-on-surface placeholder:text-on-surface-variant/50 focus:ring-primary-container/30 focus:border-primary-container pr-10"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
              >
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            disabled={isLoading || !password || !confirmPassword || password.length < 8 || password !== confirmPassword}
            className="w-full bg-primary-container hover:bg-primary-fixed text-on-primary-container font-semibold h-12"
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </Button>

          <div className="text-center pt-4 border-t border-outline-variant/30">
            <p className="text-sm text-on-surface-variant">
              Remember your password?{' '}
              <Link to="/login" className="text-primary-container hover:text-primary-fixed font-semibold transition-colors">
                Sign In
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
