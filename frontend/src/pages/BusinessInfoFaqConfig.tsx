/**
 * BusinessInfoFaqConfig Page Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Main page for configuring business information and FAQ items.
 * Integrates BusinessInfoForm and FaqList components with:
 * - Save Configuration button for business info
 * - Automatic persistence for FAQ operations
 * - Loading states and error handling
 * - Navigation breadcrumbs
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { useEffect } from 'react';
import { Info, CheckCircle2, AlertCircle } from 'lucide-react';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { BusinessInfoForm } from '../components/business-info/BusinessInfoForm';
import { FaqList } from '../components/business-info/FaqList';

/**
 * BusinessInfoFaqConfig Component
 *
 * Main configuration page for business information and FAQ items.
 *
 * Features:
 * - Business information form with save functionality
 * - FAQ list with add/edit/delete operations
 * - Automatic loading of existing configuration
 * - Success and error notifications
 */
export const BusinessInfoFaqConfig: React.FC = () => {
  const {
    businessName,
    businessDescription,
    businessHours,
    loadingState,
    faqsLoadingState,
    error,
    isDirty,
    fetchBusinessInfo,
    updateBusinessInfo,
    clearError,
  } = useBusinessInfoStore();

  // Success notification state
  const [showSuccess, setShowSuccess] = React.useState(false);
  const [successTimeout, setSuccessTimeout] = React.useState<NodeJS.Timeout | null>(null);

  // Load configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        await Promise.all([
          fetchBusinessInfo(),
          // FAQs are loaded by FaqList component
        ]);
      } catch (err) {
        console.error('Failed to load configuration:', err);
      }
    };

    loadConfig();
  }, [fetchBusinessInfo]);

  // Clear success timeout on unmount
  useEffect(() => {
    return () => {
      if (successTimeout) {
        clearTimeout(successTimeout);
      }
    };
  }, [successTimeout]);

  // Handle save business info
  const handleSaveBusinessInfo = async () => {
    clearError();

    try {
      await updateBusinessInfo({
        business_name: businessName,
        business_description: businessDescription,
        business_hours: businessHours,
      });

      // Show success notification
      setShowSuccess(true);
      if (successTimeout) {
        clearTimeout(successTimeout);
      }
      const timeout = setTimeout(() => {
        setShowSuccess(false);
      }, 3000);
      setSuccessTimeout(timeout);
    } catch (err) {
      console.error('Failed to save business info:', err);
    }
  };

  // Is any operation in progress?
  const isLoading = loadingState === 'loading' || faqsLoadingState === 'loading';
  const hasConfig = businessName || businessDescription || businessHours;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb Navigation */}
      <nav className="bg-white border-b border-gray-200" aria-label="Breadcrumb">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <ol className="flex items-center gap-2 text-sm">
            <li>
              <a
                href="/dashboard"
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                Dashboard
              </a>
            </li>
            <li className="text-gray-400">/</li>
            <li>
              <span className="font-medium text-gray-900">Business Info & FAQ</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Success Notification */}
      {showSuccess && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right">
          <div
            role="alert"
            className="flex items-center gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-lg shadow-lg"
          >
            <CheckCircle2 size={20} className="text-green-600 flex-shrink-0" />
            <p className="text-sm font-medium text-green-800">
              Business info saved successfully!
            </p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Business Info & FAQ Configuration
              </h1>
              <p className="text-lg text-gray-600 max-w-3xl">
                Configure your business information and create FAQ items for automatic
                customer responses. The bot will use this information to provide accurate
                answers to common questions.
              </p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm">
              <Info size={16} />
              <span>Story 1.11</span>
            </div>
          </div>
        </div>

        {/* Error Display (page-level) */}
        {error && (
          <div
            role="alert"
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
          >
            <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button
              type="button"
              onClick={clearError}
              className="text-red-600 hover:text-red-800"
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Business Info Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Business Information</h2>
                {hasConfig && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-md">
                    <CheckCircle2 size={12} />
                    Configured
                  </span>
                )}
              </div>

              <div className="space-y-6">
                <BusinessInfoForm disabled={isLoading} />

                {/* Save Button */}
                <div className="pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={handleSaveBusinessInfo}
                    disabled={isLoading || !isDirty}
                    className="w-full px-4 py-2.5 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Saving...
                      </span>
                    ) : (
                      'Save Business Info'
                    )}
                  </button>
                  {!isDirty && hasConfig && (
                    <p className="text-xs text-center text-gray-500 mt-2">
                      All changes saved
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* FAQ List */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <FaqList />
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-xl">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            How Business Info & FAQ Work
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-sm text-blue-800">
            <div>
              <h4 className="font-medium mb-2">Business Information</h4>
              <p className="text-blue-700">
                Your business name, description, and hours are automatically included in bot
                responses. When customers ask about your business, the bot uses this information
                to provide accurate answers.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-2">FAQ Matching</h4>
              <p className="text-blue-700">
                FAQ items are matched using keyword analysis. When a customer question matches
                an FAQ keyword or question text, the bot responds instantly with your predefined
                answer. This saves time and ensures consistency.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BusinessInfoFaqConfig;
