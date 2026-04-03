import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import DashboardLayout from './layout/DashboardLayout';
import Dashboard from '../pages/Dashboard';
import Conversations from '../pages/Conversations';
import HandoffQueue from '../pages/HandoffQueue';
import ConversationHistory from '../pages/ConversationHistory';
import Costs from '../pages/Costs';
import Settings from '../pages/Settings';
import WidgetSettings from '../pages/WidgetSettings';
import { ProviderSettings } from '../pages/ProviderSettings';
import { EmbeddingSettings } from './settings/EmbeddingSettings';
import ShippingCarriers from '../pages/ShippingCarriers';
import PersonalityConfig from '../pages/PersonalityConfig';
import Onboarding from '../pages/Onboarding';
import OnboardingSuccess from '../pages/OnboardingSuccess';
import BusinessInfoFaqConfig from '../pages/BusinessInfoFaqConfig';
import BotConfig from '../pages/BotConfig';
import { BotPreview } from '../pages/BotPreview';
import Login from '../pages/Login';
import Register from '../pages/Register';
import ForgotPassword from '../pages/ForgotPassword';
import ResetPassword from '../pages/ResetPassword';
import WidgetTestPage from '../pages/WidgetTestPage';
import AuditLogs from '../pages/AuditLogs';
import KnowledgeBasePage from '../pages/KnowledgeBasePage';
import { WidgetDemo } from '../widget/demo/WidgetDemo';
import { GeneralModeDemo } from '../pages/GeneralModeDemo';
import { OnboardingGuard, AuthGuard } from './RouteGuards';
import { useAuthStore } from '../stores/authStore';

const DashboardLayoutWrapper = () => (
  <DashboardLayout>
    <Outlet />
  </DashboardLayout>
);

export function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <Routes>
      {/* Public routes - no auth required */}
      <Route path="/widget-test" element={<WidgetTestPage />} />
      <Route path="/widget-demo" element={<WidgetDemo />} />
      <Route path="/general-mode-demo" element={<GeneralModeDemo />} />

      {/* Auth-wrapped login route - redirects to dashboard if already logged in */}
      <Route
        path="/login"
        element={
          <AuthGuard isAuthenticated={isAuthenticated}>
            <Login />
          </AuthGuard>
        }
      />

      {/* Registration route - no auth required */}
      <Route
        path="/register"
        element={
          <AuthGuard isAuthenticated={isAuthenticated}>
            <Register />
          </AuthGuard>
        }
      />

      {/* Password reset routes - no auth required */}
      <Route
        path="/forgot-password"
        element={
          <AuthGuard isAuthenticated={isAuthenticated}>
            <ForgotPassword />
          </AuthGuard>
        }
      />
      <Route
        path="/reset-password/:token"
        element={
          <AuthGuard isAuthenticated={isAuthenticated}>
            <ResetPassword />
          </AuthGuard>
        }
      />

      {/* Protected routes with onboarding guard */}
      <Route
        element={
          <OnboardingGuard isAuthenticated={isAuthenticated}>
            <DashboardLayoutWrapper />
          </OnboardingGuard>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/conversations/:conversationId/history" element={<ConversationHistory />} />
        <Route path="/handoff-queue" element={<HandoffQueue />} />
        <Route path="/costs" element={<Costs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/settings/widget" element={<WidgetSettings />} />
        <Route path="/settings/provider" element={<ProviderSettings />} />
        <Route path="/settings/shipping" element={<ShippingCarriers />} />
        <Route path="/settings/embedding" element={<EmbeddingSettings />} />
        <Route path="/personality" element={<PersonalityConfig />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/onboarding/success" element={<OnboardingSuccess />} />
        <Route path="/business-info-faq" element={<BusinessInfoFaqConfig />} />
        <Route path="/bot-config" element={<BotConfig />} />
        <Route path="/bot-preview" element={<BotPreview />} />
        <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
        <Route path="/dashboard/audit-logs" element={<AuditLogs />} />
      </Route>

      {/* Wildcard redirects to dashboard (will be guarded by OnboardingGuard) */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
