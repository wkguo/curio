import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full resize-none rounded-2xl border-2 border-ink-200 bg-white px-4 py-3 text-[16px] font-semibold text-ink-900 placeholder:font-semibold placeholder:text-ink-300 transition focus:border-curio-400 focus:outline-none focus:ring-4 focus:ring-curio-100 disabled:bg-ink-50",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
