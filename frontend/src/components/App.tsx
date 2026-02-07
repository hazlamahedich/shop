import { useState, useEffect } from 'react';
import DashboardLayout from './layout/DashboardLayout';
import Dashboard from '../pages/Dashboard';
import Conversations from '../pages/Conversations';
import Costs from '../pages/Costs';
import Settings from '../pages/Settings';
import { ProviderSettings } from '../pages/ProviderSettings';
import Onboarding from '../pages/Onboarding';
import OnboardingSuccess from '../pages/OnboardingSuccess';

export function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };

    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  // Simple routing for demo purposes
  // In a real app we'd use react-router-dom
  const renderPage = () => {
    switch (currentPath) {
      case '/conversations':
        return <Conversations />;
      case '/costs':
        return <Costs />;
      case '/settings':
        return <Settings />;
      case '/settings/provider':
        return <ProviderSettings />;
      case '/onboarding':
        return <Onboarding />;
      case '/onboarding/success':
        return <OnboardingSuccess />;
      case '/dashboard':
      default:
        return <Dashboard />;
    }
  };

  return <DashboardLayout>{renderPage()}</DashboardLayout>;
}
