/**
 * BusinessInfoForm Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Redesigned for "Mantis HUD".
 */

import * as React from 'react';
import { Building2, FileText } from 'lucide-react';
import { useBusinessInfoStore } from '../../stores/businessInfoStore';
import { ContactOptionsConfig } from '../widget/ContactOptionsConfig';

export interface BusinessInfoFormProps {
  /** Optional CSS class name */
  className?: string;
  /** Whether the form is disabled (during save operations) */
  disabled?: boolean;
}

/**
 * BusinessInfoForm Component
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
    const value = e.target.value.slice(0, 100);
    setBusinessName(value);
  };

  // Handle business description change
  const handleBusinessDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value.slice(0, 500);
    setBusinessDescription(value);
  };

  // Character count color based on remaining characters
  const getCharacterCountColor = () => {
    const remaining = 500 - descriptionLength;
    if (remaining < 50) return 'text-[#ffb4ab]';
    if (remaining < 100) return 'text-[#f9a826]';
    return 'text-[#00dfc1]';
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
          className="p-4 bg-[#ffb4ab]/5 border border-[#ffb4ab]/20 rounded-lg flex items-start gap-3 backdrop-blur-md"
        >
          <svg
            className="w-5 h-5 text-[#ffb4ab] flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-sm text-[#ffb4ab]">{error}</p>
        </div>
      )}

      {/* Business Name Field */}
      <div className="space-y-2">
        <label
          htmlFor="business-name"
          className="flex items-center gap-2 text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] ml-1"
        >
          <Building2 size={14} className="text-[#00dfc1]" />
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
          className="w-full bg-[#1b1b20]/60 border-0 border-b-2 border-[#3a4a46] focus:border-[#00f5d4] focus:ring-0 text-sm py-3 px-4 text-[#e4e1e9] transition-all outline-none rounded-t-lg disabled:opacity-50 disabled:cursor-not-allowed placeholder-[#b9cac4]/30"
        />
        <div className="flex justify-between items-center px-1">
          <p className="text-[10px] text-[#b9cac4]/60 font-medium">
            The name appearing in bot responses.
          </p>
          <p className="text-[10px] font-mono text-[#b9cac4]/50">
            {(businessName?.length || 0)} / 100
          </p>
        </div>
      </div>

      {/* Business Description Field */}
      <div className="space-y-2">
        <label
          htmlFor="business-description"
          className="flex items-center gap-2 text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] ml-1"
        >
          <FileText size={14} className="text-[#00dfc1]" />
          Business Description
        </label>
        <textarea
          id="business-description"
          value={businessDescription || ''}
          onChange={handleBusinessDescriptionChange}
          disabled={disabled}
          maxLength={500}
          rows={4}
          placeholder="Describe what your business sells..."
          className="w-full bg-[#1b1b20]/60 border-0 border-b-2 border-[#3a4a46] focus:border-[#00f5d4] focus:ring-0 text-sm py-3 px-4 text-[#e4e1e9] transition-all outline-none resize-none rounded-t-lg disabled:opacity-50 disabled:cursor-not-allowed placeholder-[#b9cac4]/30"
        />
        <div className="flex justify-between items-start px-1">
          <p className="text-[10px] text-[#b9cac4]/60 leading-relaxed font-medium max-w-[70%]">
            Helps the bot explain what your business sells.
          </p>
          <p className={`text-[10px] font-mono font-bold ${getCharacterCountColor()}`}>
            {descriptionLength} / 500
          </p>
        </div>
      </div>

      {/* Story 10-5: Contact Options Configuration */}
      <div className="pt-6 border-t border-[#3a4a46]/30">
        <ContactOptionsConfig />
      </div>

      {/* Tip Note */}
      <div className="p-4 bg-[#00bbf9]/5 border border-[#00bbf9]/20 rounded-lg backdrop-blur-sm mt-4">
        <p className="text-xs text-[#82d3ff] tracking-wide leading-relaxed text-center">
          <strong className="text-[#00bbf9]">Tip:</strong> This business information helps the bot providing personalization.
        </p>
      </div>
    </form>
  );
});

BusinessInfoForm.displayName = 'BusinessInfoForm';
