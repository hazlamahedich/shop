/** Collapsible component for expandable help sections.

Features aria-expanded for WCAG AA compliance.
*/

import * as React from "react";

export interface CollapsibleProps {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export interface CollapsibleTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  "aria-expanded": boolean;
  "aria-controls"?: string;
}

const CollapsibleContext = React.createContext<{
  open: boolean;
  setOpen: (open: boolean) => void;
  id: string;
}>({
  open: false,
  setOpen: () => {},
  id: "",
});

export const Collapsible = React.forwardRef<HTMLDivElement, CollapsibleProps>(
  ({ children, open: controlledOpen, onOpenChange }, ref) => {
    const [internalOpen, setInternalOpen] = React.useState(false);
    const id = React.useId();

    const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
    const setOpen = React.useCallback(
      (newOpen: boolean) => {
        if (controlledOpen === undefined) {
          setInternalOpen(newOpen);
        }
        onOpenChange?.(newOpen);
      },
      [controlledOpen, onOpenChange],
    );

    return (
      <CollapsibleContext.Provider value={{ open, setOpen, id }}>
        <div ref={ref}>{children}</div>
      </CollapsibleContext.Provider>
    );
  },
);
Collapsible.displayName = "Collapsible";

export const CollapsibleTrigger = React.forwardRef<HTMLButtonElement, CollapsibleTriggerProps>(
  ({ className = "", children, ...props }, ref) => {
    const context = React.useContext(CollapsibleContext);

    return (
      <button
        ref={ref}
        type="button"
        className={`
          inline-flex items-center justify-center text-sm font-medium
          text-blue-600 hover:text-blue-700 focus:outline-none
          focus:ring-2 focus:ring-blue-500 rounded
          ${className}
        `}
        aria-expanded={context.open}
        aria-controls={`${context.id}-content`}
        onClick={() => context.setOpen(!context.open)}
        {...props}
      >
        {children}
        <svg
          className={`ml-1 h-4 w-4 transition-transform ${context.open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    );
  },
);
CollapsibleTrigger.displayName = "CollapsibleTrigger";

export const CollapsibleContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = "", children, ...props }, ref) => {
    const context = React.useContext(CollapsibleContext);

    if (!context.open) {
      return null;
    }

    return (
      <div
        ref={ref}
        id={`${context.id}-content`}
        className={`
          overflow-hidden transition-all duration-200 ease-in-out
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  },
);
CollapsibleContent.displayName = "CollapsibleContent";

export { CollapsibleContext };
