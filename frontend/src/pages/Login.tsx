/**
 * Login Page
 *
 * Story 1.8: Merchant Dashboard Authentication
 *
 * Displays login form with:
 * - Email input (validated)
 * - Password input (min 8 chars)
 * - Error messages for:
 *   - Invalid credentials
 *   - Rate limiting
 *   - Network errors
 * - Loading state during login
 *
 * AC 1: Login page displays email and password inputs
 * AC 2: Successful login redirects to /dashboard
 * AC 3: Failed login shows clear error "Invalid email or password"
 * AC 7: Rate limiting feedback (5 attempts per 15 minutes)
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { LoginRequest } from '../types/auth';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, error, clearError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Clear any lingering error from the store when Login page mounts
  useEffect(() => {
    clearError();
  }, [clearError]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Navigate to intended destination or dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Clear error when user starts typing
  useEffect(() => {
    if (email || password) {
      clearError();
      setLocalError(null);
    }
  }, [email, password, clearError]);

  // Log when localError changes for debugging
  useEffect(() => {
    if (localError) {
      console.log('Local error set:', localError);
    }
  }, [localError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Basic validation
    if (!email || !password) {
      setLocalError('Please enter both email and password');
      return;
    }

    if (!email.includes('@')) {
      setLocalError('Please enter a valid email address');
      return;
    }

    if (password.length < 8) {
      setLocalError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    setLocalError(null);

    try {
      const credentials: LoginRequest = { email, password };
      await login(credentials);

      // Navigate to intended destination on successful login
      // Priority order (MEDIUM-10: standardized):
      // 1. location.state.from.pathname - React Router state from ProtectedRoute (most recent)
      // 2. sessionStorage.getItem('intendedDestination') - Fallback from ProtectedRoute (persists across reload)
      // 3. '/dashboard' - Default destination
      const from = (location.state as any)?.from?.pathname
        || sessionStorage.getItem('intendedDestination')
        || '/dashboard';

      // Clear the intended destination from sessionStorage after use
      sessionStorage.removeItem('intendedDestination');

      navigate(from, { replace: true });
    } catch (err) {
      // Error is already set in store, but we can show local feedback too
      const errorMessage = err instanceof Error ? err.message : 'Login failed';

      // Check for rate limiting error
      if ((err as any).code === 2011) {
        setLocalError('Too many login attempts. Please try again later.');
      } else {
        setLocalError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Listen for logout events from other tabs via BroadcastChannel
  useEffect(() => {
    const channel = new BroadcastChannel('auth-channel');

    channel.addEventListener('message', (event) => {
      if (event.data.type === 'LOGOUT') {
        // Already on login page, just ensure we're logged out
        clearError();
        setLocalError(null);
      }
    });

    return () => {
      channel.close();
    };
  }, [clearError]);

  const getErrorMessage = () => {
    // Prioritize local error over store error
    if (localError) return localError;
    if (error) return error;
    return null;
  };

  const errorMessage = getErrorMessage();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <h1 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Merchant Dashboard Login
          </h1>
          <p className="mt-2 text-center text-sm text-gray-600">
            Shopping Assistant Bot Dashboard
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            {/* Email Input */}
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value.trim())}
                disabled={isLoading}
              />
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value.trim())}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Error Message */}
          {errorMessage && (
            <div className="rounded-md bg-red-50 p-4" role="alert">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {errorMessage}
                  </h3>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </div>

          {/* Help Text */}
          <div className="text-center text-sm text-gray-600">
            <p>Forgot your password? Contact your administrator.</p>
          </div>
        </form>

        {/* Rate Limit Notice */}
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Security Notice
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  For your security, login attempts are limited to 5 attempts per
                  15 minutes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
