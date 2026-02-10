/**
 * Session Expiry Warning Component
 *
 * Story 1.8: Displays warning banner when session is about to expire.
 *
 * Shows at 19 hours (5 minutes before expiry) for 24-hour sessions.
 * Offers to extend session or logout.
 * Auto-logout when session expires.
 *
 * WCAG AA compliant with keyboard navigation and screen reader support.
 */

import { useState, useEffect } from 'react';
import { AlertCircle, LogOut, RefreshCw, X } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { isSessionExpiringSoon, getTimeUntilExpiration } from '../../services/auth';

interface SessionExpiryWarningProps {
  /** Warning threshold in milliseconds (default: 5 minutes) */
  warningThreshold?: number;
  /** Check interval in milliseconds (default: 30 seconds) */
  checkInterval?: number;
}

const SessionExpiryWarning: React.FC<SessionExpiryWarningProps> = ({
  warningThreshold = 5 * 60 * 1000, // 5 minutes
  checkInterval = 30 * 1000, // 30 seconds
}) => {
  const { sessionExpiresAt, refreshSession, logout, isAuthenticated } = useAuthStore();
  const [isVisible, setIsVisible] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || !sessionExpiresAt) {
      setIsVisible(false);
      return;
    }

    // Check if session is expiring soon
    const checkExpiry = () => {
      const timeLeft = getTimeUntilExpiration(sessionExpiresAt);

      // Show warning if less than threshold
      if (timeLeft > 0 && timeLeft < warningThreshold) {
        setIsVisible(true);
        setTimeRemaining(timeLeft);
      } else if (timeLeft === 0) {
        // Session expired - auto logout
        handleAutoLogout();
      } else {
        setIsVisible(false);
      }
    };

    // Check immediately
    checkExpiry();

    // Set up interval to check expiry
    const intervalId = setInterval(checkExpiry, checkInterval);

    return () => clearInterval(intervalId);
  }, [isAuthenticated, sessionExpiresAt, warningThreshold, checkInterval]);

  const handleAutoLogout = async () => {
    setIsVisible(false);
    await logout();
    // Redirect to login will be handled by auth state change
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshSession();
      setIsVisible(false); // Hide warning after successful refresh
    } catch (error) {
      console.error('Failed to refresh session:', error);
      // If refresh fails, user will need to login again
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLogout = async () => {
    setIsVisible(false);
    await logout();
  };

  const handleClose = () => {
    setIsVisible(false);
  };

  // Format remaining time as minutes and seconds
  const formatTimeRemaining = (ms: number): string => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      aria-atomic="true"
      className="fixed top-0 left-0 right-0 z-50 bg-amber-50 border-b border-amber-200 px-4 py-3 shadow-lg"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertCircle
            className="text-amber-600 flex-shrink-0"
            size={20}
            aria-hidden="true"
          />
          <div className="flex flex-col">
            <p className="text-sm font-medium text-amber-800">
              Your session will expire in {formatTimeRemaining(timeRemaining)}
            </p>
            <p className="text-xs text-amber-700">
              Refresh your session to continue working, or you will be logged out automatically.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Refresh session to stay logged in"
          >
            <RefreshCw
              size={16}
              className={`mr-1.5 ${isRefreshing ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
            {isRefreshing ? 'Refreshing...' : 'Refresh Session'}
          </button>

          <button
            type="button"
            onClick={handleLogout}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
            aria-label="Logout now"
          >
            <LogOut size={16} className="mr-1.5" aria-hidden="true" />
            Logout
          </button>

          <button
            type="button"
            onClick={handleClose}
            className="inline-flex items-center p-1.5 text-amber-600 hover:bg-amber-100 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors"
            aria-label="Close warning"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionExpiryWarning;
