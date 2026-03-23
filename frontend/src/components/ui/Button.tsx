/** Button component with variants.

Supports disabled state for guard logic.
*/

import * as React from "react";

export interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "data-testid"> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
  dataTestId?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", size = "default", disabled, children, dataTestId, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 disabled:pointer-events-none disabled:opacity-50";

    const variantStyles = {
      default: "bg-emerald-600 text-white hover:bg-emerald-700",
      destructive: "bg-red-600 text-white hover:bg-red-700",
      outline: "border border-white/20 bg-white/[0.05] hover:bg-white/[0.10] text-white/80",
      secondary: "bg-white/10 text-white/80 hover:bg-white/15",
      ghost: "hover:bg-white/10 text-white/70",
    };

    const sizeStyles = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10",
    };

    return (
      <button
        ref={ref}
        data-testid={dataTestId}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

export { Button };
