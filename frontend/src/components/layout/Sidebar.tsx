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

  // Navigation items
  interface NavItem {
    icon: React.ElementType;
    label: string;
    path: string;
    requiresStore?: boolean;
    badgeType?: 'conversations' | 'handoff';
  }

  const baseNavItems: NavItem[] = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: TestTube, label: 'Test Your Bot', path: '/bot-preview' },
    { icon: MessageSquare, label: 'Conversations', path: '/conversations', badgeType: 'conversations' },
    { icon: Users, label: 'Handoff Queue', path: '/handoff-queue', badgeType: 'handoff' },
    { icon: DollarSign, label: 'Costs', path: '/costs' },
    { icon: Info, label: 'Business Info & FAQ', path: '/business-info-faq' },
  ];

  if (merchant?.onboardingMode === 'general') {
    baseNavItems.push({ icon: BookOpen, label: 'Knowledge Base', path: '/knowledge-base' });
  }

  baseNavItems.push(
    { icon: Smile, label: 'Bot Personality', path: '/personality' },
    { icon: Bot, label: 'Bot Config', path: '/bot-config' },
    { icon: Settings, label: 'Settings', path: '/settings' },
    { icon: Cpu, label: 'LLM Settings', path: '/settings/provider' }
  );

  const navItems = baseNavItems;
  const visibleNavItems = navItems.filter((item) =>
    item.requiresStore ? hasStoreConnected : true
  );

  const getUserInitials = () => {
    if (!merchant?.email) return 'MA';
    const email = merchant.email;
    const name = email.split('@')[0];
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <aside className="w-64 glass-card h-screen fixed left-0 top-0 flex flex-col z-50 rounded-none border-y-0 border-l-0 shadow-[20px_0_40px_rgba(0,0,0,0.3)]">
      <div className="p-8 mb-4">
        <div className="text-3xl font-black bg-gradient-to-r from-[#00f5d4] to-[#00d1b2] bg-clip-text text-transparent mantis-glow-text tracking-tighter">
          MANTIS
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto custom-scrollbar">
        {visibleNavItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            data-testid={item.path === '/conversations' ? 'nav-conversations' : undefined}
            className={`flex items-center justify-between px-4 py-2.5 rounded-xl transition-all duration-300 group ${
              isActive(item.path)
                ? 'bg-[#00f5d4]/10 text-[#00f5d4] border border-[#00f5d4]/20 shadow-[0_0_20px_rgba(0,245,212,0.1)] glow-active'
                : 'text-white/40 hover:bg-white/5 hover:text-[#00f5d4]/80'
            }`}
          >
            <div className="flex items-center space-x-3">
              <item.icon size={18} className={isActive(item.path) ? 'text-[#00f5d4]' : 'group-hover:text-[#00f5d4] transition-colors'} />
              <span className="text-xs font-bold uppercase tracking-widest">{item.label}</span>
            </div>
            {item.badgeType === 'conversations' && activeCount > 0 && (
              <span
                data-testid="conversations-active-badge"
                className="bg-[#00f5d4] text-black text-[9px] font-black px-1.5 py-0.5 rounded-md min-w-[18px] text-center shadow-[0_0_10px_rgba(0,245,212,0.4)]"
              >
                {activeCount > 99 ? '99+' : activeCount}
              </span>
            )}
            {item.badgeType === 'handoff' && unreadCount > 0 && (
              <span
                data-testid="handoff-unread-badge"
                className="bg-red-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded-md min-w-[18px] text-center shadow-[0_0_10px_rgba(239,68,68,0.3)]"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </a>
        ))}
      </nav>

      <div className="p-6 border-t border-white/5">
        <div className="flex items-center justify-between group cursor-pointer p-2 rounded-2xl hover:bg-white/5 transition-colors">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="w-9 h-9 flex-shrink-0 rounded-xl bg-gradient-to-br from-[#00f5d4] to-[#00d1b2] flex items-center justify-center font-black text-black text-xs shadow-[0_0_15px_rgba(0,245,212,0.3)]">
              {getUserInitials()}
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-black text-white truncate uppercase tracking-tight">
                {merchant?.bot_name || 'Merchant'}
              </p>
              <p className="text-[9px] font-bold text-white/30 truncate tracking-tight">
                {merchant?.email || 'Not logged in'}
              </p>
            </div>
          </div>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="p-2 text-white/20 hover:text-red-400 rounded-lg transition-all duration-200"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
