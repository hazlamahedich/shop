import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import DashboardLayout from './layout/DashboardLayout';
import Dashboard from '../pages/Dashboard';
import Conversations from '../pages/Conversations';
import Costs from '../pages/Costs';
import Settings from '../pages/Settings';
import { ProviderSettings } from '../pages/ProviderSettings';
import PersonalityConfig from '../pages/PersonalityConfig';
import Onboarding from '../pages/Onboarding';
import OnboardingSuccess from '../pages/OnboardingSuccess';
import BusinessInfoFaqConfig from '../pages/BusinessInfoFaqConfig';
import BotConfig from '../pages/BotConfig';
import { BotPreview } from '../pages/BotPreview';
import Login from '../pages/Login';

const DashboardLayoutWrapper = () => (
  <DashboardLayout>
    <Outlet />
  </DashboardLayout>
);

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<DashboardLayoutWrapper />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/costs" element={<Costs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/settings/provider" element={<ProviderSettings />} />
        <Route path="/personality" element={<PersonalityConfig />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/onboarding/success" element={<OnboardingSuccess />} />
        <Route path="/business-info-faq" element={<BusinessInfoFaqConfig />} />
        <Route path="/bot-config" element={<BotConfig />} />
        <Route path="/bot-preview" element={<BotPreview />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
