import React from 'react';
import { Search, Bell, LogOut, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { HelpMenu } from './HelpMenu';

const Header = () => {
  const navigate = useNavigate();
  const { merchant, logout, isAuthenticated } = useAuthStore();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Still navigate to login even if logout API fails
      navigate('/login');
    }
  };

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
        {/* User Info */}
        {isAuthenticated && merchant && (
          <div className="flex items-center space-x-2 text-sm">
            <User size={16} className="text-gray-500" />
            <span className="text-gray-700 font-medium">{merchant.email}</span>
            {merchant.bot_name && (
              <span className="text-gray-500">({merchant.bot_name})</span>
            )}
          </div>
        )}

        {/* Notification Bell */}
        <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-full relative">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* Help Menu */}
        <HelpMenu />

        {/* Logout Button */}
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
