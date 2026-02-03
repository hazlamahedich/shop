/** Main App component for Shopping Assistant Bot frontend. */

import { PrerequisiteChecklist } from "./onboarding/PrerequisiteChecklist";
import { DeploymentWizard } from "./onboarding/DeploymentWizard";
import { FacebookConnection } from "./onboarding/FacebookConnection";
import { ShopifyConnection } from "./onboarding/ShopifyConnection";
import { LLMConfiguration } from "./onboarding/LLMConfiguration";
import { useIntegrationsStore } from "../stores/integrationsStore";

export function App() {
  const { facebookConnection, shopifyConnection } = useIntegrationsStore();

  return (
    <div className="app min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-slate-900">Shopping Assistant Bot</h1>
          <p className="text-sm text-slate-600">Merchant Onboarding</p>
        </div>
      </header>
      <main className="py-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-8">
          <PrerequisiteChecklist />
          <DeploymentWizard />
          {facebookConnection.connected && (
            <FacebookConnection />
          )}
          {facebookConnection.connected && (
            <ShopifyConnection />
          )}
          {facebookConnection.connected && shopifyConnection.connected && (
            <LLMConfiguration />
          )}
        </div>
      </main>
    </div>
  );
}
