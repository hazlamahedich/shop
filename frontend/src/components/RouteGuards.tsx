/** Route Guard Components.

Protects routes based on onboarding and authentication status.
Ensures merchants complete onboarding before accessing main dashboard.

Sprint Change 2026-02-13: Added StoreRequiredGuard for optional e-commerce integration
*/

import * as React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { useTutorialStore } from '../stores/tutorialStore';
import { useHasStoreConnected } from '../stores/authStore';
import { TutorialPrompt } from './onboarding/TutorialPrompt';

export interface RouteGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  isAuthenticated?: boolean;
}

/**
 * Onboarding Route Guard
 * Redirects unauthenticated users and ensures onboarding completion.
 */
export function OnboardingGuard({ children, requireAuth = true, isAuthenticated = false }: RouteGuardProps) {
  const location = useLocation();
  const { isFullyOnboarded, currentPhase } = useOnboardingPhaseStore();
  const { isStarted, isCompleted, isSkipped } = useTutorialStore();

  // Debug logging
  console.log('[OnboardingGuard]', {
    pathname: location.pathname,
    isFullyOnboarded,
    currentPhase,
    isStarted,
    isCompleted,
    isSkipped,
  });

  // Allow public routes
  if (location.pathname.startsWith('/onboarding/') || location.pathname === '/') {
    return <>{children}</>;
  }

  // Require authentication for protected routes
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  // Bot config routes require auth but are part of onboarding
  if (location.pathname.startsWith('/bot-config')) {
    if (requireAuth && !isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
  }

  // Dashboard requires full onboarding
  if (location.pathname.startsWith('/dashboard')) {
    if (requireAuth && !isAuthenticated) {
      return <Navigate to="/login" replace />;
    }

    // If not fully onboarded, handle tutorial flow
    if (!isFullyOnboarded) {
      // If tutorial is in progress, show the dashboard with the tutorial overlay
      if (isStarted) {
        return <>{children}</>;
      }
      // If tutorial not completed/skipped, show tutorial prompt
      if (!isCompleted && !isSkipped) {
        return <TutorialPrompt />;
      }
      // Redirect to bot config for setup completion
      return <Navigate to="/bot-config" replace />;
    }
  }

  return <>{children}</>;
}

/**
 * Authentication Guard
 * Redirects authenticated users away from auth pages.
 */
export function AuthGuard({ children, isAuthenticated = false }: RouteGuardProps) {
  const location = useLocation();

  // If already authenticated, redirect to dashboard or onboarding
  if (isAuthenticated) {
    const { isFullyOnboarded } = useOnboardingPhaseStore.getState();
    if (isFullyOnboarded) {
      return <Navigate to="/dashboard" replace />;
    }
    return <Navigate to="/bot-config" replace />;
  }

  return <>{children}</>;
}

/**
 * Store Required Guard
 * Sprint Change 2026-02-13: Make Shopify Optional Integration
 *
 * Protects routes that require an e-commerce store connection.
 * Redirects to /bot-config (store connection settings) if no store is connected.
 *
 * Use this guard for routes like /products, /orders, /inventory that require
 * e-commerce functionality.
 */
export interface StoreGuardProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export function StoreRequiredGuard({ children, redirectTo = '/bot-config' }: StoreGuardProps) {
  const location = useLocation();
  const hasStoreConnected = useHasStoreConnected();

  if (!hasStoreConnected) {
    // Redirect to store connection page with return URL
    return (
      <Navigate
        to={redirectTo}
        replace
        state={{ from: location.pathname, requiresStore: true }}
      />
    );
  }

  return <>{children}</>;
}
