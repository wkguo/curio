import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-extrabold [&_svg]:size-3.5", {
  variants: {
    variant: {
      default: "bg-curio-100 text-curio-700",
      mint: "bg-mint-100 text-mint-700",
      sun: "bg-sun-100 text-sun-700",
      coral: "bg-coral-100 text-coral-700",
      sky: "bg-sky-100 text-sky-700",
      ink: "bg-ink-100 text-ink-600",
      outline: "border border-ink-200 bg-white text-ink-600",
    },
  },
  defaultVariants: { variant: "default" },
});

export function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
