/** Badge Component.
 *
 * Small status indicator badge.
 */

import * as React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
}

export const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
          variant === "default" && "border-transparent bg-slate-900 text-slate-50",
          variant === "success" && "border-transparent bg-green-500 text-white",
          variant === "warning" && "border-transparent bg-yellow-500 text-white",
          variant === "destructive" && "border-transparent bg-red-500 text-white",
          variant === "outline" && "text-slate-950",
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = "Badge";
