/** Alert Component.
 *
 * Alert banner component for messages and notifications.
 */

import * as React from "react";
import { cn } from "../../lib/utils";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive";
  title?: string;
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = "default", title, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        role={variant === "destructive" ? "alert" : "status"}
        className={cn(
          "relative w-full rounded-lg border p-4",
          variant === "default" &&
            "bg-blue-50 border-blue-200 text-blue-800",
          variant === "destructive" &&
            "bg-red-50 border-red-200 text-red-800",
          className
        )}
        {...props}
      >
        {title && (
          <h5 className="mb-1 font-medium leading-none tracking-tight">
            {title}
          </h5>
        )}
        <div className="text-sm">{children}</div>
      </div>
    );
  }
);

Alert.displayName = "Alert";
