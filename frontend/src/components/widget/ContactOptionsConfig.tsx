import React, { useState } from 'react';
import type { ContactOption } from '../../widget/types/widget';

export interface ContactOptionsConfigProps {
  value: ContactOption[];
  onChange: (options: ContactOption[]) => void;
  disabled?: boolean;
}

const PHONE_REGEX = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateOption(option: ContactOption): string | null {
  if (!option.label.trim()) {
    return 'Label is required';
  }
  
  if (!option.value.trim()) {
    return 'Value is required';
  }
  
  if (option.type === 'phone' && !PHONE_REGEX.test(option.value.replace(/\s/g, ''))) {
    return 'Invalid phone number format';
  }
  
  if (option.type === 'email' && !EMAIL_REGEX.test(option.value)) {
    return 'Invalid email format';
  }
  
  if (option.type === 'custom') {
    try {
      new URL(option.value);
    } catch {
      return 'Invalid URL format';
    }
  }
  
  return null;
}

export function ContactOptionsConfig({ value, onChange, disabled }: ContactOptionsConfigProps) {
  const [errors, setErrors] = useState<Record<number, string>>({});
  
  const addOption = (type: ContactOption['type']) => {
    const newOption: ContactOption = {
      type,
      label: type === 'phone' ? 'Call Support' : type === 'email' ? 'Email Support' : 'Custom Link',
      value: '',
      icon: type === 'phone' ? '📞' : type === 'email' ? '✉️' : '🔗',
    };
    onChange([...value, newOption]);
  };
  
  const removeOption = (index: number) => {
    const newOptions = value.filter((_, i) => i !== index);
    onChange(newOptions);
    const newErrors = { ...errors };
    delete newErrors[index];
    setErrors(newErrors);
  };
  
  const updateOption = (index: number, field: keyof ContactOption, newValue: string) => {
    const newOptions = [...value];
    newOptions[index] = { ...newOptions[index], [field]: newValue };
    onChange(newOptions);
    
    const error = validateOption(newOptions[index]);
    if (error) {
      setErrors({ ...errors, [index]: error });
    } else {
      const newErrors = { ...errors };
      delete newErrors[index];
      setErrors(newErrors);
    }
  };
  
  const hasPhone = value.some(o => o.type === 'phone');
  const hasEmail = value.some(o => o.type === 'email');
  
  return (
    <div className="contact-options-config" data-testid="contact-options-config">
      <div className="contact-options-header">
        <h4>Contact Options</h4>
        <p className="text-sm text-gray-500">
          Add contact options for shoppers who need human support. At least one option is required.
        </p>
      </div>
      
      <div className="contact-options-list">
        {value.map((option, index) => (
          <div key={index} className="contact-option-item" data-testid={`contact-option-${index}`}>
            <div className="contact-option-type">
              <span className="contact-option-icon">{option.icon}</span>
              <span className="contact-option-type-label">
                {option.type === 'phone' ? 'Phone' : option.type === 'email' ? 'Email' : 'Custom'}
              </span>
            </div>
            
            <div className="contact-option-fields">
              <input
                type="text"
                placeholder="Label"
                value={option.label}
                onChange={(e) => updateOption(index, 'label', e.target.value)}
                disabled={disabled}
                className="contact-option-input"
                data-testid={`contact-label-${index}`}
              />
              
              <input
                type={option.type === 'email' ? 'email' : option.type === 'phone' ? 'tel' : 'url'}
                placeholder={
                  option.type === 'phone' ? '+1-555-123-4567' :
                  option.type === 'email' ? 'support@example.com' :
                  'https://example.com'
                }
                value={option.value}
                onChange={(e) => updateOption(index, 'value', e.target.value)}
                disabled={disabled}
                className="contact-option-input"
                data-testid={`contact-value-${index}`}
              />
              
              {errors[index] && (
                <span className="contact-option-error" data-testid={`contact-error-${index}`}>
                  {errors[index]}
                </span>
              )}
            </div>
            
            <button
              type="button"
              onClick={() => removeOption(index)}
              disabled={disabled}
              className="contact-option-remove"
              data-testid={`contact-remove-${index}`}
              aria-label={`Remove ${option.type} option`}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      
      <div className="contact-options-actions">
        {!hasPhone && (
          <button
            type="button"
            onClick={() => addOption('phone')}
            disabled={disabled}
            className="contact-option-add"
            data-testid="add-phone-option"
          >
            + Add Phone
          </button>
        )}
        
        {!hasEmail && (
          <button
            type="button"
            onClick={() => addOption('email')}
            disabled={disabled}
            className="contact-option-add"
            data-testid="add-email-option"
          >
            + Add Email
          </button>
        )}
        
        <button
          type="button"
          onClick={() => addOption('custom')}
          disabled={disabled}
          className="contact-option-add"
          data-testid="add-custom-option"
        >
          + Add Custom Link
        </button>
      </div>
      
      {value.length === 0 && (
        <p className="contact-options-warning" data-testid="no-contact-options-warning">
          ⚠️ At least one contact option is required for the contact card to appear.
        </p>
      )}
    </div>
  );
}
