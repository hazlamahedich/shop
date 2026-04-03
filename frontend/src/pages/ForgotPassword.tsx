import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';
import { authApi } from '../services/auth';
import { useToast } from '../context/ToastContext';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      toast('Please enter your email address', 'error');
      return;
    }

    setIsLoading(true);

    try {
      await authApi.forgotPassword(email);
      setIsSuccess(true);
      toast('If an account exists with this email, a password reset link has been sent', 'success', 5000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send reset email';
      toast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

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

        {/* Success state */}
        {isSuccess ? (
          <div className="glass-panel rounded-3xl p-10 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="w-20 h-20 rounded-full bg-primary-container/20 flex items-center justify-center mx-auto mb-6 border border-primary-container/30">
              <CheckCircle size={40} className="text-primary-container" />
            </div>
            <h1 className="text-3xl font-bold font-headline text-on-surface mb-3 tracking-tight">
              Check Your Email
            </h1>
            <p className="text-on-surface-variant mb-8 leading-relaxed">
              We've sent a password reset link to <strong>{email}</strong>. The link will expire in 1 hour.
            </p>
            <div className="space-y-4">
              <p className="text-sm text-on-surface-variant">
                Didn't receive the email? Check your spam folder or
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setIsSuccess(false);
                  setEmail('');
                }}
                className="w-full"
              >
                Try Again
              </Button>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="text-center mb-10">
              <div className="w-16 h-16 rounded-2xl bg-primary-container/10 flex items-center justify-center mx-auto mb-6 border border-primary-container/20">
                <Mail size={32} className="text-primary-container" />
              </div>
              <h1 className="text-4xl font-bold font-headline text-on-surface mb-3 tracking-tight">
                Forgot Password?
              </h1>
              <p className="text-on-surface-variant max-w-sm mx-auto leading-relaxed">
                No problem! Enter your email address and we'll send you a link to reset your password.
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="glass-panel rounded-3xl p-10 space-y-6">
              <div>
                <Label htmlFor="email" className="text-sm font-medium text-on-surface mb-2 block">
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-surface-container border-outline-variant text-on-surface placeholder:text-on-surface-variant/50 focus:ring-primary-container/30 focus:border-primary-container"
                  disabled={isLoading}
                />
              </div>

              <Button
                type="submit"
                disabled={isLoading || !email.trim()}
                className="w-full bg-primary-container hover:bg-primary-fixed text-on-primary-container font-semibold h-12"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
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
          </>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
