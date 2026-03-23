import React, { useState, useRef, useEffect } from 'react';
import { Bell, LogOut, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useHandoffAlertsStore } from '../../stores/handoffAlertStore';
import { HelpMenu } from './HelpMenu';
import { GlobalSearch } from './GlobalSearch';

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
    <header className="bg-[#030303]/80 backdrop-blur-xl border-b border-emerald-500/10 h-16 flex items-center justify-between px-8 pl-72 fixed top-0 right-0 w-full z-40 transition-all duration-300">
      <GlobalSearch />

      <div className="flex items-center space-x-6">
        {isAuthenticated && merchant && (
          <div className="hidden lg:flex items-center space-x-2 text-sm">
            <User size={16} className="text-emerald-500/70" />
            <span className="text-slate-100 font-medium">{merchant.email}</span>
            {merchant.bot_name && (
              <span className="text-slate-500">({merchant.bot_name})</span>
            )}
          </div>
        )}

        <div className="relative" ref={dropdownRef}>
          <button
            data-testid="notification-bell"
            aria-label="Notifications"
            role="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={`p-2 rounded-full relative transition-all duration-200 ${
              isDropdownOpen ? 'bg-emerald-500/10 text-emerald-400' : 'text-slate-400 hover:bg-emerald-500/5 hover:text-emerald-300'
            }`}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <span
                data-testid="notification-badge"
                className="absolute -top-0.5 -right-0.5 bg-emerald-500 text-black text-[10px] font-bold w-5 h-5 flex items-center justify-center rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </button>

          {isDropdownOpen && (
            <div
              data-testid="notification-dropdown"
              className="absolute right-0 mt-3 w-80 glass-card shadow-2xl z-50 overflow-hidden border-emerald-500/20"
            >
              <div className="flex items-center justify-between px-4 py-3 border-b border-emerald-500/10 bg-emerald-500/5">
                <h3 className="font-semibold text-slate-100">Handoff Alerts</h3>
                {unreadCount > 0 && (
                  <button
                    data-testid="mark-all-read"
                    onClick={handleMarkAllRead}
                    className="text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div data-testid="handoff-alerts-list" className="max-h-96 overflow-y-auto custom-scrollbar">
                {recentAlerts.length === 0 ? (
                  <div className="px-4 py-8 text-center text-slate-500 italic">
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
                        className={`px-4 py-4 border-b border-emerald-500/5 cursor-pointer transition-colors ${
                          !alert.isRead ? 'bg-emerald-500/5 hover:bg-emerald-500/10' : 'hover:bg-white/5'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <div className="flex items-center space-x-2">
                            <span data-testid="urgency-indicator" data-urgency={alert.urgencyLevel} aria-label={style.label}>
                              {style.emoji}
                            </span>
                            <span data-testid="alert-customer-name" className="font-medium text-slate-100 text-sm">
                              {alert.customerName || `Customer #${alert.customerId}`}
                            </span>
                          </div>
                          <span data-testid="alert-wait-time" className="text-[10px] font-mono text-slate-500">
                            {formatWaitTime(alert.waitTimeSeconds)}
                          </span>
                        </div>
                        <p data-testid="alert-preview" className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {alert.conversationPreview}
                        </p>
                      </div>
                    );
                  })
                )}
              </div>

              {alerts.length > 5 && (
                <div className="px-4 py-3 border-t border-emerald-500/10">
                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      navigate('/conversations?hasHandoff=true');
                    }}
                    className="w-full text-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
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
            className="flex items-center space-x-2 px-3 py-2 text-slate-400 hover:bg-emerald-500/10 hover:text-emerald-400 rounded-lg transition-all duration-200"
            title="Logout"
          >
            <LogOut size={18} />
            <span className="hidden sm:inline text-sm font-semibold">Logout</span>
          </button>
        )}
      </div>
    </header>
  );
};

export default Header;
