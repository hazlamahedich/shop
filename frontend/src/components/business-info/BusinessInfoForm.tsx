/**
 * BusinessInfoForm Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Displays a form for entering and editing business information including:
 * - Business Name (max 100 characters)
 * - Business Description (max 500 characters with character count)
 *
 * Note: Business Hours moved to BusinessHoursConfig component (Story 3.10)
 *
 * Provides form validation, character counts, and help text.
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { Building2, FileText } from 'lucide-react';
import { useBusinessInfoStore } from '../../stores/businessInfoStore';

export interface BusinessInfoFormProps {
  /** Optional CSS class name */
  className?: string;
  /** Whether the form is disabled (during save operations) */
  disabled?: boolean;
}

/**
 * BusinessInfoForm Component
 *
 * A form component for managing business information with:
 * - Text input for business name (max 100 chars)
 * - Textarea for business description (max 500 chars with character count)
 * - Validation and error display
 * - Loading states
 */
export const BusinessInfoForm = React.forwardRef<
  HTMLFormElement,
  BusinessInfoFormProps
>(({ className = '', disabled = false }, ref) => {
  const {
    businessName,
    businessDescription,
    setBusinessName,
    setBusinessDescription,
    error,
  } = useBusinessInfoStore();

  // Local state for character counts
  const [descriptionLength, setDescriptionLength] = React.useState(0);

  // Update description length when description changes
  React.useEffect(() => {
    setDescriptionLength(businessDescription?.length || 0);
  }, [businessDescription]);

  // Handle business name change
  const handleBusinessNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.slice(0, 100); // Enforce max length
    setBusinessName(value);
  };

  // Handle business description change
  const handleBusinessDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value.slice(0, 500); // Enforce max length
    setBusinessDescription(value);
  };

  // Character count color based on remaining characters
  const getCharacterCountColor = () => {
    const remaining = 500 - descriptionLength;
    if (remaining < 50) return 'text-red-600';
    if (remaining < 100) return 'text-amber-600';
    return 'text-gray-500';
  };

  return (
    <form
      ref={ref}
      className={`space-y-6 ${className}`}
      aria-label="Business information form"
    >
      {/* Error Display */}
      {error && (
        <div
          role="alert"
          className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
        >
          <svg
            className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Business Name Field */}
      <div className="space-y-2">
        <label
          htmlFor="business-name"
          className="flex items-center gap-2 text-sm font-medium text-gray-700"
        >
          <Building2 size={16} className="text-gray-500" />
          Business Name
        </label>
        <input
          id="business-name"
          type="text"
          value={businessName || ''}
          onChange={handleBusinessNameChange}
          disabled={disabled}
          maxLength={100}
          placeholder="e.g., Alex's Athletic Gear"
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
          aria-describedby="business-name-description"
        />
        <p id="business-name-description" className="text-xs text-gray-500">
          The name of your business as it should appear in bot responses.
        </p>
        <p className="text-xs text-gray-400 text-right">
          {(businessName?.length || 0)} / 100
        </p>
      </div>

      {/* Business Description Field */}
      <div className="space-y-2">
        <label
          htmlFor="business-description"
          className="flex items-center gap-2 text-sm font-medium text-gray-700"
        >
          <FileText size={16} className="text-gray-500" />
          Business Description
        </label>
        <textarea
          id="business-description"
          value={businessDescription || ''}
          onChange={handleBusinessDescriptionChange}
          disabled={disabled}
          maxLength={500}
          rows={4}
          placeholder="Describe what your business sells and what makes it unique..."
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          aria-describedby="business-description-description business-description-count"
        />
        <p id="business-description-description" className="text-xs text-gray-500">
          A brief description that helps the bot explain what your business sells.
        </p>
        <div className="flex justify-between items-center">
          <p className="text-xs text-gray-400">
            This description is used when customers ask "What do you sell?"
          </p>
          <p
            id="business-description-count"
            className={`text-xs font-medium ${getCharacterCountColor()}`}
          >
            {descriptionLength} / 500
          </p>
        </div>
      </div>

      {/* Help Note */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> This business information helps the bot provide more accurate
          and personalized responses to customer questions.
        </p>
      </div>
    </form>
  );
});

BusinessInfoForm.displayName = 'BusinessInfoForm';
