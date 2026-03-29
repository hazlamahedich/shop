/**
 * FaqForm Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * A modal form for creating and editing FAQ items with:
 * - Question input (max 200 characters with character count)
 * - Answer textarea (max 1000 characters with character count)
 * - Keywords input (optional, comma-separated)
 * - Save and Cancel buttons
 * - Validation and help text
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { HelpCircle, MessageSquare, Tag, X } from 'lucide-react';
import type { FaqItem, FaqCreateRequest, FaqUpdateRequest } from '../../stores/businessInfoStore';

export interface FaqFormProps {
  /** FAQ item to edit (null for create mode) */
  faq: FaqItem | null;
  /** Whether the form modal is open */
  isOpen: boolean;
  /** Callback when form is submitted */
  onSave: (faq: FaqCreateRequest | FaqUpdateRequest) => Promise<void>;
  /** Callback when form is cancelled */
  onCancel: () => void;
  /** Whether the form is disabled (during save operations) */
  disabled?: boolean;
  /** Initial question to pre-populate (for create mode) */
  initialQuestion?: string;
}

/**
 * Default empty form state
 */
const emptyForm = {
  question: '',
  answer: '',
  keywords: '',
};

/**
 * FaqForm Component
 *
 * A modal dialog form for creating/editing FAQ items with:
 * - Question input (max 200 chars) with character count
 * - Answer textarea (max 1000 chars) with character count
 * - Keywords input (optional, comma-separated)
 * - Save and Cancel buttons
 * - Form validation
 */
