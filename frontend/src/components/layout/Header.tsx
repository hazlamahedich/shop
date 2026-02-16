import React, { useState, useRef, useEffect } from 'react';
import { Search, Bell, LogOut, User, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useHandoffAlertsStore } from '../../stores/handoffAlertStore';
import { HelpMenu } from './HelpMenu';

const URGENCY_STYLES = {
  high: { emoji: '🔴', label: 'High Priority', bg: 'bg-red-50', border: 'border-red-200' },
  medium: { emoji: '🟡', label: 'Medium Priority', bg: 'bg-yellow-50', border: 'border-yellow-200' },
  low: { emoji: '🟢', label: 'Low Priority', bg: 'bg-green-50', border: 'border-green-200' },
};

const formatWaitTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
};

const Header = () => {
  const navigate = useNavigate();
  const { merchant, logout, isAuthenticated } = useAuthStore();
  const { alerts, unreadCount, fetchAlerts, markAsRead, markAllAsRead } = useHandoffAlertsStore();
  
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchAlerts();
    }
  }, [isAuthenticated, fetchAlerts]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      navigate('/login');
    }
  };

  const handleMarkAllRead = async () => {
    await markAllAsRead();
  };

  const handleAlertClick = async (alertId: number, conversationId: number) => {
    await markAsRead(alertId);
    setIsDropdownOpen(false);
    navigate(`/conversations/${conversationId}`);
  };

  const recentAlerts = alerts.slice(0, 5);

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8 pl-72 fixed top-0 right-0 w-full z-10">
      <div className="flex items-center w-full max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {isAuthenticated && merchant && (
          <div className="flex items-center space-x-2 text-sm">
            <User size={16} className="text-gray-500" />
            <span className="text-gray-700 font-medium">{merchant.email}</span>
            {merchant.bot_name && (
              <span className="text-gray-500">({merchant.bot_name})</span>
            )}
          </div>
        )}

        <div className="relative" ref={dropdownRef}>
          <button
            data-testid="notification-bell"
            aria-label="Notifications"
            role="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="p-2 text-gray-500 hover:bg-gray-100 rounded-full relative"
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span
                data-testid="notification-badge"
                className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs font-medium w-5 h-5 flex items-center justify-center rounded-full"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {isDropdownOpen && (
            <div
              data-testid="notification-dropdown"
              className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
            >
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">Handoff Alerts</h3>
                {unreadCount > 0 && (
                  <button
                    data-testid="mark-all-read"
                    onClick={handleMarkAllRead}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div data-testid="handoff-alerts-list" className="max-h-96 overflow-y-auto">
                {recentAlerts.length === 0 ? (
                  <div className="px-4 py-8 text-center text-gray-500">
                    No handoff alerts
                  </div>
                ) : (
                  recentAlerts.map((alert) => {
                    const style = URGENCY_STYLES[alert.urgencyLevel as keyof typeof URGENCY_STYLES] || URGENCY_STYLES.low;
                    return (
                      <div
                        key={alert.id}
                        data-testid="handoff-alert-item"
                        data-is-read={alert.isRead}
                        data-urgency={alert.urgencyLevel}
                        onClick={() => handleAlertClick(alert.id, alert.conversationId)}
                        className={`px-4 py-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                          !alert.isRead ? 'bg-blue-50/50' : ''
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2">
                            <span data-testid="urgency-indicator" data-urgency={alert.urgencyLevel} aria-label={style.label}>
                              {style.emoji}
                            </span>
                            <span data-testid="alert-customer-name" className="font-medium text-gray-900 text-sm">
                              {alert.customerName || `Customer #${alert.customerId}`}
                            </span>
                          </div>
                          <span data-testid="alert-wait-time" className="text-xs text-gray-500">
                            {formatWaitTime(alert.waitTimeSeconds)}
                          </span>
                        </div>
                        <p data-testid="alert-preview" className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {alert.conversationPreview}
                        </p>
                      </div>
                    );
                  })
                )}
              </div>

              {alerts.length > 5 && (
                <div className="px-4 py-3 border-t border-gray-200">
                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      navigate('/conversations?hasHandoff=true');
                    }}
                    className="w-full text-center text-sm text-blue-600 hover:text-blue-800"
                  >
                    View all alerts ({alerts.length})
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <HelpMenu />

        {isAuthenticated && (
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut size={18} />
            <span className="hidden sm:inline text-sm font-medium">Logout</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
