/** Checkbox component with label support.

WCAG AA compliant: implicit label via component structure.
*/

import * as React from "react";

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  label?: string;
  description?: string;
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className = "", label, description, id, checked, onChange, ...props }, ref) => {
    const checkboxId = id || `checkbox-${React.useId()}`;

    return (
      <div className="flex items-start space-x-3">
        <input
          ref={ref}
          type="checkbox"
          id={checkboxId}
          checked={checked}
          onChange={onChange}
          className={`
            mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-2
            focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed
            disabled:opacity-50
            ${className}
          `}
          {...props}
        />
        {label && (
          <div className="flex-1">
            <label htmlFor={checkboxId} className="text-sm font-medium text-slate-700 cursor-pointer">
              {label}
            </label>
            {description && (
              <p className="text-xs text-slate-500 mt-0.5">{description}</p>
            )}
          </div>
        )}
      </div>
    );
  },
);
Checkbox.displayName = "Checkbox";

export { Checkbox };