export const FaqForm: React.FC<FaqFormProps> = ({
  faq,
  isOpen,
  onSave,
  onCancel,
  disabled = false,
  initialQuestion = '',
}) => {
  // Form state
  const [formData, setFormData] = React.useState(emptyForm);
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const prevInitialQuestion = React.useRef(initialQuestion);

  // Initialize form data when FAQ changes or modal opens
  React.useEffect(() => {
    if (isOpen) {
      if (faq) {
        setFormData({
          question: faq.question,
          answer: faq.answer,
          keywords: faq.keywords || '',
        });
      } else {
        // Use initialQuestion if provided (and changed from previous)
        const question = initialQuestion && initialQuestion !== prevInitialQuestion.current
          ? initialQuestion
          : emptyForm.question;
        setFormData({
          ...emptyForm,
          question,
        });
        if (initialQuestion && initialQuestion !== prevInitialQuestion.current) {
          prevInitialQuestion.current = initialQuestion;
        }
      }
      setErrors({});
    }
  }, [faq, isOpen, initialQuestion]);

  // Handle input changes
  const handleChange = (field: keyof typeof formData, value: string, maxLength?: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: maxLength ? value.slice(0, maxLength) : value,
    }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.question.trim()) {
      newErrors.question = 'Question is required';
    } else if (formData.question.trim().length > 200) {
      newErrors.question = 'Question must be 200 characters or less';
    }

    if (!formData.answer.trim()) {
      newErrors.answer = 'Answer is required';
    } else if (formData.answer.trim().length > 1000) {
      newErrors.answer = 'Answer must be 1000 characters or less';
    }

    if (formData.keywords.length > 500) {
      newErrors.keywords = 'Keywords must be 500 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const updateData: FaqCreateRequest | FaqUpdateRequest = {
      question: formData.question.trim(),
      answer: formData.answer.trim(),
      keywords: formData.keywords.trim() || null,
    };

    // Only include order_index for create, not for update
    if (!faq) {
      (updateData as FaqCreateRequest).order_index = undefined; // Let server assign
    }

    await onSave(updateData);
  };

  // Character count colors
  const getQuestionCountColor = () => {
    const length = formData.question.length;
    if (length > 180) return 'text-[#ffb4ab]';
    if (length > 150) return 'text-[#f9a826]';
    return 'text-[#b9cac4]';
  };

  const getAnswerCountColor = () => {
    const length = formData.answer.length;
    if (length > 900) return 'text-[#ffb4ab]';
    if (length > 750) return 'text-[#f9a826]';
    return 'text-[#b9cac4]';
  };

  // Close modal on escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !disabled) {
        onCancel();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, disabled, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="faq-form-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#001219]/80 backdrop-blur-sm"
        onClick={disabled ? undefined : onCancel}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative bg-[#1f1f25] border border-[#3a4a46]/30 shadow-[0_0_40px_rgba(0,0,0,0.5)] rounded-xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#3a4a46]/30 bg-[#1b1b20]/50">
          <h2 id="faq-form-title" className="text-xl font-bold text-[#e4e1e9] font-['Space_Grotesk']">
            {faq ? 'Edit FAQ Item' : 'Add FAQ Item'}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            disabled={disabled}
            className="p-2 text-[#b9cac4] hover:text-[#00f5d4] hover:bg-[#00f5d4]/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Close dialog"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Question Field */}
            <div className="space-y-2">
              <label
                htmlFor="faq-question"
                className="flex items-center gap-2 text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] ml-1"
              >
                <HelpCircle size={14} className="text-[#00dfc1]" />
                Question <span className="text-[#ffb4ab]">*</span>
              </label>
              <input
                id="faq-question"
                type="text"
                value={formData.question}
                onChange={(e) => handleChange('question', e.target.value, 200)}
                disabled={disabled}
                maxLength={200}
                placeholder="e.g., What are your shipping options?"
                className={`w-full bg-[#1b1b20] py-3 px-4 text-sm text-[#e4e1e9] border border-[#3a4a46]/40 rounded-lg focus:ring-1 focus:ring-[#00f5d4] focus:border-[#00f5d4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed placeholder-[#b9cac4]/30 ${
                  errors.question
                    ? 'border-[#ffb4ab]/50 focus:ring-[#ffb4ab] focus:border-[#ffb4ab]'
                    : ''
                }`}
                aria-describedby="faq-question-description faq-question-count"
                aria-invalid={!!errors.question}
                aria-required="true"
              />
              <p id="faq-question-description" className="text-[10px] text-[#b9cac4]/60 font-medium px-1">
                The question customers might ask about your business.
              </p>
              <div className="flex justify-between items-center px-1">
                {errors.question && (
                  <p className="text-[10px] text-[#ffb4ab]" role="alert">
                    {errors.question}
                  </p>
                )}
                <p
                  id="faq-question-count"
                  className={`text-[10px] font-mono font-bold ml-auto ${getQuestionCountColor()}`}
                >
                  {formData.question.length} / 200
                </p>
              </div>
            </div>

            {/* Answer Field */}
            <div className="space-y-2">
              <label
                htmlFor="faq-answer"
                className="flex items-center gap-2 text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] ml-1"
              >
                <MessageSquare size={14} className="text-[#00dfc1]" />
                Answer <span className="text-[#ffb4ab]">*</span>
              </label>
              <textarea
                id="faq-answer"
                value={formData.answer}
                onChange={(e) => handleChange('answer', e.target.value, 1000)}
                disabled={disabled}
                maxLength={1000}
                rows={5}
                placeholder="e.g., We offer free shipping on orders over $50. Standard shipping takes 3-5 business days."
                className={`w-full bg-[#1b1b20] py-3 px-4 text-sm text-[#e4e1e9] border border-[#3a4a46]/40 rounded-lg focus:ring-1 focus:ring-[#00f5d4] focus:border-[#00f5d4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed resize-none placeholder-[#b9cac4]/30 ${
                  errors.answer
                    ? 'border-[#ffb4ab]/50 focus:ring-[#ffb4ab] focus:border-[#ffb4ab]'
                    : ''
                }`}
                aria-describedby="faq-answer-description faq-answer-count"
                aria-invalid={!!errors.answer}
                aria-required="true"
              />
              <p id="faq-answer-description" className="text-[10px] text-[#b9cac4]/60 font-medium px-1">
                The answer the bot will provide when this question is matched.
              </p>
              <div className="flex justify-between items-center px-1">
                {errors.answer && (
                  <p className="text-[10px] text-[#ffb4ab]" role="alert">
                    {errors.answer}
                  </p>
                )}
                <p
                  id="faq-answer-count"
                  className={`text-[10px] font-mono font-bold ml-auto ${getAnswerCountColor()}`}
                >
                  {formData.answer.length} / 1000
                </p>
              </div>
            </div>

            {/* Keywords Field */}
            <div className="space-y-2">
              <label
                htmlFor="faq-keywords"
                className="flex items-center gap-2 text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] ml-1"
              >
                <Tag size={14} className="text-[#00dfc1]" />
                Keywords <span className="text-[#b9cac4]/50 normal-case tracking-normal">(optional)</span>
              </label>
              <input
                id="faq-keywords"
                type="text"
                value={formData.keywords}
                onChange={(e) => handleChange('keywords', e.target.value, 500)}
                disabled={disabled}
                maxLength={500}
                placeholder="e.g., shipping, delivery, returns"
                className={`w-full bg-[#1b1b20] py-3 px-4 text-sm text-[#e4e1e9] border border-[#3a4a46]/40 rounded-lg focus:ring-1 focus:ring-[#00f5d4] focus:border-[#00f5d4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed placeholder-[#b9cac4]/30 ${
                  errors.keywords
                    ? 'border-[#ffb4ab]/50 focus:ring-[#ffb4ab] focus:border-[#ffb4ab]'
                    : ''
                }`}
                aria-describedby="faq-keywords-description faq-keywords-count"
                aria-invalid={!!errors.keywords}
              />
              <p id="faq-keywords-description" className="text-[10px] text-[#b9cac4]/60 font-medium px-1">
                Comma-separated keywords that help the bot match customer questions to this FAQ.
              </p>
              <div className="flex justify-between items-center px-1">
                {errors.keywords && (
                  <p className="text-[10px] text-[#ffb4ab]" role="alert">
                    {errors.keywords}
                  </p>
                )}
                <p id="faq-keywords-count" className="text-[10px] font-mono font-bold text-[#b9cac4]/50 ml-auto">
                  {formData.keywords.length} / 500
                </p>
              </div>
            </div>

            {/* Help Note */}
            <div className="p-4 bg-[#00bbf9]/5 border border-[#00bbf9]/20 rounded-lg backdrop-blur-sm mt-6">
              <p className="text-xs text-[#82d3ff] tracking-wide leading-relaxed">
                <strong className="text-[#00bbf9]">Tip:</strong> Keywords help the bot match customer questions even when they
                don&apos;t use the exact wording of your FAQ question.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-[#3a4a46]/30 bg-[#1b1b20]/50">
            <button
              type="button"
              onClick={onCancel}
              disabled={disabled}
              className="px-5 py-2.5 text-sm font-bold text-[#b9cac4] bg-[#1b1b20] border border-[#3a4a46]/40 rounded-lg hover:text-[#e4e1e9] hover:bg-[#3a4a46]/20 hover:border-[#3a4a46] focus:ring-2 focus:ring-[#b9cac4] focus:ring-offset-2 focus:ring-offset-[#1b1b20] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={disabled}
              className="px-5 py-2.5 text-sm font-bold text-[#00f5d4] bg-[#00f5d4]/10 border border-[#00f5d4]/30 rounded-lg hover:bg-[#00f5d4]/20 hover:shadow-[0_0_15px_rgba(0,245,212,0.15)] focus:ring-2 focus:ring-[#00f5d4] focus:ring-offset-2 focus:ring-offset-[#1b1b20] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {disabled ? (
                <span className="flex items-center gap-2">
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
                'Save FAQ'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
