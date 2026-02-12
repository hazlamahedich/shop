/** Main entry point for Shopping Assistant Bot frontend. */

import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './components/App';
import { ToastProvider } from './context/ToastContext';
import { initializeAuth, cleanupAuth, useAuthStore } from './stores/authStore';

import './index.css';

import { BrowserRouter } from 'react-router-dom';

const AuthInitializer: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    // Initialize auth on app mount - checks if user has valid session
    const init = async () => {
      try {
        await initializeAuth();
      } catch (error) {
        console.error('Auth initialization failed:', error);
      } finally {
        setIsInitializing(false);
      }
    };

    init();

    // Cleanup on unmount
    return () => {
      cleanupAuth();
    };
  }, []);

  // Show loading spinner while checking auth
  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return <App />;
};

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <ToastProvider>
        <BrowserRouter>
          <AuthInitializer />
        </BrowserRouter>
      </ToastProvider>
    </React.StrictMode>
  );
}
