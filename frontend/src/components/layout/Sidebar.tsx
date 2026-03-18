import React, { useEffect } from 'react';
import { LayoutDashboard, MessageSquare, DollarSign, Settings, Cpu, Smile, Info, Bot, TestTube, LogOut, Users, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore, useHasStoreConnected } from '../../stores/authStore';
import { useHandoffAlertsStore } from '../../stores/handoffAlertStore';
import { useConversationStore } from '../../stores/conversationStore';

const Sidebar = () => {
  const navigate = useNavigate();
  const { merchant, logout, isAuthenticated } = useAuthStore();
  const hasStoreConnected = useHasStoreConnected();
  const { unreadCount, startPolling: startHandoffPolling, stopPolling: stopHandoffPolling } = useHandoffAlertsStore();
  const { activeCount, startActiveCountPolling, stopActiveCountPolling } = useConversationStore();

  // Start polling for unread count on mount
  useEffect(() => {
    startHandoffPolling(30000); // Poll every 30 seconds
    startActiveCountPolling(30000); // Poll every 30 seconds
    return () => {
      stopHandoffPolling();
      stopActiveCountPolling();
    };
  }, [startHandoffPolling, stopHandoffPolling, startActiveCountPolling, stopActiveCountPolling]);

  const isActive = (path: string) => {
    return window.location.pathname === path;
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      navigate('/login');
    }
  };

  // Navigation items - Sprint Change 2026-02-13: Support store-dependent items
  interface NavItem {
    icon: React.ElementType;
    label: string;
    path: string;
    requiresStore?: boolean; // If true, only shown when store is connected
    badgeType?: 'conversations' | 'handoff'; // Which badge to show
  }

  // Build nav items array based on mode
  const baseNavItems: NavItem[] = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: TestTube, label: 'Test Your Bot', path: '/bot-preview' },
    { icon: MessageSquare, label: 'Conversations', path: '/conversations', badgeType: 'conversations' },
    { icon: Users, label: 'Handoff Queue', path: '/handoff-queue', badgeType: 'handoff' },
    { icon: DollarSign, label: 'Costs', path: '/costs' },
    // Sprint Change 2026-02-13: Store-dependent navigation items
    // Uncomment when Products and Orders pages are implemented:
    // { icon: Package, label: 'Products', path: '/products', requiresStore: true },
    // { icon: ShoppingCart, label: 'Orders', path: '/orders', requiresStore: true },
    { icon: Info, label: 'Business Info & FAQ', path: '/business-info-faq' },
  ];

  // Story 8-8: Add Knowledge Base only in General mode
  if (merchant?.onboardingMode === 'general') {
    baseNavItems.push({ icon: BookOpen, label: 'Knowledge Base', path: '/knowledge-base' });
  }

  // Add remaining items
  baseNavItems.push(
    { icon: Smile, label: 'Bot Personality', path: '/personality' },
    { icon: Bot, label: 'Bot Config', path: '/bot-config' },
    { icon: Settings, label: 'Settings', path: '/settings' },
    { icon: Cpu, label: 'LLM Settings', path: '/settings/provider' }
  );

  const navItems = baseNavItems;

  // Filter nav items based on store connection
  const visibleNavItems = navItems.filter((item) =>
    item.requiresStore ? hasStoreConnected : true
  );

  // Get user initials for avatar
  const getUserInitials = () => {
    if (!merchant?.email) return 'MA';
    const email = merchant.email;
    const name = email.split('@')[0];
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <aside className="w-64 glass-card h-screen fixed left-0 top-0 flex flex-col z-50 rounded-none border-y-0 border-l-0">
      <div className="p-8 mb-4">
        <div className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-green-500 bg-clip-text text-transparent mantis-glow-text">
          Mantis
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2 overflow-y-auto custom-scrollbar">
        {visibleNavItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            data-testid={item.path === '/conversations' ? 'nav-conversations' : undefined}
            className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 group ${
              isActive(item.path)
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-[0_0_20px_rgba(16,185,129,0.15)] glow-active'
                : 'text-white/50 hover:bg-emerald-500/5 hover:text-emerald-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              <item.icon size={20} className={isActive(item.path) ? 'text-emerald-400' : 'group-hover:text-emerald-400 transition-colors'} />
              <span className="font-medium">{item.label}</span>
            </div>
            {item.badgeType === 'conversations' && activeCount > 0 && (
              <span
                data-testid="conversations-active-badge"
                className="bg-emerald-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center shadow-[0_0_10px_rgba(16,185,129,0.5)]"
              >
                {activeCount > 99 ? '99+' : activeCount}
              </span>
            )}
            {item.badgeType === 'handoff' && unreadCount > 0 && (
              <span
                data-testid="handoff-unread-badge"
                className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full min-w-[20px] text-center shadow-[0_0_10px_rgba(239,68,68,0.3)]"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </a>
        ))}
      </nav>

      <div className="p-6 border-t border-emerald-500/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center font-bold text-black shadow-[0_0_15px_rgba(16,185,129,0.3)]">
              {getUserInitials()}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-slate-100 truncate">
                {merchant?.bot_name || 'Merchant'}
              </p>
              <p className="text-[10px] font-black text-emerald-500/40 uppercase tracking-widest truncate">
                {merchant?.email || 'Not logged in'}
              </p>
            </div>
          </div>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="p-2 text-slate-500 hover:bg-emerald-500/10 hover:text-emerald-400 rounded-lg transition-all duration-200"
              title="Logout"
            >
              <LogOut size={18} className="text-emerald-500/40" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
