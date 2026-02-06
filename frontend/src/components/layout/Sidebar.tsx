import React from 'react';
import { LayoutDashboard, MessageSquare, DollarSign, Settings } from 'lucide-react';

const Sidebar = () => {
  // Placeholder for navigation logic until routing is fully set up
  const isActive = (path: string) => path === '/dashboard';

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: MessageSquare, label: 'Conversations', path: '/conversations' },
    { icon: DollarSign, label: 'Costs', path: '/costs' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 h-screen fixed left-0 top-0 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-primary">Shop</h1>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              isActive(item.path)
                ? 'bg-blue-50 text-primary font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </a>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-medium">
            MA
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Merchant Admin</p>
            <p className="text-xs text-gray-500">admin@shop.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
