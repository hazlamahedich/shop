import React, { useEffect } from 'react';
import { LayoutDashboard, MessageSquare, DollarSign, Settings, Cpu, Smile, Info, Bot, TestTube, LogOut, Package, ShoppingCart, Users } from 'lucide-react';
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
    icon: React.ComponentType<{ size?: number }>;
    label: string;
    path: string;
    requiresStore?: boolean; // If true, only shown when store is connected
    badgeType?: 'conversations' | 'handoff'; // Which badge to show
  }

  const navItems: NavItem[] = [
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
    { icon: Smile, label: 'Bot Personality', path: '/personality' },
    { icon: Bot, label: 'Bot Config', path: '/bot-config' },
    { icon: Settings, label: 'Settings', path: '/settings' },
    { icon: Cpu, label: 'LLM Settings', path: '/settings/provider' },
  ];

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
    <aside className="w-64 bg-gray-50 border-r border-gray-200 h-screen fixed left-0 top-0 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-primary">Shop</h1>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {visibleNavItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            data-testid={item.path === '/conversations' ? 'nav-conversations' : undefined}
            className={`flex items-center justify-between px-4 py-3 rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-blue-50 text-primary font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-3">
              <item.icon size={20} />
              <span>{item.label}</span>
            </div>
            {item.badgeType === 'conversations' && activeCount > 0 && (
              <span
                data-testid="conversations-active-badge"
                className="bg-blue-500 text-white text-xs font-medium px-2 py-0.5 rounded-full min-w-[20px] text-center"
              >
                {activeCount > 99 ? '99+' : activeCount}
              </span>
            )}
            {item.badgeType === 'handoff' && unreadCount > 0 && (
              <span
                data-testid="handoff-unread-badge"
                className="bg-red-500 text-white text-xs font-medium px-2 py-0.5 rounded-full min-w-[20px] text-center"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </a>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-medium">
              {getUserInitials()}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {merchant?.bot_name || 'Merchant'}
              </p>
              <p className="text-xs text-gray-500">
                {merchant?.email || 'Not logged in'}
              </p>
            </div>
          </div>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
